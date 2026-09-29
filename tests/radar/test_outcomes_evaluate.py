
import numpy as np
import pandas as pd
import pytest

from radar.domain import Alert
from radar.evaluate import EvalSpec, align_alerts, evaluate
from radar.outcomes import OutcomeSpec, label_distress

DAYS = pd.date_range("2008-01-01", periods=60, freq="D")
SPEC = OutcomeSpec(horizon_days=5, threshold=0.2)


def prices():
    crash = np.r_[np.full(30, 100.0), np.full(30, 70.0)]     # A drops 30% on day 30
    flat = np.full(60, 50.0)                                  # B never moves
    delisted = np.r_[np.full(20, 40.0), [20.0]]               # C halves, then stops trading
    return pd.DataFrame({
        "date": list(DAYS) * 2 + list(DAYS[:21]),
        "entity_id": ["A"] * 60 + ["B"] * 60 + ["C"] * 21,
        "close": np.r_[crash, flat, delisted],
    })


def day(i):
    return DAYS[i].date()


def test_labels_onset_and_crash_date():
    lab = label_distress(prices(), SPEC).set_index(["entity_id", "date"])
    a = lab.loc["A"]
    assert list(a["distressed"].iloc[24:31]) == [0, 1, 1, 1, 1, 1, 0]
    assert a["onset"].sum() == 1 and a["onset"].iloc[25]
    assert a["crash_date"].iloc[25] == DAYS[30]
    assert a["distressed"].iloc[-5:].isna().all()           # still trading: tail unlabeled


def test_delisted_series_keeps_truncated_window():
    c = label_distress(prices(), SPEC).set_index(["entity_id", "date"]).loc["C"]
    assert c["distressed"].iloc[19] == 1 and np.isnan(c["distressed"].iloc[20])
    assert c["distressed"].iloc[15] == 1                     # 5-day window reaches the final drop


def test_alert_acts_next_trading_day():
    lab = label_distress(prices(), SPEC)
    aligned = align_alerts([Alert(day(24), "A", 0.9, "e"), Alert(day(24), "A", 0.5, "e2")], lab)
    assert list(aligned["date"]) == [DAYS[25]] and aligned["score"].iloc[0] == 0.9


def test_precision_recall_lead():
    lab = label_distress(prices(), SPEC)
    good = [Alert(day(24), "A", 1.0, "e1")]              # acts day 25, crash day 30
    late = [Alert(day(30), "A", 1.0, "e2")]              # announced on crash day
    noise = [Alert(day(10), "B", 1.0, "e3")]
    spec = EvalSpec(lookback_days=30, bootstrap=0)
    m = evaluate(good + noise, lab, {"A", "B"}, day(0), day(59), spec)
    assert m["precision"] == pytest.approx(0.5)
    assert m["recall"] == pytest.approx(1.0) and m["onsets"] == 1
    assert m["median_lead_days"] == 5
    assert m["lift"] == pytest.approx(0.5 / m["base_rate"])
    late_m = evaluate(late, lab, {"A", "B"}, day(0), day(59), spec)
    assert late_m["recall"] == 0 and late_m["precision"] == 0


def test_bootstrap_interval_brackets_point():
    lab = label_distress(prices(), SPEC)
    alerts = [Alert(day(24), "A", 1.0, "e1"), Alert(day(10), "B", 1.0, "e3")]
    m = evaluate(alerts, lab, {"A", "B", "C"}, day(0), day(59), EvalSpec(bootstrap=300, seed=1))
    assert m["precision_ci_low"] <= m["precision"] <= m["precision_ci_high"]


def test_price_validation():
    bad = prices()
    bad.loc[0, "close"] = -1
    with pytest.raises(ValueError):
        label_distress(bad, SPEC)
    with pytest.raises(ValueError):
        label_distress(pd.concat([prices(), prices().head(1)]), SPEC)
