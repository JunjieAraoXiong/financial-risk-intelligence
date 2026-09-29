#!/usr/bin/env python3
"""
Demo: FEEKG Knowledge Graph Capabilities

Demonstrates what you can do with 74,012 triples including:
- Natural language-like queries
- CSV source tracing
- Event pattern analysis
- Entity relationship discovery
- Data quality verification

Usage:
    ./venv/bin/python scripts/demo_feekg_capabilities.py
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

# AllegroGraph connection
base_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/').rstrip('/')
catalog = os.getenv('AG_CATALOG', 'mycatalog')
repo = os.getenv('AG_REPO', 'FEEKG')
auth = (os.getenv('AG_USER'), os.getenv('AG_PASS'))

repo_url = f"{base_url}/catalogs/{catalog}/repositories/{repo}"


def run_query(query, description):
    """Run SPARQL query and display results"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print('='*70)

    try:
        response = requests.get(
            repo_url,
            params={'query': query},
            headers={'Accept': 'application/sparql-results+json'},
            auth=auth,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def demo_1_database_stats():
    """Demo 1: Database Statistics"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>

SELECT
    (COUNT(DISTINCT ?event) as ?eventCount)
    (COUNT(DISTINCT ?entity) as ?entityCount)
    (MIN(?date) as ?startDate)
    (MAX(?date) as ?endDate)
WHERE {
    ?event feekg:date ?date .
    OPTIONAL { ?event feekg:involves ?entity . }
}
"""

    result = run_query(query, "Demo 1: Database Overview")

    if result:
        binding = result['results']['bindings'][0]
        print(f"\n📊 FEEKG Knowledge Graph Statistics:")
        print(f"   • Events: {binding['eventCount']['value']}")
        print(f"   • Entities: {binding['entityCount']['value']}")
        print(f"   • Date Range: {binding['startDate']['value']} to {binding['endDate']['value']}")
        print(f"   • Total Triples: 74,012")


def demo_2_csv_traceability():
    """Demo 2: CSV Source Traceability"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?row ?capitalIqId ?originalType ?mappedType ?confidence
WHERE {
    ?event rdfs:label ?label .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:capitalIqId ?capitalIqId .
    ?event feekg:originalEventType ?originalType .
    ?event feekg:eventType ?mappedType .
    ?event feekg:classificationConfidence ?confidence .
}
ORDER BY ?row
LIMIT 5
"""

    result = run_query(query, "Demo 2: CSV Source Traceability (Sample)")

    if result:
        print(f"\n🔍 Every event traceable to exact CSV row:\n")
        for i, binding in enumerate(result['results']['bindings'], 1):
            label = binding['label']['value'][:55]
            row = binding['row']['value']
            cap_id = binding['capitalIqId']['value']
            orig_type = binding['originalType']['value'][:28]
            mapped = binding['mappedType']['value']
            conf = float(binding['confidence']['value'])

            print(f"{i}. {label}...")
            print(f"   CSV Row: {row} | Capital IQ ID: {cap_id}")
            print(f"   {orig_type} → {mapped} ({conf:.0%} confidence)")
            print()


def demo_3_legal_issues():
    """Demo 3: Find All Legal Issues (Like Natural Language Query)"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?date ?company ?row ?confidence
WHERE {
    ?event feekg:eventType "legal_issue" .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:actor ?company .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:classificationConfidence ?confidence .
}
ORDER BY ?date DESC
LIMIT 10
"""

    result = run_query(query, 'Demo 3: "What legal issues occurred?" (Natural Query)')

    if result:
        print(f"\n⚖️  Legal Issues with Source Tracing:\n")
        for i, binding in enumerate(result['results']['bindings'], 1):
            label = binding['label']['value'][:50]
            date = binding['date']['value']
            company = binding['company']['value'][:25]
            row = binding['row']['value']
            conf = float(binding['confidence']['value'])

            print(f"{i}. [{date}] {label}...")
            print(f"   Company: {company}")
            print(f"   Source: CSV row {row} | Confidence: {conf:.0%}")
            print()


def demo_4_event_timeline():
    """Demo 4: Event Timeline by Month"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>

SELECT (SUBSTR(?date, 1, 7) as ?month) (COUNT(?event) as ?count)
WHERE {
    ?event feekg:date ?date .
}
GROUP BY (SUBSTR(?date, 1, 7))
ORDER BY ?month
LIMIT 15
"""

    result = run_query(query, "Demo 4: Event Timeline (Crisis Hotspots)")

    if result:
        print(f"\n📅 Events by Month (look for crisis spikes):\n")

        max_count = max(int(b['count']['value']) for b in result['results']['bindings'])

        for binding in result['results']['bindings']:
            month = binding['month']['value']
            count = int(binding['count']['value'])

            # Simple bar chart
            bar_width = int((count / max_count) * 40)
            bar = '█' * bar_width

            print(f"{month}: {bar} {count:>4} events")


def demo_5_entity_network():
    """Demo 5: Entity Relationship Network"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?entity (COUNT(DISTINCT ?event) as ?eventCount)
WHERE {
    ?event feekg:involves ?ent .
    ?ent rdfs:label ?entity .
}
GROUP BY ?entity
ORDER BY DESC(?eventCount)
LIMIT 10
"""

    result = run_query(query, "Demo 5: Most Active Entities (Network Hubs)")

    if result:
        print(f"\n🏢 Entities by Event Count:\n")
        for i, binding in enumerate(result['results']['bindings'], 1):
            entity = binding['entity']['value']
            count = int(binding['eventCount']['value'])
            print(f"{i:2}. {entity:30} {count:>4} events")


def demo_6_classification_quality():
    """Demo 6: Classification Quality by Method"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?method
       (COUNT(?event) as ?count)
       (AVG(?confidence) as ?avgConfidence)
WHERE {
    ?event feekg:classificationMethod ?method .
    ?event feekg:classificationConfidence ?confidence .
}
GROUP BY ?method
ORDER BY DESC(?count)
"""

    result = run_query(query, "Demo 6: Data Quality Metrics")

    if result:
        print(f"\n📊 Classification Quality:\n")
        for binding in result['results']['bindings']:
            method = binding['method']['value']
            count = int(binding['count']['value'])
            avg_conf = float(binding['avgConfidence']['value'])

            print(f"   {method:20} {count:>4} events | {avg_conf:.1%} avg confidence")


def demo_7_high_risk_events():
    """Demo 7: High-Risk Events with Full Metadata"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?date ?type ?severity ?row ?confidence
WHERE {
    ?event feekg:severity "high" .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:eventType ?type .
    ?event feekg:severity ?severity .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:classificationConfidence ?confidence .
}
ORDER BY ?date
LIMIT 8
"""

    result = run_query(query, "Demo 7: High-Risk Events (For Risk Monitoring)")

    if result:
        print(f"\n⚠️  High-Severity Events:\n")
        for i, binding in enumerate(result['results']['bindings'], 1):
            label = binding['label']['value'][:50]
            date = binding['date']['value']
            event_type = binding['type']['value']
            row = binding['row']['value']
            conf = float(binding['confidence']['value'])

            print(f"{i}. [{date}] {label}...")
            print(f"   Type: {event_type} | CSV Row: {row} | Confidence: {conf:.0%}")
            print()


def demo_8_type_mapping_analysis():
    """Demo 8: Verify Type Mappings"""
    query = """
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?originalType ?mappedType (COUNT(?event) as ?count)
WHERE {
    ?event feekg:originalEventType ?originalType .
    ?event feekg:eventType ?mappedType .
}
GROUP BY ?originalType ?mappedType
ORDER BY DESC(?count)
LIMIT 10
"""

    result = run_query(query, "Demo 8: Type Mapping Verification")

    if result:
        print(f"\n🔄 Capital IQ → FE-EKG Type Mappings:\n")
        for i, binding in enumerate(result['results']['bindings'], 1):
            orig = binding['originalType']['value'][:30]
            mapped = binding['mappedType']['value']
            count = int(binding['count']['value'])

            print(f"{i:2}. {orig:30} → {mapped:20} ({count:>3} events)")


def main():
    print("\n" + "="*70)
    print(" FEEKG Knowledge Graph Capabilities Demo")
    print(" 74,012 triples | 4,398 events | 100% CSV traceability")
    print("="*70)

    demos = [
        demo_1_database_stats,
        demo_2_csv_traceability,
        demo_3_legal_issues,
        demo_4_event_timeline,
        demo_5_entity_network,
        demo_6_classification_quality,
        demo_7_high_risk_events,
        demo_8_type_mapping_analysis
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n❌ Error in {demo.__name__}: {e}")

        input("\nPress Enter for next demo...")

    print("\n" + "="*70)
    print(" Summary: What You Can Do")
    print("="*70)
    print("""
✅ Natural Language Queries (with AllegroGraph NLQ)
   - "What legal issues did Morgan Stanley face?"
   - "Show credit downgrades in September 2008"

✅ Complex SPARQL Analysis
   - Timeline analysis
   - Entity relationship networks
   - Risk pattern detection

✅ Full CSV Traceability
   - Every event → exact CSV row
   - Original vs mapped type comparison
   - Classification confidence scoring

✅ Data Quality Verification
   - Audit trail for compliance
   - Quality metrics by method
   - Source verification

Next Steps:
1. Set up AllegroGraph NLQ for natural language queries (~$0.20)
2. Build chatbot UI with CSV source viewer
3. Add graph visualizations (D3.js/Cytoscape.js)
4. Create risk analysis dashboard

See: FEEKG_CAPABILITIES.md for complete guide
""")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
