"""
Price-only baseline: flag a stock when its recent volatility spikes.

An ontology-driven radar is only useful if it beats (or adds to) what prices
already say. This baseline uses information available at the close of day t
only, and is scored with the same next-trading-day rule as event alerts.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from radar.domain import Alert
from radar.outcomes import validate_prices


def volatility_alerts(
    prices: pd.DataFrame,
    window: int = 20,
    reference: int = 250,
    multiple: float = 2.0,
) -> List[Alert]:
    """Alert when trailing ``window``-day realized vol exceeds ``multiple`` × its trailing median."""
    df = validate_prices(prices)
    alerts: List[Alert] = []
    for entity_id, g in df.groupby("entity_id", sort=True):
        ret = np.log(g["close"]).diff()
        vol = ret.rolling(window, min_periods=window).std()
        ref = vol.rolling(reference, min_periods=window).median()
        ratio = vol / ref
        fired = ratio > multiple
        for d, r in zip(g.loc[fired, "date"], ratio[fired]):
            alerts.append(Alert(
                date=d.date(),
                entity_id=entity_id,
                score=round(float(min(r / (2 * multiple), 1.0)), 4),
                source=f"volatility_x{multiple:g}",
                risk_category="market",
                path=(entity_id,),
            ))
    return alerts
