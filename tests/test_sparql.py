import pytest

from feekg_core.query import sparql
from feekg_core.query.sparql import InvalidQueryParameter


@pytest.mark.parametrize("value", ["evt_1", "ent_lehman_brothers", "a.b-c_9"])
def test_local_name_accepts_ids(value):
    assert sparql.local_name(value) == value


@pytest.mark.parametrize("value", [
    "", "evt 1", "evt>1", 'x" } DROP ALL', "a{b}", "_leading", "x" * 201, None, "evt\n1",
])
def test_local_name_rejects_injection(value):
    with pytest.raises(InvalidQueryParameter):
        sparql.local_name(value)


def test_iri_and_list():
    assert sparql.iri("evt_1") == "<http://feekg.org/ontology#evt_1>"
    assert sparql.iri_list(["a", "b"]) == "<http://feekg.org/ontology#a>, <http://feekg.org/ontology#b>"


def test_iso_date():
    assert sparql.iso_date("2008-09-15") == "2008-09-15"
    for bad in ["2008-13-01", "15/09/2008", '2008-09-15"^^x', ""]:
        with pytest.raises(InvalidQueryParameter):
            sparql.iso_date(bad)


def test_number_and_integer():
    assert sparql.number("0.5") == "0.5"
    for bad in ["nan", "inf", "0.5) || true"]:
        with pytest.raises(InvalidQueryParameter):
            sparql.number(bad)
    assert sparql.integer("10") == 10
    with pytest.raises(InvalidQueryParameter):
        sparql.integer(-1)
    with pytest.raises(InvalidQueryParameter):
        sparql.integer("10; DROP")


def test_choice():
    assert sparql.choice("date", ["date", "type"]) == "date"
    with pytest.raises(InvalidQueryParameter):
        sparql.choice("date DESC", ["date", "type"])


def test_local_id_from_uri():
    assert sparql.local_id_from_uri("http://feekg.org/ontology#evt_1") == "evt_1"
    assert sparql.local_id_from_uri("http://x/y/z") == "z"
