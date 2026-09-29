import pytest
import requests

from feekg_core.query.optimized_graph_queries import GraphQueryError, OptimizedGraphBackend
from feekg_core.query.sparql import InvalidQueryParameter

NS = "http://feekg.org/ontology#"


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses=None, exc=None):
        self.responses = list(responses or [])
        self.exc = exc
        self.queries = []

    def post(self, url, data=None, **kwargs):
        self.queries.append(data["query"])
        if self.exc:
            raise self.exc
        return self.responses.pop(0) if self.responses else FakeResponse({"results": {"bindings": []}})


def bindings(*rows):
    return FakeResponse({"results": {"bindings": [
        {k: {"value": v} for k, v in row.items()} for row in rows
    ]}})


def make(settings, session):
    return OptimizedGraphBackend(settings, session=session)


def test_network_failure_raises(settings):
    backend = make(settings, FakeSession(exc=requests.ConnectionError("boom")))
    with pytest.raises(GraphQueryError):
        backend.get_all_entities()


def test_http_error_raises(settings):
    backend = make(settings, FakeSession([FakeResponse({}, status=500)]))
    with pytest.raises(GraphQueryError):
        backend.get_all_entities()


def test_event_by_id_uses_iri(settings):
    session = FakeSession([bindings({"type": "merger", "date": "2008-09-15", "label": "L"})])
    event = make(settings, session).get_event_by_id("evt_1")
    assert event["eventId"] == "evt_1" and event["type"] == "merger"
    assert f"<{NS}evt_1> a feekg:Event" in session.queries[0]


def test_event_by_id_not_found(settings):
    assert make(settings, FakeSession()).get_event_by_id("evt_404") is None


def test_injection_rejected_before_query(settings):
    session = FakeSession()
    backend = make(settings, session)
    with pytest.raises(InvalidQueryParameter):
        backend.get_event_by_id('x"} ; DROP ALL ; {"')
    with pytest.raises(InvalidQueryParameter):
        backend.get_events_by_timewindow('2008-01-01" || true', "2008-12-31")
    with pytest.raises(InvalidQueryParameter):
        backend.get_events_paginated(order_by="date; DROP")
    with pytest.raises(InvalidQueryParameter):
        backend.get_evolution_links(min_score="0) || (1")
    assert session.queries == []


def test_timewindow_query_declares_xsd(settings):
    session = FakeSession()
    make(settings, session).get_events_by_timewindow("2008-09-01", "2008-09-30", entity_filter="ent_x")
    q = session.queries[0]
    assert "PREFIX xsd:" in q
    assert f"?event feekg:involves <{NS}ent_x>" in q


def test_timewindow_rejects_reversed_range(settings):
    with pytest.raises(InvalidQueryParameter):
        make(settings, FakeSession()).get_events_by_timewindow("2009-01-01", "2008-01-01")


def test_paginated_and_count_cached(settings):
    session = FakeSession([
        bindings({"eventId": "evt_1", "type": "t", "date": "2008-01-01", "label": "L", "confidence": "0.9"}),
        bindings({"count": "42"}),
        bindings({"eventId": "evt_2", "type": "t", "date": "2008-01-02", "label": "M"}),
    ])
    backend = make(settings, session)
    page = backend.get_events_paginated(offset=0, limit=1)
    assert page["total"] == 42 and page["has_more"] is True
    assert page["events"][0]["confidence"] == 0.9
    backend.get_events_paginated(offset=1, limit=1)
    assert len(session.queries) == 3  # count query served from cache the second time


def test_evolution_links_parsing_and_event_filter(settings):
    session = FakeSession([bindings({"from": NS + "evt_1", "to": NS + "evt_2", "score": "0.7",
                                     "causality": "0.5"})])
    links = make(settings, session).get_evolution_links(limit=10, min_score=0.5, event_id="evt_1")
    assert links[0]["from"] == "evt_1" and links[0]["to"] == "evt_2"
    assert links[0]["causality"] == 0.5 and links[0]["semantic"] == 0.0
    assert f"FILTER(?from = <{NS}evt_1> || ?to = <{NS}evt_1>)" in session.queries[0]


def test_links_for_no_events_skips_query(settings):
    session = FakeSession()
    assert make(settings, session).get_evolution_links_for_events([]) == []
    assert make(settings, session).get_event_entity_relationships([]) == []
    assert session.queries == []
