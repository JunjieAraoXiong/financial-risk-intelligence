# Portfolio Risk Radar: backtest framework

The radar watches a stream of corporate events and flags portfolio holdings
that are exposed to them, explaining each alert with a path through the
ontology (`holding ← subsidiary ← counterparty hit by a downgrade`).

This package answers one question with numbers: **does each ontology
capability make the alerts better?** It replays history day by day, emits
alerts using only what was known at the time, and scores them against what
the stock price did next.

## Ablation ladder

| Row | What it adds |
|---|---|
| `1_direct_mentions` | Baseline news alert: a negative event names the holding verbatim |
| `2_+entity_resolution` | Name variants, aliases and tickers resolve to the same entity |
| `3_+ownership_hierarchy` | Events at a subsidiary roll up to its owners (point in time) |
| `4_+exposure_propagation` | Shocks spread one hop to entities exposed to the shocked one |
| `5_full_minus_taxonomy` | Full system with the risk taxonomy removed (every event counts) |
| `baseline_volatility` | Price-only: realized volatility spikes above 2× its trailing median |

Rows 1–4 all use the risk taxonomy (`radar/taxonomy.py`) to decide which
events are negative and how severe they are.

## Outcomes and metrics

- **Distress**: from day t, the stock falls at least 20% below its day-t
  close within the next 20 trading days. The run of such days is an
  *episode*; its *crash date* is the day the 20% loss is realized.
- **Timing**: an alert dated d is acted on at the first trading day after d.
  A price move on the announcement day is never credited as a prediction.
- **Precision**: share of alert-days followed by distress.
- **Lift**: precision divided by the base rate of distress over all
  entity-days in the window (1.0 = no better than chance).
- **Recall**: share of episodes with an alert from 30 days before the onset
  up to (not including) the crash date.
- **Median lead**: days from the earliest qualifying alert to the crash date.
- **Intervals**: 95% bootstrap intervals that resample *entities*, because
  alerts and outcomes for the same firm are correlated.

## Running it

```bash
# Plumbing check on a generated world (NOT evidence: it is built so the ontology helps)
python -m radar.backtest synthetic --out results/backtest/synthetic

# Real data
python -m radar.backtest run \
    --ontology radar/ontology/lehman_2008.json \
    --capital-iq data/capital_iq_processed/lehman_v4_deduped.json \
    --prices data/prices/lehman_2008.csv \
    --start 2007-01-01 --end 2009-12-31 \
    --out results/backtest/lehman_2008
```

Each run writes `ablation.md` (the table), `ablation.csv`, `alerts.csv`
(every alert with its explanation path) and `manifest.json` (git commit,
parameters, SHA-256 of every input file).

## Input formats

- **Ontology** (JSON): entities with aliases and tickers, and relations
  (`subsidiary_of`, `exposed_to`, `peer`) with optional `valid_from` /
  `valid_to`. See `radar/data/io.py` and the seed file
  `radar/ontology/lehman_2008.json`.
- **Events**: processed Capital IQ JSON (v4), or a CSV with
  `id,date,event_type,mention[,headline,source_type]`. The Capital IQ loader
  uses the *raw* company name so that entity resolution can be ablated.
- **Prices** (CSV): `date,entity_id,close`, adjusted closes, keyed by the
  ontology's entity ids. Many 2008 names (LEH, BSC, WM, WB, CFC) are delisted,
  so free sources that drop dead tickers will bias the result. Use a
  survivorship-free source (CRSP via WRDS, including delisting returns).
- **Portfolio** (optional): entity ids, one per line. The default is every
  entity that has prices.

## Guarding against fooling ourselves

- **Point in time**: ownership and exposures carry validity dates. Add an
  `exposed_to` link only from a source that was public at the time, and date
  it from that disclosure.
- **Fixed parameters**: taxonomy severities, thresholds and horizons are set
  before looking at real results. Change them only with a written reason, and
  report every configuration you ran.
- **Alias hindsight**: aliases listed for a firm must be names in use at the
  time, not ones learned later.
- **More than one crisis**: a result that holds only for 2008 is an anecdote.
  The next step is an SEC EDGAR 8-K event feed (items map to event types in
  `taxonomy.EDGAR_8K_ITEMS`), so the same test can run on 2020 and 2023.
