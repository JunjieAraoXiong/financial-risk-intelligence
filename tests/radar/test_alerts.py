from datetime import date

from radar.alerts import AlertEngine, RadarConfig
from radar.domain import EXPOSED_TO, SUBSIDIARY_OF, Entity, Event, Relation
from radar.graph import OntologyGraph

ENTITIES = [
    Entity("hold", "Holdco Inc.", ticker="HLD"),
    Entity("hold_sub", "Holdco Securities LLC"),
    Entity("bank", "Bank Corp"),
]
RELATIONS = [
    Relation("hold_sub", "hold", SUBSIDIARY_OF, valid_from=date(2008, 3, 1)),
    Relation("hold", "bank", EXPOSED_TO),
]
G = OntologyGraph(ENTITIES, RELATIONS)


def ev(i, d, etype, mention):
    return Event(f"e{i}", d, etype, mention)


def run(cfg, events, portfolio=frozenset({"hold"}), **kw):
    return AlertEngine(G, cfg).run(events, set(portfolio), **kw)


def test_taxonomy_ignores_benign_events():
    events = [ev(1, date(2008, 5, 1), "earnings_announcement", "Holdco Inc."),
              ev(2, date(2008, 5, 2), "credit_downgrade", "Holdco Inc.")]
    alerts = run(RadarConfig("full"), events)
    assert [a.source for a in alerts] == ["e2"]
    assert alerts[0].risk_category == "credit"
    assert len(run(RadarConfig("no_tax", taxonomy=False), events)) == 2


def test_subsidiary_event_respects_ownership_date():
    before = [ev(1, date(2008, 2, 1), "credit_downgrade", "Holdco Securities LLC")]
    after = [ev(2, date(2008, 4, 1), "credit_downgrade", "Holdco Securities LLC")]
    assert run(RadarConfig("full"), before) == []
    [a] = run(RadarConfig("full"), after)
    assert a.path == ("hold_sub", "hold")
    assert run(RadarConfig("flat", hierarchy=False), after) == []


def test_propagation_and_threshold():
    e = [ev(1, date(2008, 5, 1), "bankruptcy", "Bank Corp")]
    [a] = run(RadarConfig("full", max_hops=1, decay=0.5), e)
    assert a.score == 0.5 and a.path == ("bank", "hold")
    assert run(RadarConfig("direct", max_hops=0), e) == []
    weak = [ev(2, date(2008, 5, 1), "capital_raising", "Bank Corp")]   # 0.4 * 0.5 < 0.3
    assert run(RadarConfig("full", max_hops=1, decay=0.5), weak) == []


def test_resolver_choice_and_unresolved_count():
    e = [ev(1, date(2008, 5, 1), "credit_downgrade", "HLD")]
    engine = AlertEngine(G, RadarConfig("exact", resolver="exact"))
    assert engine.run(e, {"hold"}) == [] and engine.unresolved == 1
    assert len(run(RadarConfig("onto"), e)) == 1


def test_window_excludes_later_events():
    e = [ev(1, date(2008, 5, 1), "credit_downgrade", "Holdco Inc."),
         ev(2, date(2009, 5, 1), "credit_downgrade", "Holdco Inc.")]
    alerts = run(RadarConfig("full"), e, start=date(2008, 1, 1), end=date(2008, 12, 31))
    assert [a.source for a in alerts] == ["e1"]
