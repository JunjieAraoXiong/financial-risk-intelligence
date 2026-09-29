"""
Ablation study: run every rung of the ontology ladder (plus the price baseline)
on the same events, prices and window, and tabulate the metrics.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import pandas as pd

from radar.alerts import ABLATION_LADDER, AlertEngine, RadarConfig
from radar.baselines import volatility_alerts
from radar.domain import Event
from radar.evaluate import EvalSpec, evaluate
from radar.graph import OntologyGraph
from radar.outcomes import OutcomeSpec, label_distress

TABLE_COLUMNS = [
    ("config", "Configuration"),
    ("alert_days", "Alert-days"),
    ("precision", "Precision"),
    ("lift", "Lift vs base rate"),
    ("recall", "Recall"),
    ("median_lead_days", "Median lead (days)"),
    ("unresolved_events", "Unresolved events"),
]


@dataclass
class BacktestResult:
    table: pd.DataFrame
    alerts: Dict[str, list] = field(default_factory=dict)
    manifest: Dict = field(default_factory=dict)


def run_ablation(
    graph: OntologyGraph,
    events: Sequence[Event],
    prices: pd.DataFrame,
    portfolio: Set[str],
    start: date,
    end: date,
    configs: Iterable[RadarConfig] = ABLATION_LADDER,
    outcome: OutcomeSpec = OutcomeSpec(),
    eval_spec: EvalSpec = EvalSpec(),
    include_baseline: bool = True,
) -> BacktestResult:
    configs = list(configs)
    labels = label_distress(prices, outcome)
    missing = portfolio - set(labels["entity_id"])
    if missing:
        raise ValueError(f"No prices for portfolio entities: {sorted(missing)[:10]}")

    rows: List[Dict] = []
    all_alerts: Dict[str, list] = {}
    for cfg in configs:
        engine = AlertEngine(graph, cfg)
        alerts = engine.run(events, portfolio, start=start, end=end)
        all_alerts[cfg.name] = alerts
        rows.append({"config": cfg.name, "unresolved_events": engine.unresolved,
                     **evaluate(alerts, labels, portfolio, start, end, eval_spec)})

    if include_baseline:
        alerts = [a for a in volatility_alerts(prices) if a.entity_id in portfolio]
        all_alerts["baseline_volatility"] = alerts
        rows.append({"config": "baseline_volatility", "unresolved_events": 0,
                     **evaluate(alerts, labels, portfolio, start, end, eval_spec)})

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "portfolio_size": len(portfolio),
        "events": len(events),
        "outcome": asdict(outcome),
        "evaluation": asdict(eval_spec),
        "configs": [c.as_dict() for c in configs],
    }
    return BacktestResult(table=pd.DataFrame(rows), alerts=all_alerts, manifest=manifest)


def _fmt(value, ci_low=None, ci_high=None, pct=False) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, float):
        fmt = (lambda v: f"{v:.1%}") if pct else (lambda v: f"{v:.2f}")
        text = fmt(value)
        if ci_low is not None and not math.isnan(ci_low):
            text += f" [{fmt(ci_low)}, {fmt(ci_high)}]"
        return text
    return str(value)


def to_markdown(table: pd.DataFrame) -> str:
    header = "| " + " | ".join(label for _, label in TABLE_COLUMNS) + " |"
    sep = "|" + "|".join("---" for _ in TABLE_COLUMNS) + "|"
    lines = [header, sep]
    for _, r in table.iterrows():
        cells = []
        for key, _ in TABLE_COLUMNS:
            if key in ("precision", "recall"):
                cells.append(_fmt(r.get(key), r.get(f"{key}_ci_low"), r.get(f"{key}_ci_high"), pct=True))
            elif key == "lift":
                cells.append(_fmt(r.get(key), r.get("lift_ci_low"), r.get("lift_ci_high")))
            else:
                cells.append(_fmt(r.get(key)))
        lines.append("| " + " | ".join(cells) + " |")
    base = table["base_rate"].dropna()
    if not base.empty:
        lines.append("")
        lines.append(f"Base rate (share of entity-days followed by a distress drawdown): {base.iloc[0]:.1%}. "
                     "Brackets are 95% entity-clustered bootstrap intervals.")
    return "\n".join(lines)


def write_result(result: BacktestResult, out_dir: Path, inputs: Optional[Dict[str, Path]] = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    result.table.to_csv(out_dir / "ablation.csv", index=False)
    (out_dir / "ablation.md").write_text(to_markdown(result.table) + "\n")
    alerts = [
        {"config": name, "date": a.date.isoformat(), "entity_id": a.entity_id, "score": a.score,
         "source": a.source, "risk_category": a.risk_category, "path": list(a.path)}
        for name, items in result.alerts.items() for a in items
    ]
    pd.DataFrame(alerts).to_csv(out_dir / "alerts.csv", index=False)
    manifest = dict(result.manifest)
    if inputs:
        manifest["inputs"] = {k: {"path": str(p), "sha256": _sha256(p)} for k, p in inputs.items()}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> Optional[str]:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
