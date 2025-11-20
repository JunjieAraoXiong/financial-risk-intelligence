#!/usr/bin/env python3
"""
Load Lehman Brothers Case Study into FE-EKG

Loads processed Capital IQ data and runs event evolution analysis.

Usage:
    python ingestion/load_lehman.py
    python ingestion/load_lehman.py --input data/capital_iq_processed/lehman_case_study.json
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config.graph_backend import get_connection
from feekg_core.evolution.methods import compute_all_evolution_links


def load_lehman_case_study(input_file: str = 'data/capital_iq_processed/lehman_case_study.json'):
    """
    Load Lehman Brothers case study into Neo4j and run evolution analysis

    Args:
        input_file: Path to processed JSON file
    """

    print("\n" + "=" * 70)
    print("  Load Lehman Brothers Case Study into FE-EKG")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"\n❌ Error: File not found: {input_file}")
        print("\nPlease run the processing pipeline first:")
        print("  ./venv/bin/python ingestion/process_capital_iq.py \\")
        print("      --input data/capital_iq_raw/your_file.xlsx \\")
        print("      --filter lehman")
        sys.exit(1)

    # Load JSON data
    print(f"\n1. Loading data from: {input_file}")
    with open(input_file, 'r') as f:
        data = json.load(f)

    print(f"   ✅ Loaded {data['metadata']['events_count']} events")
    print(f"   ✅ Loaded {data['metadata']['entities_count']} entities")

    # Connect to backend
    print(f"\n2. Connecting to graph database...")
    try:
        backend = get_connection()
        print(f"   ✅ Connected to {backend.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n   Please start Neo4j:")
        print("   ./scripts/start_neo4j.sh")
        sys.exit(1)

    # Clear existing data
    print(f"\n3. Clearing existing data...")
    backend.clear()
    print("   ✅ Database cleared")

    # Load entities
    print(f"\n4. Loading {len(data['entities'])} entities...")
    entity_count = 0
    for entity in data['entities']:
        query = """
        MERGE (e:Entity {entityId: $entityId})
        SET e.name = $name,
            e.type = $type,
            e.createdAt = datetime()
        RETURN e.entityId as id
        """
        try:
            result = backend.execute_query(query, {
                'entityId': entity['entityId'],
                'name': entity['name'],
                'type': entity['type']
            })
            entity_count += 1
        except Exception as e:
            print(f"   ⚠️  Failed to create entity {entity['entityId']}: {e}")

    print(f"   ✅ Loaded {entity_count} entities")

    # Load events
    print(f"\n5. Loading {len(data['events'])} events...")
    event_count = 0

    # Build entity name to ID map for faster lookup
    entity_map = {e['name']: e['entityId'] for e in data['entities']}

    for event in data['events']:
        query = """
        MERGE (ev:Event {eventId: $eventId})
        SET ev.type = $type,
            ev.date = date($date),
            ev.headline = $headline,
            ev.description = $description,
            ev.source = $source,
            ev.actor = $actor,
            ev.severity = $severity,
            ev.sentiment = $sentiment,
            ev.createdAt = datetime()
        RETURN ev.eventId as id
        """
        try:
            result = backend.execute_query(query, {
                'eventId': event['eventId'],
                'type': event['type'],
                'date': event['date'],
                'headline': event['headline'],
                'description': event['description'],
                'source': event.get('source', 'Capital IQ'),
                'actor': event.get('actor', 'unknown'),
                'severity': event.get('severity', 'low'),  # Store severity from v2
                'sentiment': 0.0
            })
            event_count += 1

            # Link event to entities (optimized with entity_map)
            for entity_name in event['entities']:
                # Use entity_map for O(1) lookup instead of O(n) search
                entity_id = entity_map.get(entity_name)
                if entity_id:
                    link_query = """
                    MATCH (e:Entity {entityId: $entityId})
                    MATCH (ev:Event {eventId: $eventId})
                    MERGE (e)-[:INVOLVES]->(ev)
                    """
                    backend.execute_query(link_query, {
                        'entityId': entity_id,
                        'eventId': event['eventId']
                    })

        except Exception as e:
            print(f"   ⚠️  Failed to create event {event['eventId']}: {e}")

    print(f"   ✅ Loaded {event_count} events")

    # Run event evolution analysis
    print(f"\n6. Running event evolution analysis...")
    print("   Methods:")
    print("      1. Temporal Correlation (TCDI)")
    print("      2. Entity Overlap")
    print("      3. Semantic Similarity")
    print("      4. Topic Relevance")
    print("      5. Event Type Causality")
    print("      6. Emotional Consistency")

    try:
        links = compute_all_evolution_links(
            data['events'],
            data['entities'],
            threshold=0.2
        )
        print(f"\n   ✅ Computed {len(links)} evolution links (score ≥ 0.2)")
    except Exception as e:
        print(f"   ⚠️  Evolution computation failed: {e}")
        links = []

    # Store evolution links in Neo4j
    if links:
        print(f"\n   Storing evolution links in Neo4j...")
        link_count = 0
        for link in links:
            query = """
            MATCH (from:Event {eventId: $from})
            MATCH (to:Event {eventId: $to})
            MERGE (from)-[r:EVOLVES_TO]->(to)
            SET r.score = $score,
                r.method = $method,
                r.temporal = $temporal,
                r.entity = $entity,
                r.semantic = $semantic,
                r.topic = $topic,
                r.causality = $causality,
                r.emotional = $emotional
            """
            try:
                backend.execute_query(query, {
                    'from': link['from'],
                    'to': link['to'],
                    'score': link['score'],
                    'method': 'composite',
                    'temporal': link['components'].get('temporal', 0.0),
                    'entity': link['components'].get('entity', 0.0),
                    'semantic': link['components'].get('semantic', 0.0),
                    'topic': link['components'].get('topic', 0.0),
                    'causality': link['components'].get('causality', 0.0),
                    'emotional': link['components'].get('emotional', 0.0)
                })
                link_count += 1
            except Exception as e:
                print(f"   ⚠️  Failed to store link: {e}")

        print(f"   ✅ Stored {link_count} evolution links")

    # Create risks based on event type and severity
    print(f"\n7. Creating risk nodes...")

    # Define comprehensive event-to-risk mapping
    event_risk_mapping = {
        'bankruptcy': {
            'risk_type': 'credit_risk',
            'base_severity': 'critical',
            'base_likelihood': 0.95,
            'description': 'Credit default and bankruptcy contagion risk'
        },
        'government_intervention': {
            'risk_type': 'systemic_risk',
            'base_severity': 'critical',
            'base_likelihood': 0.90,
            'description': 'Systemic financial crisis requiring government intervention'
        },
        'credit_downgrade': {
            'risk_type': 'credit_risk',
            'base_severity': 'high',
            'base_likelihood': 0.80,
            'description': 'Credit quality deterioration and funding risk'
        },
        'earnings_loss': {
            'risk_type': 'financial_risk',
            'base_severity': 'high',
            'base_likelihood': 0.75,
            'description': 'Financial performance deterioration and solvency risk'
        },
        'restructuring': {
            'risk_type': 'operational_risk',
            'base_severity': 'high',
            'base_likelihood': 0.70,
            'description': 'Business restructuring and operational disruption risk'
        },
        'merger_acquisition': {
            'risk_type': 'counterparty_risk',
            'base_severity': 'medium',
            'base_likelihood': 0.65,
            'description': 'Acquisition integration and counterparty exposure risk'
        },
        'capital_raising': {
            'risk_type': 'liquidity_risk',
            'base_severity': 'medium',
            'base_likelihood': 0.70,
            'description': 'Liquidity stress and capital adequacy concerns'
        },
        'management_change': {
            'risk_type': 'operational_risk',
            'base_severity': 'medium',
            'base_likelihood': 0.60,
            'description': 'Management instability and governance risk'
        },
        'stock_movement': {
            'risk_type': 'market_risk',
            'base_severity': 'medium',
            'base_likelihood': 0.55,
            'description': 'Stock price volatility and shareholder value risk'
        },
        'legal_issue': {
            'risk_type': 'legal_risk',
            'base_severity': 'medium',
            'base_likelihood': 0.60,
            'description': 'Legal liability and regulatory compliance risk'
        },
        'strategic_partnership': {
            'risk_type': 'strategic_risk',
            'base_severity': 'low',
            'base_likelihood': 0.45,
            'description': 'Strategic alliance and partnership execution risk'
        },
        'earnings_announcement': {
            'risk_type': 'market_risk',
            'base_severity': 'low',
            'base_likelihood': 0.50,
            'description': 'Market volatility and investor sentiment risk'
        },
        'business_operations': {
            'risk_type': 'operational_risk',
            'base_severity': 'low',
            'base_likelihood': 0.40,
            'description': 'Business operations and execution risk'
        }
    }

    # Severity to likelihood adjustment
    severity_adjustment = {
        'critical': 0.0,   # No reduction for critical
        'high': -0.10,     # Reduce likelihood by 10%
        'medium': -0.20,   # Reduce likelihood by 20%
        'low': -0.30       # Reduce likelihood by 30%
    }

    risk_count = 0
    for event_data in data['events']:
        event_type = event_data['type']
        event_severity = event_data.get('severity', 'low')

        # Only create risks for events with defined risk mappings
        if event_type in event_risk_mapping:
            risk_id = f"risk_{event_data['eventId']}"
            risk_config = event_risk_mapping[event_type]

            # Use event severity from v2, fallback to mapping base severity
            severity = event_severity if event_severity in ['critical', 'high', 'medium', 'low'] else risk_config['base_severity']

            # Adjust likelihood based on actual event severity
            likelihood = max(0.1, min(1.0, risk_config['base_likelihood'] + severity_adjustment.get(severity, 0)))

            query = """
            MERGE (r:Risk {riskId: $riskId})
            SET r.riskType = $riskType,
                r.severity = $severity,
                r.likelihood = $likelihood,
                r.description = $description,
                r.createdAt = datetime()
            RETURN r.riskId as id
            """
            try:
                backend.execute_query(query, {
                    'riskId': risk_id,
                    'riskType': risk_config['risk_type'],
                    'severity': severity,
                    'likelihood': likelihood,
                    'description': f"{risk_config['description']}: {event_data['headline'][:100]}"
                })

                # Link risk to event
                link_query = """
                MATCH (ev:Event {eventId: $eventId})
                MATCH (r:Risk {riskId: $riskId})
                MERGE (ev)-[:TRIGGERS]->(r)
                """
                backend.execute_query(link_query, {
                    'eventId': event_data['eventId'],
                    'riskId': risk_id
                })
                risk_count += 1
            except Exception as e:
                print(f"   ⚠️  Failed to create risk: {e}")

    print(f"   ✅ Created {risk_count} risk nodes")

    # Get final statistics
    print(f"\n8. Getting statistics...")

    # Count nodes and relationships
    entity_count_query = "MATCH (e:Entity) RETURN count(e) as count"
    event_count_query = "MATCH (ev:Event) RETURN count(ev) as count"
    risk_count_query = "MATCH (r:Risk) RETURN count(r) as count"
    evolution_count_query = "MATCH ()-[r:EVOLVES_TO]->() RETURN count(r) as count"
    entity_event_count_query = "MATCH ()-[r:INVOLVES]->() RETURN count(r) as count"
    event_risk_count_query = "MATCH ()-[r:TRIGGERS]->() RETURN count(r) as count"

    entity_count_result = backend.execute_query(entity_count_query)
    event_count_result = backend.execute_query(event_count_query)
    risk_count_result = backend.execute_query(risk_count_query)
    evolution_count_result = backend.execute_query(evolution_count_query)
    entity_event_count_result = backend.execute_query(entity_event_count_query)
    event_risk_count_result = backend.execute_query(event_risk_count_query)

    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"\n✅ Lehman Brothers case study loaded successfully!")
    print(f"\nDatabase statistics:")
    print(f"  - Entities: {entity_count_result[0]['count'] if entity_count_result else 0}")
    print(f"  - Events: {event_count_result[0]['count'] if event_count_result else 0}")
    print(f"  - Risks: {risk_count_result[0]['count'] if risk_count_result else 0}")
    print(f"  - Evolution links: {evolution_count_result[0]['count'] if evolution_count_result else 0}")
    print(f"  - Entity-Event links: {entity_event_count_result[0]['count'] if entity_event_count_result else 0}")
    print(f"  - Event-Risk links: {event_risk_count_result[0]['count'] if event_risk_count_result else 0}")
    print(f"\nNext steps:")
    print(f"  1. Convert to RDF: ./venv/bin/python scripts/convert_lehman_to_rdf.py")
    print(f"  2. Query evolution: ./venv/bin/python scripts/query_lehman_sparql.py")
    print(f"  3. Generate visuals: ./venv/bin/python scripts/visualize_lehman.py")
    print("=" * 70 + "\n")

    # Close connection
    backend.close()


def main():
    parser = argparse.ArgumentParser(description='Load Lehman Brothers case study into FE-EKG')
    parser.add_argument('--input',
                       default='data/capital_iq_processed/lehman_case_study.json',
                       help='Input JSON file (default: lehman_case_study.json)')

    args = parser.parse_args()

    load_lehman_case_study(args.input)


if __name__ == '__main__':
    main()
