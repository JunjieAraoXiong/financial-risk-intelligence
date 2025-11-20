"""
Entity Alias Resolution for Financial Institutions

Maps various spellings and variations of entity names to canonical forms.
Solves the duplicate entity problem (e.g., "AIG" vs "American International Group").

Usage:
    from config.entity_aliases import get_canonical_name

    canonical = get_canonical_name("American International Group")
    # Returns: "AIG"
"""

# Canonical entity name mappings
# Format: "Alias/Variation" -> "Canonical Name"
ENTITY_ALIASES = {
    # AIG variations
    'American International Group': 'AIG',
    'American International Group Inc.': 'AIG',
    'American International Group, Inc.': 'AIG',
    'American International Group Inc': 'AIG',
    'AIG Inc.': 'AIG',
    'A.I.G.': 'AIG',

    # JPMorgan variations
    'JPMorgan Chase & Co.': 'JPMorgan',
    'JPMorgan Chase & Co': 'JPMorgan',
    'JPMorgan Chase': 'JPMorgan',
    'JP Morgan Chase': 'JPMorgan',
    'JP Morgan': 'JPMorgan',
    'J.P. Morgan': 'JPMorgan',
    'J.P. Morgan Chase': 'JPMorgan',
    'JPMorgan Chase Bank': 'JPMorgan',

    # Bank of America variations
    'Bank of America Corporation': 'Bank of America',
    'Bank of America Corp.': 'Bank of America',
    'Bank of America Corp': 'Bank of America',
    'BofA': 'Bank of America',
    'B of A': 'Bank of America',
    'BankAmerica': 'Bank of America',
    'Bank of America, N.A.': 'Bank of America',

    # Goldman Sachs variations
    'Goldman Sachs Group Inc.': 'Goldman Sachs',
    'Goldman Sachs Group Inc': 'Goldman Sachs',
    'Goldman Sachs Group': 'Goldman Sachs',
    'The Goldman Sachs Group': 'Goldman Sachs',
    'The Goldman Sachs Group, Inc.': 'Goldman Sachs',
    'Goldman Sachs & Co.': 'Goldman Sachs',
    'Goldman, Sachs & Co.': 'Goldman Sachs',

    # Morgan Stanley variations
    'Morgan Stanley & Co.': 'Morgan Stanley',
    'Morgan Stanley & Co': 'Morgan Stanley',
    'Morgan Stanley Inc.': 'Morgan Stanley',
    'Morgan Stanley Inc': 'Morgan Stanley',
    'Morgan Stanley & Co. Inc.': 'Morgan Stanley',
    'Morgan Stanley Dean Witter': 'Morgan Stanley',

    # Merrill Lynch variations
    'Merrill Lynch & Co.': 'Merrill Lynch',
    'Merrill Lynch & Co': 'Merrill Lynch',
    'Merrill Lynch, Pierce, Fenner & Smith': 'Merrill Lynch',
    'Merrill Lynch Pierce Fenner & Smith': 'Merrill Lynch',
    'Merrill Lynch & Co., Inc.': 'Merrill Lynch',
    'Merrill Lynch Inc.': 'Merrill Lynch',

    # Lehman Brothers variations
    'Lehman Brothers Holdings Inc.': 'Lehman Brothers',
    'Lehman Brothers Holdings Inc': 'Lehman Brothers',
    'Lehman Brothers Holdings': 'Lehman Brothers',
    'Lehman Brothers Inc.': 'Lehman Brothers',
    'Lehman Brothers Inc': 'Lehman Brothers',

    # Citigroup variations
    'Citigroup Inc.': 'Citigroup',
    'Citigroup Inc': 'Citigroup',
    'Citi': 'Citigroup',
    'Citibank': 'Citigroup',
    'Citibank N.A.': 'Citigroup',
    'Citicorp': 'Citigroup',
    'Citi Inc.': 'Citigroup',

    # Bear Stearns variations
    'Bear Stearns Companies Inc.': 'Bear Stearns',
    'Bear Stearns Companies Inc': 'Bear Stearns',
    'Bear Stearns & Co.': 'Bear Stearns',
    'Bear Stearns & Co': 'Bear Stearns',
    'Bear, Stearns & Co.': 'Bear Stearns',
    'The Bear Stearns Companies': 'Bear Stearns',

    # Deutsche Bank variations
    'Deutsche Bank AG': 'Deutsche Bank',
    'Deutsche Bank Aktiengesellschaft': 'Deutsche Bank',
    'DB AG': 'Deutsche Bank',

    # Wells Fargo variations
    'Wells Fargo & Company': 'Wells Fargo',
    'Wells Fargo & Co.': 'Wells Fargo',
    'Wells Fargo & Co': 'Wells Fargo',
    'Wells Fargo Bank': 'Wells Fargo',

    # UBS variations
    'UBS AG': 'UBS',
    'UBS Group AG': 'UBS',
    'Union Bank of Switzerland': 'UBS',

    # Credit Suisse variations
    'Credit Suisse Group AG': 'Credit Suisse',
    'Credit Suisse AG': 'Credit Suisse',
    'Credit Suisse First Boston': 'Credit Suisse',
    'CSFB': 'Credit Suisse',

    # Barclays variations
    'Barclays PLC': 'Barclays',
    'Barclays plc': 'Barclays',
    'Barclays Bank': 'Barclays',
    'Barclays Capital': 'Barclays',

    # HSBC variations
    'HSBC Holdings plc': 'HSBC',
    'HSBC Holdings': 'HSBC',
    'HSBC Bank': 'HSBC',
    'Hongkong and Shanghai Banking Corporation': 'HSBC',

    # Wachovia variations
    'Wachovia Corporation': 'Wachovia',
    'Wachovia Corp.': 'Wachovia',
    'Wachovia Bank': 'Wachovia',

    # Washington Mutual variations
    'Washington Mutual Inc.': 'Washington Mutual',
    'Washington Mutual Inc': 'Washington Mutual',
    'WaMu': 'Washington Mutual',
    'Washington Mutual Bank': 'Washington Mutual',

    # Freddie Mac variations
    'Federal Home Loan Mortgage Corporation': 'Freddie Mac',
    'Federal Home Loan Mortgage Corp.': 'Freddie Mac',
    'FHLMC': 'Freddie Mac',

    # Fannie Mae variations
    'Federal National Mortgage Association': 'Fannie Mae',
    'Federal National Mortgage Assn.': 'Fannie Mae',
    'FNMA': 'Fannie Mae',

    # Regulators/Government
    'Securities and Exchange Commission': 'SEC',
    'U.S. Securities and Exchange Commission': 'SEC',
    'Federal Reserve': 'Fed',
    'Federal Reserve System': 'Fed',
    'Federal Reserve Bank': 'Fed',
    'The Federal Reserve': 'Fed',
    'U.S. Federal Reserve': 'Fed',
    'Federal Deposit Insurance Corporation': 'FDIC',
    'U.S. Treasury': 'Treasury',
    'Department of the Treasury': 'Treasury',
    'U.S. Department of the Treasury': 'Treasury',
}


