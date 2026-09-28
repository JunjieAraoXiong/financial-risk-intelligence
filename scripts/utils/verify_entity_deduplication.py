#!/usr/bin/env python3
"""
Entity Deduplication Verification Script

Compares entity counts and references before/after deduplication:
- v3 (with duplicates): AIG + American International Group = 2 nodes
- v4 (deduplicated): AIG only = 1 node

Usage:
    python scripts/verify_entity_deduplication.py
"""

import json
import os
import sys
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.config.entity_aliases import get_canonical_name, ENTITY_ALIASES


def load_json(filepath: str) -> Dict:
    """Load JSON file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return None

    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_entities(data: Dict, version: str) -> Dict:
    """Analyze entity usage in dataset"""
    if not data:
        return None

    entities = data.get('entities', [])
    events = data.get('events', [])

    # Count entity references in events
    entity_references = defaultdict(int)
    for event in events:
        event_entities = event.get('entities', [])
        for entity_name in event_entities:
            entity_references[entity_name] += 1

    # Group entities by canonical name
    canonical_groups = defaultdict(list)
    for entity in entities:
        entity_name = entity['name']
        canonical = get_canonical_name(entity_name)
        canonical_groups[canonical].append(entity_name)

    # Find duplicates (entities with same canonical name)
    duplicates = {canonical: names for canonical, names in canonical_groups.items() if len(names) > 1}

    return {
        'version': version,
        'total_entities': len(entities),
        'total_events': len(events),
        'entity_references': dict(entity_references),
        'canonical_groups': dict(canonical_groups),
        'duplicates': duplicates,
        'duplicate_count': len(duplicates)
    }


def compare_versions(v3_data: Dict, v4_data: Dict):
    """Compare v3 vs v4 entity deduplication"""
    print("\n" + "=" * 80)
    print("  Entity Deduplication Verification")
    print("=" * 80)

    if not v3_data or not v4_data:
        print("❌ Missing data files. Please process both v3 and v4 first.")
        return

    print(f"\nDataset Overview:")
    print(f"  v3 (with duplicates):    {v3_data['total_entities']} entities, {v3_data['total_events']} events")
    print(f"  v4 (deduplicated):       {v4_data['total_entities']} entities, {v4_data['total_events']} events")
    print(f"  Entities removed:        {v3_data['total_entities'] - v4_data['total_entities']}")

    # Show duplicates found in v3
    if v3_data['duplicates']:
        print(f"\n🔍 Duplicate Entities Found in v3 ({len(v3_data['duplicates'])} groups):")
        for canonical, aliases in sorted(v3_data['duplicates'].items()):
            print(f"\n  {canonical}:")
            for alias in aliases:
                ref_count = v3_data['entity_references'].get(alias, 0)
                print(f"    • {alias} ({ref_count} references)")

    # Verify v4 has no duplicates
    print(f"\n✅ Deduplication Status:")
    if v4_data['duplicate_count'] == 0:
        print(f"  v4 has NO duplicate entities (all aliases resolved to canonical names)")
    else:
        print(f"  ⚠️  v4 still has {v4_data['duplicate_count']} duplicate groups")
        for canonical, aliases in v4_data['duplicates'].items():
            print(f"    • {canonical}: {', '.join(aliases)}")

    # Show entity consolidation examples
    print(f"\n📊 Entity Consolidation Examples:")
    example_entities = ['AIG', 'JPMorgan', 'Bank of America', 'Lehman Brothers']

    for canonical in example_entities:
        v3_names = v3_data['canonical_groups'].get(canonical, [])
        v4_names = v4_data['canonical_groups'].get(canonical, [])

        v3_refs = sum(v3_data['entity_references'].get(name, 0) for name in v3_names)
        v4_refs = sum(v4_data['entity_references'].get(name, 0) for name in v4_names)

        print(f"\n  {canonical}:")
        print(f"    v3: {len(v3_names)} variant(s) → {v3_refs} total references")
        if v3_names:
            for name in v3_names:
                refs = v3_data['entity_references'].get(name, 0)
                print(f"      • {name} ({refs} refs)")

        print(f"    v4: {len(v4_names)} variant(s) → {v4_refs} total references")
        if v4_names:
            for name in v4_names:
                refs = v4_data['entity_references'].get(name, 0)
                print(f"      • {name} ({refs} refs)")

        if v3_refs == v4_refs and len(v4_names) == 1:
            print(f"    ✅ Consolidated successfully")

    # Show overall statistics
    print(f"\n📈 Overall Statistics:")
    v3_total_refs = sum(v3_data['entity_references'].values())
    v4_total_refs = sum(v4_data['entity_references'].values())

    print(f"  Total entity references:")
    print(f"    v3: {v3_total_refs}")
    print(f"    v4: {v4_total_refs}")
    print(f"    Difference: {v3_total_refs - v4_total_refs} (should be ~0 if no data loss)")

    # Quality metrics
    print(f"\n✅ Quality Metrics:")
    print(f"  Entities reduced: {v3_data['total_entities']} → {v4_data['total_entities']} ({((v3_data['total_entities'] - v4_data['total_entities']) / v3_data['total_entities'] * 100):.1f}% reduction)")
    print(f"  Reference integrity: {'✅ Preserved' if abs(v3_total_refs - v4_total_refs) < 10 else '⚠️  May have changed'}")
    print(f"  Duplicate groups eliminated: {v3_data['duplicate_count']} → {v4_data['duplicate_count']}")

    print("\n" + "=" * 80 + "\n")


def main():
    # Paths to data files
    v3_file = 'data/capital_iq_processed/lehman_v3_traced.json'
    v4_file = 'data/capital_iq_processed/lehman_v4_deduped.json'

    # Load data
    print("Loading datasets...")
    v3_json = load_json(v3_file)
    v4_json = load_json(v4_file)

    # Analyze
    v3_analysis = analyze_entities(v3_json, 'v3')
    v4_analysis = analyze_entities(v4_json, 'v4')

    # Compare
    compare_versions(v3_analysis, v4_analysis)

    # Save analysis report
    report = {
        'v3_analysis': v3_analysis,
        'v4_analysis': v4_analysis,
        'summary': {
            'entities_removed': v3_analysis['total_entities'] - v4_analysis['total_entities'] if v3_analysis and v4_analysis else 0,
            'duplicate_groups_eliminated': v3_analysis['duplicate_count'] - v4_analysis['duplicate_count'] if v3_analysis and v4_analysis else 0,
            'deduplication_successful': v4_analysis['duplicate_count'] == 0 if v4_analysis else False
        }
    }

    report_file = 'results/entity_deduplication_report.json'
    os.makedirs('results', exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📄 Detailed report saved to: {report_file}")


if __name__ == '__main__':
    main()
