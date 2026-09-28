"""
Check contents of FEEKG repository in mycatalog
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

# Build URL for mycatalog
repo_url = f"{base_url}/catalogs/{catalog}/repositories/{repo}"
auth = (user, password)

print("=" * 80)
print("Checking FEEKG Repository in mycatalog")
print("=" * 80)
print(f"URL: {repo_url}")
print()

# 1. Check size
print("1. Checking triple count...")
try:
    response = requests.get(f"{repo_url}/size", auth=auth, timeout=10)
    response.raise_for_status()
    count = int(response.text.strip())
    print(f"   ✓ Triple count: {count}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    count = 0
print()

# 2. Get sample triples
if count > 0:
    print("2. Fetching sample triples...")
    query = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . }
    LIMIT 10
    """

    try:
        response = requests.get(
            repo_url,
            params={'query': query},
            headers={'Accept': 'application/sparql-results+json'},
            auth=auth,
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        if 'results' in results and 'bindings' in results['results']:
            bindings = results['results']['bindings']
            print(f"   ✓ Found {len(bindings)} sample triples:")
            print()
            for i, binding in enumerate(bindings, 1):
                s = binding.get('s', {}).get('value', 'N/A')
                p = binding.get('p', {}).get('value', 'N/A')
                o = binding.get('o', {}).get('value', 'N/A')

                # Shorten URIs for readability
                s_short = s.split('#')[-1].split('/')[-1][:50]
                p_short = p.split('#')[-1].split('/')[-1][:30]
                o_short = o.split('#')[-1].split('/')[-1][:50]

                print(f"   {i:2}. {s_short}")
                print(f"       --[{p_short}]--> {o_short}")
                print()
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
        print(f"   Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
    print()

    # 3. Get distinct predicates (to understand data structure)
    print("3. Analyzing data structure (distinct predicates)...")
    query = """
    SELECT DISTINCT ?p
    WHERE { ?s ?p ?o . }
    """

    try:
        response = requests.get(
            repo_url,
            params={'query': query},
            headers={'Accept': 'application/sparql-results+json'},
            auth=auth,
            timeout=10
        )
        response.raise_for_status()
        results = response.json()

        if 'results' in results and 'bindings' in results['results']:
            predicates = [b.get('p', {}).get('value', 'N/A') for b in results['results']['bindings']]
            print(f"   ✓ Found {len(predicates)} distinct predicates:")
            for pred in sorted(predicates):
                pred_short = pred.split('#')[-1].split('/')[-1]
                print(f"      - {pred_short}")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")

print()
print("=" * 80)
print("Summary")
print("=" * 80)
print(f"✓ Repository: {catalog}/{repo}")
print(f"✓ Total triples: {count}")
print(f"✓ Status: {'Has data' if count > 0 else 'Empty'}")
print()
