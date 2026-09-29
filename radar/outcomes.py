"""
Outcome labels from prices: did the stock suffer a large drawdown soon after?

For each entity and trading day t:

    forward_drawdown(t) = min(close[t+1 .. t+H]) / close[t] - 1
    distressed(t)       = forward_drawdown(t) <= -threshold

A *distress episode* is a run of distressed days. Its ``onset`` is the first day
of the run, and its ``crash_date`` is the first later day on which the close is
``threshold`` below the onset close, i.e. when the loss has actually happened.
A useful warning arrives before ``crash_date``. A series
that ends before the data does (delisting) keeps its truncated windows, because
the delisting itself is the outcome; a series still trading at the end of the
data has its last H days left unlabeled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PRICE_COLUMNS = ("date", "entity_id", "close")


@dataclass(frozen=True)
class OutcomeSpec:
    horizon_days: int = 20        # trading days
    threshold: float = 0.20       # 20% drawdown


def validate_prices(prices: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in PRICE_COLUMNS if c not in prices.columns]
    if missing:
        raise ValueError(f"Price data missing columns: {missing}")
    df = prices.loc[:, list(PRICE_COLUMNS)].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    if (df["close"] <= 0).any():
        raise ValueError("Prices must be positive")
    if df.duplicated(["entity_id", "date"]).any():
        raise ValueError("Duplicate (entity_id, date) rows in price data")
    return df.sort_values(["entity_id", "date"]).reset_index(drop=True)


def label_distress(prices: pd.DataFrame, spec: OutcomeSpec = OutcomeSpec()) -> pd.DataFrame:
    """Per entity-day labels: fwd_drawdown, distressed (NaN = unlabeled), onset, crash_date (on onset rows)."""
    df = validate_prices(prices)
    data_end = df["date"].max()
    h = spec.horizon_days
    parts = []
    for entity_id, g in df.groupby("entity_id", sort=True):
        g = g.copy()
        future = g["close"].shift(-1)
        rev = future.iloc[::-1]
        fwd_min = rev.rolling(h, min_periods=1).min().iloc[::-1]
        fwd_n = rev.rolling(h, min_periods=1).count().iloc[::-1]
        g["fwd_drawdown"] = fwd_min / g["close"] - 1.0

        still_trading = g["date"].iloc[-1] >= data_end
        labeled = fwd_n >= (h if still_trading else 1)
        distressed = (g["fwd_drawdown"] <= -spec.threshold).astype(float)
        distressed[~labeled] = np.nan
        g["distressed"] = distressed

        flag = distressed.fillna(0.0).astype(bool)
        g["onset"] = flag & ~flag.shift(1, fill_value=False)
        g["crash_date"] = pd.NaT
        closes = g["close"].to_numpy()
        dates = g["date"].to_numpy()
        for pos in np.flatnonzero(g["onset"].to_numpy()):
            below = np.flatnonzero(closes[pos + 1:pos + 1 + h] <= closes[pos] * (1 - spec.threshold))
            if below.size:
                g.iloc[pos, g.columns.get_loc("crash_date")] = dates[pos + 1 + below[0]]
        parts.append(g)
    return pd.concat(parts, ignore_index=True)
