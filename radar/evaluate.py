"""
Scoring alerts against distress outcomes, with entity-clustered bootstrap CIs.

Timing rule (conservative): an alert dated d is acted on at the first trading
day strictly after d, so any price reaction on the announcement day itself is
not credited as a prediction.

Metrics (per configuration):
- precision  share of alert-days followed by a distress drawdown
- base_rate  share of all labeled entity-days in the window that are distressed
- lift       precision / base_rate (1.0 = no better than chance)
- recall     share of distress episodes with an alert in the window from
             ``lookback_days`` before the onset up to (not including) the crash
             date, i.e. a warning issued before the loss had happened
- lead_days  median calendar days from the earliest such alert to the crash date
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Optional, Set

import numpy as np
import pandas as pd

from radar.domain import Alert

COUNT_COLUMNS = ("alert_days", "alert_hits", "labeled_days", "distressed_days", "onsets", "onsets_hit")


@dataclass(frozen=True)
class EvalSpec:
    lookback_days: int = 30
    bootstrap: int = 1000
    seed: int = 0


def align_alerts(alerts: Iterable[Alert], labels: pd.DataFrame) -> pd.DataFrame:
    """Map each alert to the first trading day after its date; one row per (entity, trading day)."""
    rows = [{"entity_id": a.entity_id, "alert_date": pd.Timestamp(a.date), "score": a.score} for a in alerts]
    if not rows:
        return pd.DataFrame(columns=["entity_id", "date", "score"])
    a = pd.DataFrame(rows)
    a["key"] = a["alert_date"] + pd.Timedelta(days=1)
    days = labels[["entity_id", "date"]].rename(columns={"date": "key"})
    days["date"] = days["key"]
    out = pd.merge_asof(
        a.sort_values("key"), days.sort_values("key"), on="key", by="entity_id", direction="forward",
    ).dropna(subset=["date"])
    return out.groupby(["entity_id", "date"], as_index=False)["score"].max()


def entity_counts(
    alerts: Iterable[Alert],
    labels: pd.DataFrame,
    portfolio: Set[str],
    start: date,
    end: date,
    spec: EvalSpec = EvalSpec(),
) -> pd.DataFrame:
    """Per-entity counts over the evaluation window; the bootstrap resamples these rows."""
    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    lab = labels[labels["entity_id"].isin(portfolio) & labels["date"].between(lo, hi)]
    aligned = align_alerts(alerts, labels)
    aligned = aligned[aligned["entity_id"].isin(portfolio) & aligned["date"].between(lo, hi)]
    aligned = aligned.merge(lab[["entity_id", "date", "distressed"]], on=["entity_id", "date"], how="left")
    aligned = aligned.dropna(subset=["distressed"])

    lookback = pd.Timedelta(days=spec.lookback_days)
    alert_dates: Dict[str, np.ndarray] = {
        eid: g["date"].to_numpy() for eid, g in aligned.groupby("entity_id")
    }

    rows = []
    leads = []
    for eid in sorted(portfolio):
        el = lab[lab["entity_id"] == eid]
        ea = aligned[aligned["entity_id"] == eid]
        episodes = el.loc[el["onset"], ["date", "crash_date"]]
        hit = 0
        dates = alert_dates.get(eid, np.array([], dtype="datetime64[ns]"))
        for onset, crash in episodes.itertuples(index=False):
            window = dates[(dates >= (onset - lookback).to_datetime64()) & (dates < crash.to_datetime64())]
            if window.size:
                hit += 1
                leads.append((crash - pd.Timestamp(window.min())).days)
        rows.append({
            "entity_id": eid,
            "alert_days": len(ea),
            "alert_hits": int(ea["distressed"].sum()),
            "labeled_days": int(el["distressed"].notna().sum()),
            "distressed_days": int(el["distressed"].sum(skipna=True)),
            "onsets": len(episodes),
            "onsets_hit": hit,
        })
    counts = pd.DataFrame(rows, columns=["entity_id", *COUNT_COLUMNS])
    counts.attrs["lead_days"] = leads
    return counts


def _ratio(num, den):
    return np.divide(num, den, out=np.full_like(num, np.nan, dtype=float), where=den > 0)


def metrics_from_totals(t: np.ndarray) -> Dict[str, np.ndarray]:
    """``t`` has COUNT_COLUMNS along its last axis (works for one row or a bootstrap matrix)."""
    t = np.asarray(t, dtype=float)
    alert_days, alert_hits, labeled, distressed, onsets, onsets_hit = np.moveaxis(t, -1, 0)
    precision = _ratio(alert_hits, alert_days)
    base_rate = _ratio(distressed, labeled)
    return {
        "precision": precision,
        "base_rate": base_rate,
        "lift": _ratio(precision, base_rate),
        "recall": _ratio(onsets_hit, onsets),
    }


def summarize(counts: pd.DataFrame, spec: EvalSpec = EvalSpec()) -> Dict[str, float]:
    """Point estimates plus 95% entity-clustered bootstrap intervals."""
    matrix = counts[list(COUNT_COLUMNS)].to_numpy(dtype=float)
    point = metrics_from_totals(matrix.sum(axis=0))
    result: Dict[str, float] = {k: float(v) for k, v in point.items()}
    totals = matrix.sum(axis=0)
    result.update({
        "alert_days": int(totals[0]),
        "onsets": int(totals[4]),
        "onsets_hit": int(totals[5]),
        "entities": len(counts),
    })
    leads = counts.attrs.get("lead_days", [])
    result["median_lead_days"] = float(np.median(leads)) if leads else float("nan")

    if spec.bootstrap and len(counts) > 1:
        rng = np.random.default_rng(spec.seed)
        idx = rng.integers(0, len(counts), size=(spec.bootstrap, len(counts)))
        boot = metrics_from_totals(matrix[idx].sum(axis=1))
        for name, values in boot.items():
            finite = values[np.isfinite(values)]
            lo, hi = (np.percentile(finite, [2.5, 97.5]) if finite.size else (np.nan, np.nan))
            result[f"{name}_ci_low"] = float(lo)
            result[f"{name}_ci_high"] = float(hi)
    return result


def evaluate(
    alerts: Iterable[Alert],
    labels: pd.DataFrame,
    portfolio: Set[str],
    start: date,
    end: date,
    spec: Optional[EvalSpec] = None,
) -> Dict[str, float]:
    spec = spec or EvalSpec()
    return summarize(entity_counts(alerts, labels, portfolio, start, end, spec), spec)
