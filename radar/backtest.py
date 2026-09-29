"""
Command-line entry point for the ablation backtest.

    # Plumbing check on synthetic data (not evidence):
    python -m radar.backtest synthetic --out results/backtest/synthetic

    # Real data:
    python -m radar.backtest run \\
        --ontology radar/ontology/lehman_2008.json \\
        --capital-iq data/capital_iq_processed/lehman_v4_deduped.json \\
        --prices data/prices/lehman_2008.csv \\
        --start 2007-01-01 --end 2009-12-31 \\
        --out results/backtest/lehman_2008
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from radar.ablation import run_ablation, to_markdown, write_result
from radar.data.capital_iq import load_capital_iq_events
from radar.data.io import load_events_csv, load_ontology, load_portfolio, load_prices_csv
from radar.data.synthetic import make_world
from radar.evaluate import EvalSpec
from radar.graph import OntologyGraph
from radar.outcomes import OutcomeSpec


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--out", type=Path, required=True, help="Output directory")
    p.add_argument("--horizon", type=int, default=20, help="Outcome horizon in trading days")
    p.add_argument("--threshold", type=float, default=0.20, help="Drawdown that counts as distress")
    p.add_argument("--lookback", type=int, default=30, help="Days before onset an alert still counts")
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="radar.backtest", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    syn = sub.add_parser("synthetic", help="Run on a generated world with known ground truth")
    _add_common(syn)
    syn.add_argument("--world-seed", type=int, default=7)

    real = sub.add_parser("run", help="Run on real ontology, events and prices")
    _add_common(real)
    real.add_argument("--ontology", type=Path, required=True)
    events = real.add_mutually_exclusive_group(required=True)
    events.add_argument("--events", type=Path, help="Events CSV (id,date,event_type,mention,...)")
    events.add_argument("--capital-iq", type=Path, help="Processed Capital IQ JSON (v4)")
    real.add_argument("--prices", type=Path, required=True)
    real.add_argument("--portfolio", type=Path, help="Entity ids, one per line (default: all priced entities)")
    real.add_argument("--start", type=date.fromisoformat, required=True)
    real.add_argument("--end", type=date.fromisoformat, required=True)

    args = parser.parse_args(argv)
    outcome = OutcomeSpec(horizon_days=args.horizon, threshold=args.threshold)
    eval_spec = EvalSpec(lookback_days=args.lookback, bootstrap=args.bootstrap, seed=args.seed)

    if args.command == "synthetic":
        world = make_world(seed=args.world_seed)
        graph = OntologyGraph(world.entities, world.relations)
        result = run_ablation(graph, world.events, world.prices, world.portfolio, world.start, world.end,
                              outcome=outcome, eval_spec=eval_spec)
        result.manifest["data"] = {"synthetic": True, "world_seed": args.world_seed,
                                   "note": "Plumbing check only; the world is built so ontology features help."}
        inputs = None
    else:
        entities, relations = load_ontology(args.ontology)
        graph = OntologyGraph(entities, relations)
        event_list = (load_events_csv(args.events) if args.events
                      else load_capital_iq_events(args.capital_iq))
        prices = load_prices_csv(args.prices)
        portfolio = load_portfolio(args.portfolio) if args.portfolio else set(prices["entity_id"].unique())
        unknown = portfolio - set(graph.entities)
        if unknown:
            parser.error(f"Portfolio entities not in ontology: {sorted(unknown)[:10]}")
        result = run_ablation(graph, event_list, prices, portfolio, args.start, args.end,
                              outcome=outcome, eval_spec=eval_spec)
        inputs = {"ontology": args.ontology, "events": args.events or args.capital_iq, "prices": args.prices}
        if args.portfolio:
            inputs["portfolio"] = args.portfolio

    write_result(result, args.out, inputs)
    print(to_markdown(result.table))
    print(f"\nWrote {args.out}/ablation.md, ablation.csv, alerts.csv, manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
