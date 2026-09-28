#!/usr/bin/env python3
"""
Optimized Graph Queries for Scalable Visualization

SPARQL access layer over the AllegroGraph FEEKG repository:
- Pagination for incremental loading
- Time-window filtering for focused views
- Degree-based filtering for showing key nodes first
- TTL caching for repeated aggregate queries

All user-supplied values are validated through ``feekg_core.query.sparql``
before being placed in a query. Transport or server failures raise
:class:`GraphQueryError` instead of silently returning empty results.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from shared.config.settings import Settings, get_settings
from feekg_core.query import sparql
from feekg_core.query.sparql import PREFIXES, local_id_from_uri

logger = logging.getLogger(__name__)

ORDERABLE_EVENT_FIELDS = ('date', 'type', 'severity', 'label')


class GraphQueryError(RuntimeError):
    """The graph database could not be reached or rejected the query."""


def _value(binding: Dict, key: str, default=None):
    return binding.get(key, {}).get('value', default)


def _float(binding: Dict, key: str, default: float = 0.0) -> float:
    raw = _value(binding, key)
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        return default


def _link_from_binding(binding: Dict) -> Dict:
    return {
        'from': local_id_from_uri(binding['from']['value']),
        'to': local_id_from_uri(binding['to']['value']),
        'score': float(binding['score']['value']),
        'type': 'enhanced',
        'temporal': _float(binding, 'temporal'),
        'entity_overlap': _float(binding, 'entityOverlap'),
        'semantic': _float(binding, 'semantic'),
        'topic': _float(binding, 'topic'),
        'causality': _float(binding, 'causality'),
        'emotional': _float(binding, 'emotional'),
    }


_LINK_COMPONENTS = """
    OPTIONAL { ?link feekg:temporalScore ?temporal . }
    OPTIONAL { ?link feekg:entity_overlapScore ?entityOverlap . }
    OPTIONAL { ?link feekg:semanticScore ?semantic . }
    OPTIONAL { ?link feekg:topicScore ?topic . }
    OPTIONAL { ?link feekg:causalityScore ?causality . }
    OPTIONAL { ?link feekg:emotionalScore ?emotional . }
"""


class OptimizedGraphBackend:
    """
    SPARQL-over-HTTP backend for graph visualization and API queries.

    Instances are thread-safe and intended to be long-lived (one per process)
    so the HTTP connection pool and caches are reused across requests.
    """

    def __init__(self, settings: Optional[Settings] = None, session: Optional[requests.Session] = None):
        self.settings = settings or get_settings()
        self.repo_url = self.settings.ag_repo_url
        self.auth = self.settings.ag_auth
        self.timeout = self.settings.ag_timeout
        self.cache_ttl = self.settings.cache_ttl

        self.session = session or self._build_session(self.settings.ag_retries)
        self._cache: Dict[str, tuple] = {}
        self._cache_lock = threading.Lock()

    @staticmethod
    def _build_session(retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset({'GET', 'POST'}),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=16)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _query_sparql(self, query: str, timeout: Optional[float] = None) -> Dict:
        """Execute a SPARQL query and return the JSON result document."""
        try:
            response = self.session.post(
                self.repo_url,
                data={'query': query},
                headers={'Accept': 'application/sparql-results+json'},
                auth=self.auth,
                timeout=timeout or self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            logger.error("SPARQL query failed (status=%s): %s", status, exc.__class__.__name__)
            raise GraphQueryError("Graph database query failed") from exc
        except ValueError as exc:
            logger.error("SPARQL response was not valid JSON")
            raise GraphQueryError("Graph database returned an invalid response") from exc

    def _bindings(self, query: str) -> List[Dict]:
        return self._query_sparql(query).get('results', {}).get('bindings', [])

    def _count(self, where: str, var: str = '?s', distinct: bool = False) -> int:
        d = 'DISTINCT ' if distinct else ''
        rows = self._bindings(f"{PREFIXES}SELECT (COUNT({d}{var}) AS ?count) WHERE {{ {where} }}")
        return int(rows[0]['count']['value']) if rows else 0

    def _cached(self, key: str, compute: Callable[[], Any]) -> Any:
        now = time.time()
        with self._cache_lock:
            hit = self._cache.get(key)
            if hit and now - hit[1] < self.cache_ttl:
                return hit[0]
        value = compute()
        with self._cache_lock:
            self._cache[key] = (value, now)
        return value

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def ping(self) -> bool:
        """Cheap connectivity check used by readiness probes."""
        self._query_sparql("ASK { ?s ?p ?o }", timeout=min(self.timeout, 5))
        return True

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_events_paginated(self, offset: int = 0, limit: int = 100, order_by: str = 'date') -> Dict:
        """Get a page of events ordered by ``order_by``."""
        offset = sparql.integer(offset, 'offset')
        limit = sparql.integer(limit, 'limit', minimum=1)
        order_by = sparql.choice(order_by, ORDERABLE_EVENT_FIELDS, 'order_by')

        query = f"""{PREFIXES}
