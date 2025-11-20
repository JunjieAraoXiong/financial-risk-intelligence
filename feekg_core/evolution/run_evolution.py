"""
Run event evolution analysis on Evergrande data
Updates Neo4j with improved evolution links using 6 methods
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feekg_core.evolution.methods import compute_all_evolution_links
from shared.config.graph_backend import get_connection


def run_evolution_analysis(json_path='data/evergrande_crisis.json',
                           threshold=0.2,
                           update_db=True):
    """
    Run evolution analysis and optionally update database

    Args:
        json_path: Path to Evergrande data JSON
        threshold: Minimum score for evolution link (default 0.2 from paper)
        update_db: Whether to update Neo4j with new links

    Returns:
        List of evolution links with scores
    """

    print("=" * 70)
    print("FE-EKG Stage 4: Event Evolution Analysis")
    print("=" * 70)
    print(f"\n📊 Analyzing: {json_path}")
    print(f"📏 Threshold: {threshold} (from paper)")

    # Load data
    print("\n1️⃣  Loading Evergrande data...")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        events = data['events']
        entities = data['entities']

        print(f"   ✅ Loaded {len(events)} events")
        print(f"   ✅ Loaded {len(entities)} entities")
    except Exception as e:
        print(f"   ❌ Failed to load data: {e}")
        return []

    # Compute evolution links
    print("\n2️⃣  Computing evolution links using 6 methods...")
    print("   Methods:")
    print("      1. Temporal Correlation (TCDI)")
    print("      2. Entity Overlap")
    print("      3. Semantic Similarity")
    print("      4. Topic Relevance")
    print("      5. Event Type Causality")
    print("      6. Emotional Consistency")

    try:
        links = compute_all_evolution_links(events, entities, threshold=threshold)
        print(f"\n   ✅ Computed {len(links)} evolution links (score ≥ {threshold})")
    except Exception as e:
        print(f"   ❌ Computation failed: {e}")
        return []

    # Analyze results
    print("\n3️⃣  Analyzing results...")

    if not links:
        print("   ⚠️  No evolution links found above threshold")
        return []

    # Statistics
    scores = [link['score'] for link in links]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)

    print(f"   📊 Score statistics:")
    print(f"      Average: {avg_score:.3f}")
    print(f"      Maximum: {max_score:.3f}")
    print(f"      Minimum: {min_score:.3f}")

    # Component contributions
    print(f"\n   📊 Average component scores:")
    component_sums = {}
    for link in links:
        for comp, score in link['components'].items():
            component_sums[comp] = component_sums.get(comp, 0) + score

    for comp, total in sorted(component_sums.items(), key=lambda x: x[1], reverse=True):
        avg = total / len(links)
        print(f"      {comp}: {avg:.3f}")

    # Top evolution paths
    print(f"\n   🔗 Top 10 evolution links:")
    top_links = sorted(links, key=lambda x: x['score'], reverse=True)[:10]

    for i, link in enumerate(top_links, 1):
        print(f"      {i}. {link['from_type']} → {link['to_type']}")
        print(f"         ({link['from_date']} → {link['to_date']}, score: {link['score']:.3f})")

    # Update database if requested
    if update_db:
        print("\n4️⃣  Updating Neo4j database...")
        try:
            backend = get_connection()
            print("   ✅ Connected to Neo4j")

            # First, remove old simple temporal links
            print("   🗑️  Removing old temporal-only links...")
            remove_query = """
            MATCH ()-[r:EVOLVES_TO]->()
            WHERE r.type = 'temporal'
            DELETE r
            """
            backend.execute_query(remove_query)
            print("   ✅ Old links removed")

            # Add new enhanced links
            print("   ➕ Adding enhanced evolution links...")
            added = 0

            for link in links:
                query = """
                MATCH (e1:Event {eventId: $from})
                MATCH (e2:Event {eventId: $to})
                MERGE (e1)-[r:EVOLVES_TO]->(e2)
                SET r.score = $score,
                    r.temporal = $temporal,
                    r.entity_overlap = $entity_overlap,
                    r.semantic = $semantic,
                    r.topic = $topic,
                    r.causality = $causality,
                    r.emotional = $emotional,
                    r.type = 'enhanced'
                """

                params = {
                    'from': link['from'],
                    'to': link['to'],
                    'score': link['score'],
                    'temporal': link['components']['temporal'],
                    'entity_overlap': link['components']['entity_overlap'],
                    'semantic': link['components']['semantic'],
                    'topic': link['components']['topic'],
                    'causality': link['components']['causality'],
                    'emotional': link['components']['emotional'],
                }

                backend.execute_query(query, params)
                added += 1

            print(f"   ✅ Added {added} enhanced evolution links")

            # Verify
            verify_query = """
            MATCH ()-[r:EVOLVES_TO {type: 'enhanced'}]->()
            RETURN count(r) as count, avg(r.score) as avg_score
            """
            result = backend.execute_query(verify_query)
            if result:
                count = result[0]['count']
                avg = result[0]['avg_score']
                print(f"   ✅ Verification: {count} links, avg score: {avg:.3f}")

            backend.close()
            print("   🔒 Connection closed")

        except Exception as e:
            print(f"   ❌ Database update failed: {e}")

    # Save results to file
    print("\n5️⃣  Saving results...")
    output_path = 'results/evolution_links.json'
    os.makedirs('results', exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'threshold': threshold,
                    'total_links': len(links),
                    'avg_score': avg_score,
                    'max_score': max_score,
                    'min_score': min_score,
                },
                'links': links
            }, f, indent=2)

        print(f"   ✅ Saved to {output_path}")
    except Exception as e:
        print(f"   ⚠️  Failed to save: {e}")

    print("\n" + "=" * 70)
    print("✅ Evolution Analysis Complete!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   - {len(links)} evolution links computed")
    print(f"   - Average score: {avg_score:.3f}")
    print(f"   - 6 methods applied (temporal, entity, semantic, topic, causal, emotional)")

    if update_db:
        print(f"\n🌐 View in Neo4j Browser:")
        print(f"   URL: http://localhost:7474")
        print(f"\n   Query to see enhanced links:")
        print(f"   MATCH (e1:Event)-[r:EVOLVES_TO]->(e2:Event)")
        print(f"   WHERE r.type = 'enhanced'")
        print(f"   RETURN e1.type, e2.type, r.score")
        print(f"   ORDER BY r.score DESC")

    print()

    return links


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run event evolution analysis')
    parser.add_argument('--threshold', type=float, default=0.2,
                       help='Minimum evolution score (default: 0.2)')
    parser.add_argument('--no-update', action='store_true',
                       help='Do not update database (analysis only)')

    args = parser.parse_args()

    links = run_evolution_analysis(
        threshold=args.threshold,
        update_db=not args.no_update
    )

    sys.exit(0 if links else 1)