def get_canonical_name(entity_name: str) -> str:
    """
    Return canonical name for an entity

    Args:
        entity_name: Original entity name (may be an alias)

    Returns:
        Canonical name if alias found, otherwise original name

    Examples:
        >>> get_canonical_name("American International Group")
        'AIG'

        >>> get_canonical_name("JPMorgan Chase")
        'JPMorgan'

        >>> get_canonical_name("Unknown Company")
        'Unknown Company'
    """
    if not entity_name:
        return entity_name

    # Direct lookup
    if entity_name in ENTITY_ALIASES:
        return ENTITY_ALIASES[entity_name]

    # Case-insensitive lookup
    entity_lower = entity_name.lower()
    for alias, canonical in ENTITY_ALIASES.items():
        if alias.lower() == entity_lower:
            return canonical

    # No alias found - return original
    return entity_name


def get_all_aliases(canonical_name: str) -> list:
    """
    Get all known aliases for a canonical entity name

    Args:
        canonical_name: Canonical entity name

    Returns:
        List of all aliases that map to this canonical name

    Example:
        >>> get_all_aliases("AIG")
        ['American International Group', 'American International Group Inc.', ...]
    """
    aliases = [canonical_name]  # Include canonical name itself

    for alias, canonical in ENTITY_ALIASES.items():
        if canonical == canonical_name:
            aliases.append(alias)

    return aliases


def get_deduplication_stats() -> dict:
    """
    Get statistics about alias mappings

    Returns:
        Dictionary with counts and examples
    """
    # Count unique canonical names
    canonical_names = set(ENTITY_ALIASES.values())

    # Group by canonical name
    grouped = {}
    for alias, canonical in ENTITY_ALIASES.items():
        if canonical not in grouped:
            grouped[canonical] = []
        grouped[canonical].append(alias)

    # Find entities with most aliases
    most_aliases = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

    return {
        'total_aliases': len(ENTITY_ALIASES),
        'unique_entities': len(canonical_names),
        'avg_aliases_per_entity': len(ENTITY_ALIASES) / len(canonical_names),
        'top_5_aliased': [
            {
                'canonical': name,
                'alias_count': len(aliases),
                'aliases': aliases[:3]  # Show first 3
            }
            for name, aliases in most_aliases[:5]
        ]
    }


if __name__ == '__main__':
    # Test and show statistics
    print("Entity Alias Resolution System")
    print("=" * 70)
    print()

    # Show statistics
    stats = get_deduplication_stats()
    print(f"Total alias mappings: {stats['total_aliases']}")
    print(f"Unique canonical entities: {stats['unique_entities']}")
    print(f"Average aliases per entity: {stats['avg_aliases_per_entity']:.1f}")
    print()

    print("Top 5 entities with most aliases:")
    for item in stats['top_5_aliased']:
        print(f"  {item['canonical']}: {item['alias_count']} aliases")
        for alias in item['aliases']:
            print(f"    - {alias}")
    print()

    # Test examples
    print("Example resolutions:")
    test_cases = [
        'American International Group',
        'JPMorgan Chase',
        'BofA',
        'Goldman Sachs Group Inc.',
        'Unknown Company'
    ]

    for test in test_cases:
        canonical = get_canonical_name(test)
        symbol = "→" if canonical != test else "="
        print(f"  {test:40} {symbol} {canonical}")
