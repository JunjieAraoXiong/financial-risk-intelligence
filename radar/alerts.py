"""
Alert engine: replays an event stream in date order and flags portfolio holdings.

Each ``RadarConfig`` switches one ontology capability on or off, which is what
the ablation study compares.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Iterable, List, Optional, Set

from radar import taxonomy
from radar.domain import Alert, Event
from radar.graph import OntologyGraph
from radar.resolver import build_resolver


@dataclass(frozen=True)
class RadarConfig:
    name: str
    resolver: str = "ontology"      # "exact" | "ontology"
    hierarchy: bool = True          # roll subsidiary events up to owners
    max_hops: int = 1               # exposure-network propagation depth
    taxonomy: bool = True           # weight events by risk severity (else every event counts 1.0)
    decay: float = 0.5              # weight multiplier per propagation hop
    min_score: float = 0.3          # alert threshold

    def as_dict(self) -> dict:
        return asdict(self)


class AlertEngine:
    def __init__(self, graph: OntologyGraph, config: RadarConfig):
        self.graph = graph
        self.config = config
        self.resolver = build_resolver(config.resolver, graph.entities.values())
        self.unresolved = 0

    def _severity(self, event: Event):
        if not self.config.taxonomy:
            return "unclassified", 1.0
        return taxonomy.classify(event.event_type)

    def run(
        self,
        events: Iterable[Event],
        portfolio: Set[str],
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> List[Alert]:
        """Alerts for ``portfolio`` holdings from events dated within [start, end]."""
        cfg = self.config
        alerts: List[Alert] = []
        self.unresolved = 0

        for event in sorted(events, key=lambda e: (e.date, e.id)):
            if (start and event.date < start) or (end and event.date > end):
                continue
            category, severity = self._severity(event)
            if category == taxonomy.NONE or severity < cfg.min_score:
                continue
            entity_id = self.resolver.resolve(event.mention)
            if entity_id is None:
                self.unresolved += 1
                continue
            for impact in self.graph.affected(
                entity_id, event.date, use_hierarchy=cfg.hierarchy, max_hops=cfg.max_hops, decay=cfg.decay
            ):
                score = severity * impact.weight
                if impact.entity_id in portfolio and score >= cfg.min_score:
                    alerts.append(Alert(
                        date=event.date,
                        entity_id=impact.entity_id,
                        score=round(score, 4),
                        source=event.id,
                        risk_category=category,
                        path=impact.path,
                    ))
        return alerts


# The ablation ladder. Rung 1 is what a plain news-alert product does: flag a
# holding when a negative event names it verbatim. Each later rung adds one
# ontology capability. The last row removes the risk taxonomy from the full
# system (every event counts), to show what the taxonomy contributes.
ABLATION_LADDER = (
    RadarConfig("1_direct_mentions", resolver="exact", hierarchy=False, max_hops=0),
    RadarConfig("2_+entity_resolution", resolver="ontology", hierarchy=False, max_hops=0),
    RadarConfig("3_+ownership_hierarchy", resolver="ontology", hierarchy=True, max_hops=0),
    RadarConfig("4_+exposure_propagation", resolver="ontology", hierarchy=True, max_hops=1),
    RadarConfig("5_full_minus_taxonomy", resolver="ontology", hierarchy=True, max_hops=1, taxonomy=False),
)
