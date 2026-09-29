"""
Capital IQ events (output of ``feekg_core/ingestion/process_capital_iq_v4.py``).

The v4 processor already rewrites company names to canonical form. For a fair
ablation the radar must see the *raw* name, so ``mention`` is taken from
``csvSource.companyName`` (the original Capital IQ field) when present.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List

from radar.domain import Event


def load_capital_iq_events(path: Path, use_raw_names: bool = True) -> List[Event]:
    doc = json.loads(Path(path).read_text())
    events: List[Event] = []
    for e in doc["events"]:
        if not e.get("date"):
            continue
        src = e.get("csvSource") or {}
        mention = (src.get("companyName") if use_raw_names else None) or e.get("actor") or ""
        events.append(Event(
            id=e["eventId"],
            date=date.fromisoformat(e["date"][:10]),
            event_type=e.get("type", "unknown"),
            mention=mention,
            headline=e.get("headline", ""),
            source_type=src.get("originalEventType"),
        ))
    return events
