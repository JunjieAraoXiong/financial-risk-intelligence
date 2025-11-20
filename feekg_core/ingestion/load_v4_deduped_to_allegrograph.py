#!/usr/bin/env python3
"""
Load v4 Deduplicated Data to AllegroGraph

Loads lehman_v4_deduped.json (with entity deduplication) to AllegroGraph.
Replaces existing data to eliminate duplicate entities.

Usage:
    python ingestion/load_v4_deduped_to_allegrograph.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.load_capital_iq_to_allegrograph import AllegroGraphRDFLoader, load_file_to_allegrograph


def main():
    print("\n" + "=" * 70)
    print("  Loading v4 Deduplicated Data to AllegroGraph")
    print("=" * 70)

    # Initialize loader
    loader = AllegroGraphRDFLoader()

    # Check current state
    print(f"\nConfiguration:")
    print(f"  Repository: {loader.catalog}/{loader.repo}")
    print(f"  URL: {loader.base_url}/catalogs/{loader.catalog}/repositories/{loader.repo}")

    current_count = loader.get_triple_count()
    print(f"  Current triples: {current_count}")

    # Clear existing data
    print(f"\nClearing existing data...")
    loader.clear_repository()
    print(f"   ✅ Repository cleared")

    # Load v4 deduplicated data
    v4_file = 'data/capital_iq_processed/lehman_v4_deduped.json'

    if not os.path.exists(v4_file):
        print(f"❌ Error: File not found: {v4_file}")
        print(f"   Please run: python ingestion/process_capital_iq_v4.py")
        return

    print(f"\n" + "=" * 70)
    print(f"Loading: {os.path.basename(v4_file)} (Deduplicated)")
    print("=" * 70)

    # Load with evolution computation
    entity_count, event_count, link_count = load_file_to_allegrograph(
        loader,
        v4_file,
        compute_evolution=True
    )

    # Final statistics
    final_count = loader.get_triple_count()

    print(f"\n" + "=" * 70)
    print(f"  Loading Complete")
    print("=" * 70)
    print(f"\nFinal Statistics:")
    print(f"  • Entities: {entity_count} (deduplicated)")
    print(f"  • Events: {event_count}")
    print(f"  • Evolution links: {link_count}")
    print(f"  • Total triples: {final_count:,}")
    print(f"\n✅ Graph now has consolidated entities:")
    print(f"   - Single 'AIG' node (not 'AIG' + 'American International Group')")
    print(f"   - Single 'Bank of America' node (not 'BofA' + 'Bank of America')")
    print(f"   - Single 'JPMorgan' node (not 'JPMorgan' + 'JP Morgan')")
    print(f"   - Single 'Citigroup' node (not 'Citi' + 'Citigroup')")
    print(f"   - And more...")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
