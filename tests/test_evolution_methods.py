import math

from feekg_core.evolution.methods import EventEvolutionScorer, compute_all_evolution_links

ENTITIES = [{"entityId": "ent_a", "name": "A"}, {"entityId": "ent_b", "name": "B"}]


def evt(eid, date, etype, actor="ent_a", target=None, desc="bank faces liquidity pressure"):
    return {"eventId": eid, "date": date, "type": etype, "actor": actor, "target": target,
            "description": desc}


def scorer(events=()):
    return EventEvolutionScorer(list(events), ENTITIES)


def test_temporal_decay_matches_tcdi():
    s = scorer()
    a, b = evt("e1", "2008-09-01", "x"), evt("e2", "2008-09-06", "x")
    assert math.isclose(s.compute_temporal_correlation(a, b), math.exp(-0.5))


def test_temporal_is_zero_backwards_or_outside_window():
    s = scorer()
    a = evt("e1", "2008-09-10", "x")
    assert s.compute_temporal_correlation(a, evt("e0", "2008-09-01", "x")) == 0.0
    assert s.compute_temporal_correlation(a, a) == 0.0
    assert s.compute_temporal_correlation(a, evt("e2", "2008-12-01", "x")) == 0.0


def test_entity_overlap():
    s = scorer()
    same = s.compute_entity_overlap(evt("e1", "2008-01-01", "x"), evt("e2", "2008-01-02", "x"))
    none = s.compute_entity_overlap(evt("e1", "2008-01-01", "x"),
                                    evt("e2", "2008-01-02", "x", actor="ent_b"))
    assert same == 1.0 and none == 0.0


def test_scores_bounded_and_components_present():
    s = scorer()
    score, comps = s.compute_evolution_score(evt("e1", "2008-09-01", "liquidity_warning"),
                                             evt("e2", "2008-09-03", "credit_downgrade"))
    assert 0.0 <= score <= 1.0
    assert set(comps) == {"temporal", "entity_overlap", "semantic", "topic", "causality", "emotional"}
    assert all(0.0 <= v <= 1.0 for v in comps.values())


def test_compute_all_links_forward_only():
    events = [evt("e2", "2008-09-03", "credit_downgrade"), evt("e1", "2008-09-01", "liquidity_warning"),
              evt("e3", "2008-09-05", "debt_default")]
    links = compute_all_evolution_links(events, ENTITIES, threshold=0.2, use_parallel=False)
    assert links
    for link in links:
        assert link["from_date"] < link["to_date"]
        assert link["score"] >= 0.2
