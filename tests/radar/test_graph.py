from datetime import date

import pytest

from radar.domain import EXPOSED_TO, PEER, SUBSIDIARY_OF, Entity, Relation
from radar.graph import OntologyGraph

E = [Entity(x, x) for x in ("parent", "sub", "creditor", "debtor", "acquirer", "target", "peer")]


def graph(*relations):
    return OntologyGraph(E, relations)


def ids(impacts):
    return {i.entity_id: i for i in impacts}


def test_hierarchy_rolls_up_not_down():
    g = graph(Relation("sub", "parent", SUBSIDIARY_OF))
    up = ids(g.affected("sub", date(2008, 1, 1), max_hops=0))
    assert set(up) == {"sub", "parent"} and up["parent"].path == ("sub", "parent")
    assert set(ids(g.affected("parent", date(2008, 1, 1), max_hops=0))) == {"parent"}
    assert set(ids(g.affected("sub", date(2008, 1, 1), use_hierarchy=False, max_hops=0))) == {"sub"}


def test_ownership_is_point_in_time():
    g = graph(Relation("target", "acquirer", SUBSIDIARY_OF, valid_from=date(2008, 7, 1)))
    assert "acquirer" not in ids(g.affected("target", date(2008, 6, 30), max_hops=0))
    assert "acquirer" in ids(g.affected("target", date(2008, 7, 1), max_hops=0))


def test_exposure_direction_and_decay():
    g = graph(Relation("creditor", "debtor", EXPOSED_TO, weight=0.8))
    hit = ids(g.affected("debtor", date(2008, 1, 1), max_hops=1, decay=0.5))
    assert hit["creditor"].weight == pytest.approx(0.4)
    assert hit["creditor"].path == ("debtor", "creditor")
    assert "debtor" not in ids(g.affected("creditor", date(2008, 1, 1), max_hops=1))
    assert "creditor" not in ids(g.affected("debtor", date(2008, 1, 1), max_hops=0))


def test_propagated_shock_rolls_up_to_owner():
    g = graph(Relation("sub", "parent", SUBSIDIARY_OF), Relation("sub", "debtor", EXPOSED_TO))
    hit = ids(g.affected("debtor", date(2008, 1, 1), max_hops=1, decay=0.5))
    assert hit["parent"].path == ("debtor", "sub", "parent")


def test_peer_is_symmetric_and_cycles_terminate():
    g = graph(Relation("parent", "peer", PEER), Relation("peer", "parent", EXPOSED_TO))
    assert "parent" in ids(g.affected("peer", date(2008, 1, 1), max_hops=3))
    assert "peer" in ids(g.affected("parent", date(2008, 1, 1), max_hops=3))


def test_unknown_entity_in_relation_rejected():
    with pytest.raises(ValueError):
        OntologyGraph(E, [Relation("sub", "nobody", SUBSIDIARY_OF)])
