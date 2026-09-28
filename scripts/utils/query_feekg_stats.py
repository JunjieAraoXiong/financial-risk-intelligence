#!/usr/bin/env python3
"""
Query FEEKG Statistics from AllegroGraph

Shows counts of entities, events, and sample data
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
base_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/').rstrip('/')
user = os.getenv('AG_USER')
password = os.getenv('AG_PASS')
catalog = os.getenv('AG_CATALOG', 'mycatalog')
repo = os.getenv('AG_REPO', 'FEEKG')

repo_url = f"{base_url}/catalogs/{catalog}/repositories/{repo}"
auth = (user, password)

def run_query(query):
    """Run SPARQL query"""
    try:
        response = requests.get(
            repo_url,
            params={'query': query},
            headers={'Accept': 'application/sparql-results+json'},
            auth=auth,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Query failed: {e}")
        return None

print("=" * 80)
print("FEEKG AllegroGraph Statistics")
print("=" * 80)
print(f"Repository: {catalog}/{repo}")
print()

# Count entities
print("1. Counting entities...")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
SELECT (COUNT(DISTINCT ?entity) as ?count)
WHERE { ?entity a feekg:Entity . }
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    print(f"   ✓ Total entities: {count}")

# Count events
print("\n2. Counting events...")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
SELECT (COUNT(DISTINCT ?event) as ?count)
WHERE { ?event a feekg:Event . }
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    print(f"   ✓ Total events: {count}")

# Count event types
print("\n3. Event types distribution...")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?type (COUNT(?event) as ?count)
WHERE {
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
}
GROUP BY ?type
ORDER BY DESC(?count)
LIMIT 10
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    print(f"   ✓ Top event types:")
    for binding in result['results']['bindings']:
        event_type = binding['type']['value']
        count = binding['count']['value']
        print(f"      - {event_type}: {count}")

# Count events by severity
print("\n4. Events by severity...")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?severity (COUNT(?event) as ?count)
WHERE {
    ?event a feekg:Event .
    ?event feekg:severity ?severity .
}
GROUP BY ?severity
ORDER BY DESC(?count)
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    print(f"   ✓ Severity distribution:")
    for binding in result['results']['bindings']:
        severity = binding['severity']['value']
        count = binding['count']['value']
        print(f"      - {severity}: {count}")

# Sample events
print("\n5. Sample events...")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?event ?date ?type ?label
WHERE {
    ?event a feekg:Event .
    ?event feekg:date ?date .
    ?event feekg:eventType ?type .
    ?event rdfs:label ?label .
}
ORDER BY ?date
LIMIT 5
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    print(f"   ✓ First 5 events (by date):")
    for i, binding in enumerate(result['results']['bindings'], 1):
        date = binding['date']['value']
        event_type = binding['type']['value']
        label = binding['label']['value'][:60]
        print(f"      {i}. [{date}] {event_type}: {label}")

print()
print("=" * 80)
print("✅ Query complete!")
print()