SELECT ?event ?eventId ?type ?date ?label ?severity ?row ?confidence
WHERE {{
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
    ?event rdfs:label ?label .
    OPTIONAL {{ ?event feekg:severity ?severity . }}
    OPTIONAL {{ ?event feekg:csvRowNumber ?row . }}
    OPTIONAL {{ ?event feekg:classificationConfidence ?confidence . }}
    BIND(STRAFTER(STR(?event), "#") AS ?eventId)
}}
ORDER BY ?{order_by} ?event
LIMIT {limit}
OFFSET {offset}
"""
        events = [
            {
                'eventId': b['eventId']['value'],
                'type': b['type']['value'],
                'date': b['date']['value'],
                'label': b['label']['value'],
                'severity': _value(b, 'severity'),
                'csvRow': _value(b, 'row'),
                'confidence': _float(b, 'confidence'),
            }
            for b in self._bindings(query)
        ]
        total = self.get_total_event_count()
        return {
            'events': events,
            'total': total,
            'offset': offset,
            'limit': limit,
            'has_more': offset + limit < total,
        }

    def get_total_event_count(self) -> int:
        return self._cached('total_events', lambda: self._count('?s a feekg:Event .', distinct=True))

    def get_events_by_timewindow(
        self,
        start_date: str,
        end_date: str,
        entity_filter: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict]:
        """Events with ``start_date <= date <= end_date`` (inclusive, ISO dates)."""
        start = sparql.iso_date(start_date, 'start_date')
        end = sparql.iso_date(end_date, 'end_date')
        if start > end:
            raise sparql.InvalidQueryParameter("start_date must be on or before end_date")
        limit = sparql.integer(limit, 'limit', minimum=1)
        entity_clause = (
            f'?event feekg:involves {sparql.iri(entity_filter, "entity")} .' if entity_filter else ''
        )

        query = f"""{PREFIXES}
SELECT ?event ?eventId ?type ?date ?label ?severity ?actor
WHERE {{
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
    ?event rdfs:label ?label .
    OPTIONAL {{ ?event feekg:severity ?severity . }}
    OPTIONAL {{ ?event feekg:actor ?actor . }}
    FILTER(?date >= "{start}"^^xsd:date && ?date <= "{end}"^^xsd:date)
    {entity_clause}
    BIND(STRAFTER(STR(?event), "#") AS ?eventId)
}}
ORDER BY ?date ?event
LIMIT {limit}
"""
        return [
            {
                'eventId': b['eventId']['value'],
                'type': b['type']['value'],
                'date': b['date']['value'],
                'label': b['label']['value'],
                'severity': _value(b, 'severity'),
                'actor': _value(b, 'actor'),
            }
            for b in self._bindings(query)
        ]

    def get_high_impact_events(self, min_degree: int = 5, limit: int = 100) -> List[Dict]:
        """Events with the most evolution links (graph hubs)."""
        min_degree = sparql.integer(min_degree, 'min_degree')
        limit = sparql.integer(limit, 'limit', minimum=1)
        query = f"""{PREFIXES}
