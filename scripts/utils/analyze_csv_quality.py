#!/usr/bin/env python3
"""
Capital IQ CSV Data Quality Analyzer

Analyzes the raw Capital IQ CSV to understand:
1. How many unique event types exist
2. Which types are currently unmapped
3. Distribution of events across types
4. Recommendations for improving classification

Usage:
    ./venv/bin/python scripts/analyze_csv_quality.py
"""

import pandas as pd
import sys
import os
from collections import Counter
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from feekg_core.ingestion.process_capital_iq_v2 import CapitalIQProcessorV2


def analyze_raw_csv(csv_file):
    """Analyze raw Capital IQ CSV for data quality"""

    print("=" * 80)
    print("Capital IQ Data Quality Analysis")
    print("=" * 80)
    print(f"\nAnalyzing: {csv_file}")
    print()

    # Load CSV
    print("1. Loading CSV...")
    try:
        df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip', low_memory=False)
    except:
        df = pd.read_csv(csv_file, encoding='latin-1', on_bad_lines='skip', low_memory=False)

    # Normalize columns
    df.columns = df.columns.str.lower().str.strip()

    print(f"   ✓ Loaded {len(df):,} total events")
    print()

    # Convert date
    df['announcedate'] = pd.to_datetime(df['announcedate'], errors='coerce')

    # Filter to crisis period
    print("2. Filtering to crisis period (2007-2009)...")
    crisis_df = df[(df['announcedate'] >= '2007-01-01') &
                   (df['announcedate'] <= '2009-12-31')].copy()
    print(f"   ✓ {len(crisis_df):,} events in 2007-2009")
    print()

    # Analyze Capital IQ event types
    print("3. Analyzing Capital IQ event types...")
    eventtype_counts = crisis_df['eventtype'].value_counts()

    print(f"   ✓ Found {len(eventtype_counts)} unique event types")
    print(f"\n   Top 20 Capital IQ Event Types:")
    print("   " + "-" * 76)
    for i, (etype, count) in enumerate(eventtype_counts.head(20).items(), 1):
        pct = (count / len(crisis_df)) * 100
        print(f"   {i:2}. {etype[:50]:50} {count:>6,} ({pct:5.1f}%)")
    print()

    # Test current processor
    print("4. Testing current classification logic...")
    processor = CapitalIQProcessorV2(csv_file)

    # Sample classifications
    sample_size = min(1000, len(crisis_df))
    sample_df = crisis_df.sample(sample_size, random_state=42)

    classified_types = []
    unknown_count = 0
    confidence_scores = []

    for _, row in sample_df.iterrows():
        classified_type = processor.classify_event_type(
            row.get('headline', ''),
            row.get('eventtype', '')
        )
        classified_types.append(classified_type)

        if classified_type == 'unknown':
            unknown_count += 1

    unknown_pct = (unknown_count / sample_size) * 100

    print(f"   ✓ Tested {sample_size:,} events")
    print(f"   ✓ Unknown events: {unknown_count:,} ({unknown_pct:.1f}%)")
    print()

    # Classification distribution
    print("5. Current classification distribution (sample):")
    classified_counter = Counter(classified_types)
    print("   " + "-" * 76)
    for etype, count in classified_counter.most_common(15):
        pct = (count / sample_size) * 100
        print(f"   {etype[:30]:30} {count:>6,} ({pct:5.1f}%)")
    print()

    # Find unmapped types
    print("6. Identifying unmapped Capital IQ types...")

    # Get all unknown events
    unmapped_types = {}
    for _, row in crisis_df.iterrows():
        headline = row.get('headline', '')
        ciq_type = row.get('eventtype', '')

        classified = processor.classify_event_type(headline, ciq_type)

        if classified == 'unknown' and pd.notna(ciq_type):
            if ciq_type not in unmapped_types:
                unmapped_types[ciq_type] = 0
            unmapped_types[ciq_type] += 1

    print(f"   ✓ Found {len(unmapped_types)} unmapped Capital IQ types")
    print(f"\n   Top 30 Unmapped Types (causing 'unknown' classification):")
    print("   " + "-" * 76)

    sorted_unmapped = sorted(unmapped_types.items(), key=lambda x: x[1], reverse=True)
    for i, (etype, count) in enumerate(sorted_unmapped[:30], 1):
        pct = (count / len(crisis_df)) * 100
        print(f"   {i:2}. {etype[:50]:50} {count:>6,} ({pct:5.1f}%)")
    print()

    # Generate recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    total_unknown = sum(unmapped_types.values())

    print(f"Current Status:")
    print(f"  • Total events (2007-2009): {len(crisis_df):,}")
    print(f"  • Estimated unknown events: ~{int(total_unknown):,} ({(total_unknown/len(crisis_df)*100):.1f}%)")
    print(f"  • Unmapped Capital IQ types: {len(unmapped_types)}")
    print()

    print(f"To reduce 'unknown' events to <1%:")
    print()
    print(f"1. Add mappings for top 30 unmapped types (covers {sum(c for _, c in sorted_unmapped[:30]):,} events)")
    print(f"   Priority types:")
    for etype, count in sorted_unmapped[:5]:
        print(f"      - '{etype}' → Suggest FE-EKG type")
    print()

    print(f"2. Use LLM classification for remaining {len(sorted_unmapped) - 30} long-tail types")
    print(f"   Cost estimate: ~$0.50 for {sum(c for _, c in sorted_unmapped[30:])} events")
    print()

    print(f"3. Add confidence scoring:")
    print(f"   - Pattern match: 95% confidence")
    print(f"   - Capital IQ mapping: 85% confidence")
    print(f"   - LLM classification: 75% confidence")
    print()

    # Export unmapped types for manual mapping
    output_file = 'data/unmapped_capital_iq_types.json'
    import json

    unmapped_data = {
        'generated_at': datetime.now().isoformat(),
        'total_events': len(crisis_df),
        'unmapped_count': total_unknown,
        'unmapped_types': [
            {
                'capital_iq_type': etype,
                'event_count': count,
                'percentage': round((count / len(crisis_df)) * 100, 2),
                'suggested_feekg_type': ''  # To be filled manually
            }
            for etype, count in sorted_unmapped
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(unmapped_data, f, indent=2)

    print(f"✅ Exported unmapped types to: {output_file}")
    print(f"   (Edit this file to add FE-EKG type mappings)")
    print()

    print("=" * 80)


def main():
    csv_file = 'data/capital_iq_raw/capital_iq_download.csv'

    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file not found: {csv_file}")
        sys.exit(1)

    analyze_raw_csv(csv_file)


if __name__ == '__main__':
    main()
