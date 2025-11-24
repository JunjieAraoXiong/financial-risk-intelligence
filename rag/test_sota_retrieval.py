#!/usr/bin/env python3
"""
Test SOTA RAG Retrieval Improvements

Tests:
1. Multi-query retrieval with HyDE
2. Agent-specific queries
3. Query diversity across market regimes
4. Source diversity in results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import get_context_multi_query, get_agent_context
from rag.query_generator import QueryGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_query_generation():
    """Test that query generation produces diverse queries."""
    print("\n" + "="*60)
    print("TEST 1: Query Generation Diversity")
    print("="*60)

    # Test different market regimes
    test_cases = [
        ("January 2008", 0.10, 1.0, "normal"),
        ("July 2008", 0.35, 0.8, "stress"),
        ("September 2008", 0.80, 0.30, "crisis"),
    ]

    for date, vol, liq, regime in test_cases:
        print(f"\n--- {regime.upper()} regime ({date}, vol={vol}, liq={liq}) ---")
        queries = QueryGenerator.generate_market_queries(date, vol, liq, num_queries=3)
        for i, q in enumerate(queries):
            print(f"  Query {i+1}: {q}")

        # Test HyDE
        hyde = QueryGenerator.generate_hyde_document(date, vol, liq)
        print(f"  HyDE doc (first 100 chars): {hyde[:100]}...")


def test_multi_query_retrieval():
    """Test multi-query retrieval produces diverse results."""
    print("\n" + "="*60)
    print("TEST 2: Multi-Query Retrieval")
    print("="*60)

    # Test in crisis regime (should produce most diverse results)
    date = "September 2008"
    volatility = 0.80
    liquidity_factor = 0.30

    print(f"\nQuerying for: {date} (crisis)")
    print(f"Volatility: {volatility}, Liquidity Factor: {liquidity_factor}")

    results = get_context_multi_query(
        date=date,
        volatility=volatility,
        liquidity_factor=liquidity_factor,
        k=5,
        use_hyde=True
    )

    print(f"\nRetrieved {len(results)} chunks:")
    sources_seen = set()
    for i, chunk in enumerate(results):
        # Extract source from formatted chunk
        source_line = chunk.split('\n')[0] if chunk else ""
        print(f"\n  Chunk {i+1}: {source_line}")
        print(f"    Content preview: {chunk[len(source_line)+1:150]}...")

        # Track source diversity
        if 'JPM' in source_line:
            sources_seen.add('JPM')
        elif 'BIS' in source_line:
            sources_seen.add('BIS')
        elif 'FT' in source_line:
            sources_seen.add('FT')
        elif 'Financial' in source_line or 'FCIC' in source_line:
            sources_seen.add('FCIC')

    print(f"\nSource diversity: {len(sources_seen)} different sources: {sources_seen}")


def test_agent_specific_queries():
    """Test that different agents get different results."""
    print("\n" + "="*60)
    print("TEST 3: Agent-Specific Queries")
    print("="*60)

    date = "September 2008"
    volatility = 0.80

    # Test two different bank scenarios
    scenarios = [
        {
            "name": "Bank_0",
            "capital": 100.0,
            "liquidity": 0.20,
            "risk_score": 0.1,
            "desc": "Healthy bank"
        },
        {
            "name": "Bank_5",
            "capital": 40.0,
            "liquidity": 0.05,
            "risk_score": 0.8,
            "desc": "Stressed bank"
        }
    ]

    results_by_bank = {}

    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ({scenario['desc']}) ---")
        print(f"  Capital: {scenario['capital']}B, Liquidity: {scenario['liquidity']}, Risk: {scenario['risk_score']}")

        results = get_agent_context(
            bank_name=scenario['name'],
            date=date,
            capital=scenario['capital'],
            liquidity=scenario['liquidity'],
            risk_score=scenario['risk_score'],
            volatility=volatility,
            k=3
        )

        results_by_bank[scenario['name']] = results

        print(f"  Retrieved {len(results)} chunks:")
        for i, chunk in enumerate(results):
            source_line = chunk.split('\n')[0] if chunk else ""
            preview = chunk[len(source_line)+1:100] if len(chunk) > len(source_line)+1 else ""
            print(f"    {i+1}. {source_line}")
            print(f"       {preview}...")

    # Check if results are different
    if results_by_bank['Bank_0'] and results_by_bank['Bank_5']:
        content_0 = set(r[:100] for r in results_by_bank['Bank_0'])
        content_5 = set(r[:100] for r in results_by_bank['Bank_5'])
        overlap = content_0.intersection(content_5)
        print(f"\nResult overlap: {len(overlap)}/{min(len(content_0), len(content_5))} chunks")
        if len(overlap) < min(len(content_0), len(content_5)):
            print("✓ Agents receiving DIFFERENT context (as expected)")
        else:
            print("⚠ Agents receiving SAME context (investigate)")


def test_regime_comparison():
    """Test that different market regimes produce different results."""
    print("\n" + "="*60)
    print("TEST 4: Market Regime Comparison")
    print("="*60)

    regimes = [
        ("January 2008", 0.10, 1.0, "NORMAL"),
        ("September 2008", 0.80, 0.30, "CRISIS"),
    ]

    results_by_regime = {}

    for date, vol, liq, label in regimes:
        print(f"\n--- {label} ({date}) ---")
        results = get_context_multi_query(date, vol, liq, k=3, use_hyde=True)
        results_by_regime[label] = results

        print(f"  Retrieved {len(results)} chunks")
        for i, chunk in enumerate(results):
            source_line = chunk.split('\n')[0] if chunk else ""
            print(f"    {i+1}. {source_line}")

    # Compare results
    if results_by_regime.get('NORMAL') and results_by_regime.get('CRISIS'):
        normal_content = set(r[:100] for r in results_by_regime['NORMAL'])
        crisis_content = set(r[:100] for r in results_by_regime['CRISIS'])
        overlap = normal_content.intersection(crisis_content)
        print(f"\nOverlap between regimes: {len(overlap)}/{min(len(normal_content), len(crisis_content))}")
        if len(overlap) == 0:
            print("✓ Different regimes produce DIFFERENT results (as expected)")
        else:
            print(f"  Some overlap detected ({len(overlap)} chunks)")


def main():
    print("="*60)
    print("  SOTA RAG Retrieval Test Suite")
    print("="*60)

    try:
        test_query_generation()
        test_multi_query_retrieval()
        test_agent_specific_queries()
        test_regime_comparison()

        print("\n" + "="*60)
        print("  All tests completed!")
        print("="*60)
        print("\nKey improvements implemented:")
        print("  1. Dynamic query generation by market regime")
        print("  2. Multi-query retrieval (3+ queries per request)")
        print("  3. HyDE (Hypothetical Document Embeddings)")
        print("  4. Agent-specific queries based on bank state")
        print("  5. Source diversity (JPM/BIS/FT/FCIC)")
        print("  6. Deduplication across queries")
        print("  7. Cross-encoder reranking")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
