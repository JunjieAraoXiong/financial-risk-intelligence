from shared.config.entity_aliases import get_all_aliases, get_canonical_name


def test_canonical_lookup():
    assert get_canonical_name("American International Group") == "AIG"
    assert get_canonical_name("jpmorgan chase") == "JPMorgan"
    assert get_canonical_name("Unknown Co") == "Unknown Co"
    assert get_canonical_name("") == ""


def test_all_aliases_include_canonical():
    aliases = get_all_aliases("Lehman Brothers")
    assert aliases[0] == "Lehman Brothers"
    assert "Lehman Brothers Holdings Inc." in aliases