SELECT ?event ?eventId ?label ?type ?date (COUNT(?other) AS ?degree)
WHERE {{
    ?event a feekg:Event .
    ?event rdfs:label ?label .
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
    {{ ?event feekg:evolvesTo ?other . }} UNION {{ ?other feekg:evolvesTo ?event . }}
    BIND(STRAFTER(STR(?event), "#") AS ?eventId)
}}
GROUP BY ?event ?eventId ?label ?type ?date
HAVING (COUNT(?other) >= {min_degree})
ORDER BY DESC(?degree)
LIMIT {limit}
"""
        return [
            {
                'eventId': b['eventId']['value'],
                'label': b['label']['value'],
                'type': b['type']['value'],
                'date': b['date']['value'],
                'degree': int(b['degree']['value']),
            }
            for b in self._bindings(query)
        ]

    def get_event_neighborhood(self, event_id: str, max_hops: int = 1, min_score: float = 0.3) -> Dict:
        """1-hop neighborhood of an event (for expand/collapse UI)."""
        if max_hops != 1:
            raise NotImplementedError("Multi-hop neighborhoods not yet implemented")
        center = sparql.iri(event_id, 'event_id')
        score = sparql.number(min_score, 'min_score')

        query = f"""{PREFIXES}
SELECT ?neighbor ?neighborId ?label ?score ?direction
WHERE {{
    {{
        ?linkNode feekg:from {center} .
        ?linkNode feekg:to ?neighbor .
        ?linkNode feekg:score ?score .
        BIND("out" AS ?direction)
    }} UNION {{
        ?linkNode feekg:from ?neighbor .
        ?linkNode feekg:to {center} .
        ?linkNode feekg:score ?score .
        BIND("in" AS ?direction)
    }}
    ?neighbor rdfs:label ?label .
    FILTER(?score >= {score})
    BIND(STRAFTER(STR(?neighbor), "#") AS ?neighborId)
}}
"""
        neighbors, links = [], []
        for b in self._bindings(query):
            neighbor_id = b['neighborId']['value']
            link_score = float(b['score']['value'])
            neighbors.append({'eventId': neighbor_id, 'label': b['label']['value']})
            if b['direction']['value'] == 'out':
                links.append({'from': event_id, 'to': neighbor_id, 'score': link_score})
            else:
                links.append({'from': neighbor_id, 'to': event_id, 'score': link_score})
        return {'center': event_id, 'neighbors': neighbors, 'links': links}

    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Single event by its local id (e.g. ``evt_123``), or ``None``."""
        event = sparql.iri(event_id, 'event_id')
        query = f"""{PREFIXES}
SELECT ?type ?date ?label ?severity ?description ?confidence ?actor
WHERE {{
    {event} a feekg:Event .
    {event} feekg:eventType ?type .
    {event} feekg:date ?date .
    {event} rdfs:label ?label .
    OPTIONAL {{ {event} feekg:severity ?severity . }}
    OPTIONAL {{ {event} feekg:description ?description . }}
    OPTIONAL {{ {event} feekg:classificationConfidence ?confidence . }}
    OPTIONAL {{ {event} feekg:actor ?actor . }}
}}
LIMIT 1
"""
        rows = self._bindings(query)
        if not rows:
            return None
        b = rows[0]
        return {
            'eventId': event_id,
            'type': b['type']['value'],
            'date': b['date']['value'],
            'label': b['label']['value'],
            'severity': _value(b, 'severity'),
            'description': _value(b, 'description'),
            'actor': _value(b, 'actor'),
            'confidence': _float(b, 'confidence'),
        }

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------

    def get_all_entities(self) -> List[Dict]:
        query = f"""{PREFIXES}
SELECT ?entity ?label ?type
WHERE {{
    ?entity a feekg:Entity .
    ?entity rdfs:label ?label .
    ?entity feekg:entityType ?type .
}}
ORDER BY ?label
"""
        return [
            {
                'id': local_id_from_uri(b['entity']['value']),
                'name': b['label']['value'],
                'type': b['type']['value'],
            }
            for b in self._bindings(query)
        ]

    def get_entity_by_id(self, entity_id: str) -> Optional[Dict]:
        """Single entity by its local id (as returned by ``get_all_entities``)."""
        entity = sparql.iri(entity_id, 'entity_id')
        query = f"""{PREFIXES}
SELECT ?name ?type ?description (COUNT(DISTINCT ?event) AS ?eventCount)
WHERE {{
    {entity} a feekg:Entity .
    {entity} rdfs:label ?name .
    {entity} feekg:entityType ?type .
    OPTIONAL {{ {entity} feekg:description ?description . }}
    OPTIONAL {{ ?event feekg:involves {entity} . }}
}}
GROUP BY ?name ?type ?description
LIMIT 1
"""
        rows = self._bindings(query)
        if not rows:
            return None
        b = rows[0]
        return {
            'id': entity_id,
            'name': b['name']['value'],
            'type': b['type']['value'],
            'description': _value(b, 'description'),
            'eventCount': int(_value(b, 'eventCount', 0)),
        }

    # ------------------------------------------------------------------
    # Evolution links
    # ------------------------------------------------------------------

    def get_evolution_links(
        self,
        limit: int = 500,
        min_score: float = 0.0,
        event_id: Optional[str] = None,
    ) -> List[Dict]:
        """Evolution links, strongest first. ``event_id`` restricts to links touching that event."""
        limit = sparql.integer(limit, 'limit', minimum=1)
        score = sparql.number(min_score, 'min_score')
        event_filter = ''
        if event_id:
            e = sparql.iri(event_id, 'event_id')
            event_filter = f'FILTER(?from = {e} || ?to = {e})'

        query = f"""{PREFIXES}
SELECT ?from ?to ?score ?temporal ?entityOverlap ?semantic ?topic ?causality ?emotional
WHERE {{
    ?link a feekg:EvolutionLink .
    ?link feekg:from ?from .
    ?link feekg:to ?to .
    ?link feekg:score ?score .
    {_LINK_COMPONENTS}
    FILTER(?score >= {score})
    {event_filter}
}}
ORDER BY DESC(?score)
LIMIT {limit}
"""
        return [_link_from_binding(b) for b in self._bindings(query)]

    def get_evolution_links_for_events(self, event_ids: List[str], min_score: float = 0.0) -> List[Dict]:
        """Links whose endpoints are both in ``event_ids``."""
        if not event_ids:
            return []
        uris = sparql.iri_list(event_ids, 'event_id')
        score = sparql.number(min_score, 'min_score')

        query = f"""{PREFIXES}
SELECT ?from ?to ?score ?temporal ?entityOverlap ?semantic ?topic ?causality ?emotional
WHERE {{
    ?link a feekg:EvolutionLink .
    ?link feekg:from ?from .
    ?link feekg:to ?to .
    ?link feekg:score ?score .
    {_LINK_COMPONENTS}
    FILTER(?from IN ({uris}))
    FILTER(?to IN ({uris}))
    FILTER(?score >= {score})
}}
ORDER BY DESC(?score)
"""
        return [_link_from_binding(b) for b in self._bindings(query)]

    def get_evolution_statistics(self) -> Dict:
        """Aggregate statistics over all evolution links (cached)."""

        def compute() -> Dict:
            query = f"""{PREFIXES}
SELECT (COUNT(?link) AS ?count) (AVG(?score) AS ?avg) (MIN(?score) AS ?min) (MAX(?score) AS ?max)
       (SUM(IF(?score >= 0.5, 1, 0)) AS ?strong)
WHERE {{
    ?link a feekg:EvolutionLink .
    ?link feekg:score ?score .
}}
"""
            rows = self._bindings(query)
            b = rows[0] if rows else {}
            return {
                'total_links': int(_value(b, 'count', 0)),
                'avg_score': round(_float(b, 'avg'), 4),
                'min_score': round(_float(b, 'min'), 4),
                'max_score': round(_float(b, 'max'), 4),
                'strong_links': int(float(_value(b, 'strong', 0))),
            }

        return self._cached('evolution_stats', compute)

    # ------------------------------------------------------------------
    # Relationships & composite views
    # ------------------------------------------------------------------

    def get_event_entity_relationships(self, event_ids: Optional[List[str]] = None) -> List[Dict]:
        event_filter = ''
        if event_ids is not None:
            if not event_ids:
                return []
            event_filter = f'FILTER(?event IN ({sparql.iri_list(event_ids, "event_id")}))'

        query = f"""{PREFIXES}
SELECT ?event ?entity
WHERE {{
    ?event a feekg:Event .
    ?event feekg:involves ?entity .
    {event_filter}
}}
"""
        return [
            {
                'event': local_id_from_uri(b['event']['value']),
                'entity': local_id_from_uri(b['entity']['value']),
                'type': 'involves',
            }
            for b in self._bindings(query)
        ]

    def get_graph_data_for_viz(
        self,
        limit_events: int = 500,
        min_evolution_score: float = 0.3,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Entities, events and the edges between them for a 2-layer graph view."""
        if start_date and end_date:
            events = self.get_events_by_timewindow(start_date, end_date, limit=limit_events)
        else:
            events = self.get_events_paginated(offset=0, limit=limit_events)['events']
        event_ids = [e['eventId'] for e in events]

        entities = self.get_all_entities()
        evolution_links = self.get_evolution_links_for_events(event_ids, min_score=min_evolution_score)
        event_entity_rels = self.get_event_entity_relationships(event_ids)

        return {
            'nodes': {'entities': entities, 'events': events},
            'edges': {'evolution': evolution_links, 'event_entity': event_entity_rels},
            'stats': {
                'total_entities': len(entities),
                'total_events': len(events),
                'evolution_links': len(evolution_links),
                'event_entity_links': len(event_entity_rels),
            },
        }

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def _get_date_range(self) -> Dict:
        rows = self._bindings(
            f"{PREFIXES}SELECT (MIN(?date) AS ?start) (MAX(?date) AS ?end) "
            f"WHERE {{ ?e a feekg:Event . ?e feekg:date ?date . }}"
        )
        b = rows[0] if rows else {}
        return {'start': _value(b, 'start'), 'end': _value(b, 'end')}

    def _get_event_type_distribution(self) -> Dict[str, int]:
        rows = self._bindings(
            f"""{PREFIXES}
SELECT ?type (COUNT(?event) AS ?count)
WHERE {{ ?event a feekg:Event . ?event feekg:eventType ?type . }}
GROUP BY ?type
ORDER BY DESC(?count)
"""
        )
        return {b['type']['value']: int(b['count']['value']) for b in rows}

    def get_graph_stats_cached(self) -> Dict:
        """Totals, date range and event-type distribution (cached)."""

        def compute() -> Dict:
            return {
                'total_events': self.get_total_event_count(),
                'total_entities': self._count('?s a feekg:Entity .', distinct=True),
                'total_links': self._count('?s feekg:evolvesTo ?o .'),
                'date_range': self._get_date_range(),
                'event_type_distribution': self._get_event_type_distribution(),
                'timestamp': time.time(),
            }

        return self._cached('graph_stats', compute)

    def get_graph_stats(self) -> Dict:
        """Node/edge totals and the most-connected entities (cached)."""

        def compute() -> Dict:
            stats = {
                'totalEvents': self.get_total_event_count(),
                'totalEntities': self._count('?s a feekg:Entity .', distinct=True),
                'evolutionLinks': self._count('?s a feekg:EvolutionLink .', distinct=True),
                'totalRelationships': self._count('?event feekg:involves ?entity .', var='*'),
            }
            rows = self._bindings(
                f"""{PREFIXES}
SELECT ?entity ?label (COUNT(?event) AS ?degree)
WHERE {{
    ?entity a feekg:Entity .
    ?entity rdfs:label ?label .
    ?event feekg:involves ?entity .
}}
GROUP BY ?entity ?label
ORDER BY DESC(?degree)
LIMIT 10
"""
            )
            stats['topEntities'] = [
                {
                    'id': local_id_from_uri(b['entity']['value']),
                    'label': b['label']['value'],
                    'degree': int(b['degree']['value']),
                }
                for b in rows
            ]
            stats['totalNodes'] = stats['totalEvents'] + stats['totalEntities']
            stats['totalEdges'] = stats['evolutionLinks'] + stats['totalRelationships']
            return stats

        return self._cached('graph_stats_full', compute)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    backend = OptimizedGraphBackend()

    page = backend.get_events_paginated(offset=0, limit=10)
    print(f"Total events: {page['total']} (returned {len(page['events'])}, has_more={page['has_more']})")

    sept = backend.get_events_by_timewindow('2008-09-01', '2008-09-30')
    print(f"Events in Sept 2008: {len(sept)}")

    hubs = backend.get_high_impact_events(min_degree=5, limit=20)
    print(f"Hub events: {len(hubs)}")

    stats = backend.get_graph_stats_cached()
    print(f"Entities: {stats['total_entities']}  Links: {stats['total_links']}  "
          f"Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
