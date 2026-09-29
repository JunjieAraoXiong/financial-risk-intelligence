"""
File formats.

Ontology (JSON)::

    {"entities": [{"id": "ent_lehman", "name": "Lehman Brothers Holdings Inc.",
                   "aliases": ["Lehman Brothers", "LBHI"], "ticker": "LEH", "type": "investment_bank"}],
     "relations": [{"source": "ent_lbsf", "target": "ent_lehman", "kind": "subsidiary_of",
                    "weight": 1.0, "valid_from": null, "valid_to": null}]}

Events (CSV): ``id, date, event_type, mention[, headline, source_type]``
Prices (CSV): ``date, entity_id, close`` (split/dividend-adjusted closes)
Portfolio (text): one entity id per line
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Set, Tuple

import pandas as pd

from radar.domain import Entity, Event, Relation


def _date(value) -> Optional[date]:
    return date.fromisoformat(value) if value else None


def load_ontology(path: Path) -> Tuple[List[Entity], List[Relation]]:
    doc = json.loads(Path(path).read_text())
    entities = [
        Entity(id=e["id"], name=e["name"], aliases=tuple(e.get("aliases", ())),
               ticker=e.get("ticker"), type=e.get("type", "company"))
        for e in doc["entities"]
    ]
    relations = [
        Relation(source=r["source"], target=r["target"], kind=r["kind"], weight=float(r.get("weight", 1.0)),
                 valid_from=_date(r.get("valid_from")), valid_to=_date(r.get("valid_to")))
        for r in doc.get("relations", [])
    ]
    return entities, relations


def load_events_csv(path: Path) -> List[Event]:
    df = pd.read_csv(path, dtype=str).fillna("")
    required = {"id", "date", "event_type", "mention"}
    if not required <= set(df.columns):
        raise ValueError(f"Events file needs columns {sorted(required)}")
    return [
        Event(id=r["id"], date=date.fromisoformat(r["date"][:10]), event_type=r["event_type"],
              mention=r["mention"], headline=r.get("headline", ""), source_type=r.get("source_type") or None)
        for _, r in df.iterrows()
    ]


def load_prices_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])


def load_portfolio(path: Path) -> Set[str]:
    return {line.strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.startswith("#")}
