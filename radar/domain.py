"""
Core data types for the portfolio risk radar.

Everything that can change over time (ownership, exposures) carries a validity
interval so the backtest can reconstruct what was knowable on any given date.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Tuple

# Relation kinds.
SUBSIDIARY_OF = "subsidiary_of"   # source is owned by target (shock at source rolls up to target)
EXPOSED_TO = "exposed_to"         # source has credit/funding exposure to target (shock at target hits source)
PEER = "peer"                     # symmetric similarity (same business model / funding market)

RELATION_KINDS = (SUBSIDIARY_OF, EXPOSED_TO, PEER)


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    aliases: Tuple[str, ...] = ()
    ticker: Optional[str] = None
    type: str = "company"


@dataclass(frozen=True)
class Relation:
    source: str
    target: str
    kind: str
    weight: float = 1.0
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None   # exclusive

    def __post_init__(self):
        if self.kind not in RELATION_KINDS:
            raise ValueError(f"Unknown relation kind {self.kind!r}; expected one of {RELATION_KINDS}")
        if not 0.0 < self.weight <= 1.0:
            raise ValueError("Relation weight must be in (0, 1]")

    def active_on(self, d: date) -> bool:
        if self.valid_from and d < self.valid_from:
            return False
        if self.valid_to and d >= self.valid_to:
            return False
        return True


@dataclass(frozen=True)
class Event:
    id: str
    date: date
    event_type: str          # FE-EKG event type, e.g. "credit_downgrade"
    mention: str             # company name exactly as written in the source
    headline: str = ""
    source_type: Optional[str] = None   # raw vendor category (Capital IQ type, 8-K item)


@dataclass(frozen=True)
class Alert:
    date: date               # date the information became available
    entity_id: str           # portfolio holding that is flagged
    score: float
    source: str              # event id, or baseline name
    risk_category: str = "unclassified"
    path: Tuple[str, ...] = field(default_factory=tuple)   # entity ids from shocked entity to holding

    def explain(self) -> str:
        chain = " → ".join(self.path) if self.path else self.entity_id
        return f"{self.date} {self.entity_id}: {self.risk_category} via {chain} (score {self.score:.2f}, {self.source})"
