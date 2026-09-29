"""
A synthetic market with known ground truth, for testing the backtest plumbing.

Distress starts at a firm, is announced through events that name the firm in
inconsistent ways (variants, tickers, subsidiaries), and spreads with a lag to
firms exposed to it, which get no events of their own. Unrelated noise events
occur throughout.

Results on this data only show that the pipeline measures what it should; the
world is built so that ontology features help. They are not evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Set, Tuple

import numpy as np
import pandas as pd

from radar.domain import EXPOSED_TO, SUBSIDIARY_OF, Entity, Event, Relation

NEGATIVE_TYPES = ("credit_downgrade", "earnings_loss", "capital_raising", "government_intervention")
NOISE_NEGATIVE_TYPES = ("management_change", "legal_issue", "stock_movement")
BENIGN_TYPES = ("earnings_announcement", "business_operations", "merger_acquisition", "strategic_partnership")


@dataclass
class SyntheticWorld:
    entities: List[Entity]
    relations: List[Relation]
    events: List[Event]
    prices: pd.DataFrame
    portfolio: Set[str]
    start: date
    end: date
    shocks: List[Tuple[str, date]]


def make_world(
    n_firms: int = 40,
    n_shocks: int = 14,
    exposures_per_firm: int = 2,
    contagion_prob: float = 0.7,
    seed: int = 7,
    start: date = date(2007, 1, 2),
    end: date = date(2009, 12, 31),
) -> SyntheticWorld:
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, end)
    n_days = len(days)

    entities: List[Entity] = []
    relations: List[Relation] = []
    subsidiaries = {}
    for i in range(n_firms):
        fid = f"f{i:02d}"
        base = f"Firm{i:02d}"
        entities.append(Entity(id=fid, name=f"{base} Holdings Inc.", aliases=(base,), ticker=f"F{i:02d}"))
        subs = []
        for j, suffix in enumerate(("Securities LLC", "Bank N.A.")[: 1 + int(rng.integers(0, 2))]):
            sid = f"{fid}_s{j}"
            entities.append(Entity(id=sid, name=f"{base} {suffix}", type="subsidiary"))
            relations.append(Relation(sid, fid, SUBSIDIARY_OF))
            subs.append(f"{base} {suffix}")
        subsidiaries[fid] = subs

    firm_ids = [f"f{i:02d}" for i in range(n_firms)]
    exposed_to_me = {fid: [] for fid in firm_ids}
    for fid in firm_ids:
        others = [o for o in firm_ids if o != fid]
        for target in rng.choice(others, size=exposures_per_firm, replace=False):
            relations.append(Relation(fid, str(target), EXPOSED_TO, weight=float(rng.uniform(0.8, 1.0))))
            exposed_to_me[str(target)].append(fid)

    def mention(fid: str) -> str:
        i = int(fid[1:])
        base = f"Firm{i:02d}"
        forms = [
            f"{base} Holdings Inc.",                # exact
            f"{base.upper()} HOLDINGS, INC",        # formatting variant
            base,                                   # alias
            f"F{i:02d}",                            # ticker
            str(rng.choice(subsidiaries[fid])),     # subsidiary
        ]
        return forms[int(rng.choice(len(forms), p=[0.3, 0.25, 0.15, 0.1, 0.2]))]

    # Log-price paths with idiosyncratic noise; shocks add deterministic drops.
    log_ret = rng.normal(0.0002, 0.015, size=(n_firms, n_days))
    events: List[Event] = []
    eid = 0

    def add_event(d, etype, fid):
        nonlocal eid
        eid += 1
        events.append(Event(id=f"syn_{eid}", date=d.date(), event_type=etype, mention=mention(fid)))

    def add_drop(firm_idx: int, first_day: int, total: float, span: int = 10):
        per_day = np.log(1 - total) / span
        log_ret[firm_idx, first_day:first_day + span] += per_day

    shock_days = rng.choice(np.arange(120, n_days - 60), size=n_shocks, replace=False)
    shock_firms = rng.choice(firm_ids, size=n_shocks, replace=False)
    shocks = []
    for fid, d in zip(shock_firms, shock_days):
        fid = str(fid)
        shocks.append((fid, days[d].date()))
        for lag in sorted(rng.choice(np.arange(2, 11), size=int(rng.integers(1, 4)), replace=False)):
            add_event(days[d - lag], str(rng.choice(NEGATIVE_TYPES)), fid)
        add_drop(int(fid[1:]), d, 0.35)
        for victim in exposed_to_me[fid]:
            if rng.random() < contagion_prob:
                add_drop(int(victim[1:]), d + 3, 0.28)

    for d in range(n_days):
        for _ in range(int(rng.poisson(3))):
            add_event(days[d], str(rng.choice(BENIGN_TYPES)), str(rng.choice(firm_ids)))
        if rng.random() < 0.05:
            add_event(days[d], str(rng.choice(NOISE_NEGATIVE_TYPES)), str(rng.choice(firm_ids)))

    closes = 50.0 * np.exp(np.cumsum(log_ret, axis=1))
    prices = pd.DataFrame({
        "date": np.tile(days, n_firms),
        "entity_id": np.repeat(firm_ids, n_days),
        "close": closes.ravel(),
    })
    return SyntheticWorld(entities, relations, events, prices, set(firm_ids),
                          days[0].date(), days[-1].date(), shocks)
