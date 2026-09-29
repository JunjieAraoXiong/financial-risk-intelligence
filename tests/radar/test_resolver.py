from radar.domain import Entity
from radar.resolver import ExactResolver, OntologyResolver, normalize, strip_suffixes

ENTITIES = [
    Entity("lbhi", "Lehman Brothers Holdings Inc.", aliases=("Lehman Brothers", "LBHI"), ticker="LEH"),
    Entity("lbi", "Lehman Brothers Inc."),
    Entity("aig", "American International Group, Inc.", aliases=("AIG",), ticker="AIG"),
    Entity("bofa", "Bank of America Corporation", aliases=("BofA",), ticker="BAC"),
]


def test_normalize_and_strip():
    assert normalize("  AT&T  Inc. ") == "at and t inc"
    assert strip_suffixes(normalize("The Goldman Sachs Group, Inc.")) == "goldman sachs"


def test_exact_is_literal():
    r = ExactResolver(ENTITIES)
    assert r.resolve("Lehman Brothers Holdings Inc.") == "lbhi"
    assert r.resolve("LEHMAN BROTHERS HOLDINGS INC") is None
    assert r.resolve("AIG") is None


def test_ontology_variants_aliases_tickers():
    r = OntologyResolver(ENTITIES)
    assert r.resolve("LEHMAN BROTHERS HOLDINGS, INC") == "lbhi"
    assert r.resolve("Lehman Brothers") == "lbhi"          # explicit alias wins
    assert r.resolve("BAC") == "bofa"
    assert r.resolve("American International Group Inc") == "aig"
    assert r.resolve("Bank of America Corp.") == "bofa"     # suffix-stripped, unique


def test_ambiguous_suffix_strip_refuses_to_guess():
    # Both Lehman entities strip to "lehman brothers" unless an alias disambiguates.
    r = OntologyResolver([Entity("a", "Lehman Brothers Holdings Inc."), Entity("b", "Lehman Brothers Inc.")])
    assert r.resolve("Lehman Brothers Corp") is None
    assert r.resolve("Unknown Bank") is None
    assert r.resolve("") is None
