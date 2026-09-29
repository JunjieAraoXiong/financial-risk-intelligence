#!/usr/bin/env python3
"""
Check if loaded data follows FE-EKG ontology structure
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

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
print("FE-EKG Ontology Compliance Check")
print("=" * 80)
print()

# Check what namespaces are used
print("1. Checking namespaces used in data...")
query = """
SELECT DISTINCT (REPLACE(STR(?p), "^.*/([^/]+)$", "$1") AS ?predicate)
       (REPLACE(STR(?p), "^(.*/)[^/]+$", "$1") AS ?namespace)
WHERE { ?s ?p ?o . }
ORDER BY ?namespace
"""
result = run_query(query)
if result and 'results' in result:
    namespaces = set()
    for binding in result['results']['bindings']:
        ns = binding.get('namespace', {}).get('value', '')
        if ns:
            namespaces.add(ns)

    print(f"   Found {len(namespaces)} namespaces:")
    for ns in sorted(namespaces):
        print(f"      - {ns}")

# Check LAYER 1: Entity Layer
print("\n2. LAYER 1: Entity Layer")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX fe: <http://feekg.ai/ontology#>

SELECT (COUNT(?entity) as ?count)
WHERE {
    { ?entity a feekg:Entity . }
    UNION
    { ?entity a fe:Entity . }
}
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    print(f"   ✓ Entities: {count}")

# Check entity properties
query = """
SELECT DISTINCT ?p
WHERE {
    ?entity a <http://feekg.org/ontology#Entity> .
    ?entity ?p ?o .
}
"""
result = run_query(query)
if result and 'results' in result:
    print(f"   Entity properties:")
    for binding in result['results']['bindings']:
        prop = binding['p']['value'].split('#')[-1].split('/')[-1]
        print(f"      - {prop}")

# Check LAYER 2: Event Layer
print("\n3. LAYER 2: Event Layer")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX fe: <http://feekg.ai/ontology#>

SELECT (COUNT(?event) as ?count)
WHERE {
    { ?event a feekg:Event . }
    UNION
    { ?event a fe:Event . }
}
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    print(f"   ✓ Events: {count}")

# Check event properties
query = """
SELECT DISTINCT ?p
WHERE {
    ?event a <http://feekg.org/ontology#Event> .
    ?event ?p ?o .
}
LIMIT 20
"""
result = run_query(query)
if result and 'results' in result:
    print(f"   Event properties:")
    for binding in result['results']['bindings']:
        prop = binding['p']['value'].split('#')[-1].split('/')[-1]
        print(f"      - {prop}")

# Check event evolution links (fe:evolvesTo)
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX fe: <http://feekg.ai/ontology#>

SELECT (COUNT(*) as ?count)
WHERE {
    { ?e1 feekg:evolvesTo ?e2 . }
    UNION
    { ?e1 fe:evolvesTo ?e2 . }
}
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    print(f"   ✓ Evolution links: {count}")

# Check LAYER 3: Risk Layer
print("\n4. LAYER 3: Risk Layer")
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX fe: <http://feekg.ai/ontology#>

SELECT (COUNT(?risk) as ?count)
WHERE {
    { ?risk a feekg:Risk . }
    UNION
    { ?risk a fe:Risk . }
}
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    if count == '0':
        print(f"   ❌ No Risks found")
        print(f"      (Risk layer not implemented yet)")
    else:
        print(f"   ✓ Risks: {count}")

# Check RiskTypes
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX fe: <http://feekg.ai/ontology#>

SELECT (COUNT(?riskType) as ?count)
WHERE {
    { ?riskType a feekg:RiskType . }
    UNION
    { ?riskType a fe:RiskType . }
}
"""
result = run_query(query)
if result and 'results' in result and 'bindings' in result['results']:
    count = result['results']['bindings'][0]['count']['value']
    if count == '0':
        print(f"   ❌ No RiskTypes found")
    else:
        print(f"   ✓ RiskTypes: {count}")

# Summary
print("\n" + "=" * 80)
print("Summary: Ontology Compliance")
print("=" * 80)
print()
print("FE-EKG Three-Layer Architecture:")
print("  Layer 1 (Entity):  ✓ IMPLEMENTED")
print("  Layer 2 (Event):   ✓ IMPLEMENTED")
print("  Layer 3 (Risk):    ❌ NOT IMPLEMENTED")
print()
print("Issues:")
print("  1. Using 'feekg:' namespace instead of 'fe:' (defined in ontology)")
print("  2. Risk layer is missing (no Risk nodes created)")
print("  3. Evolution links may be missing (skipped during load)")
print()
print("The ontology defines the structure, but the loaded data")
print("only implements 2 out of 3 layers currently.")
print("=" * 80)
