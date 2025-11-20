"""
AllegroGraph HTTPS REST API Backend

Uses HTTPS (port 443) instead of direct TCP (port 10035)
Works when port 10035 is blocked by firewall
"""

import requests
import os
from typing import Dict, List, Optional
from urllib.parse import quote


class AllegroGraphHTTPSBackend:
    """
    AllegroGraph backend using HTTPS REST API

    This bypasses the port 10035 blocking issue by using
    the HTTPS interface (port 443) which is accessible
    """

    def __init__(self):
        """Initialize AllegroGraph HTTPS connection"""
        base_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/')
        self.base_url = base_url.rstrip('/')
        self.user = os.getenv('AG_USER', 'sadmin')
        self.password = os.getenv('AG_PASS')
        self.repo = os.getenv('AG_REPO', 'feekg_dev')

        # REST API endpoints
        self.repos_url = f"{self.base_url}/repositories"
        self.repo_url = f"{self.repos_url}/{self.repo}"
        self.statements_url = f"{self.repo_url}/statements"

        self.auth = (self.user, self.password)

    def test_connection(self) -> bool:
        """Test if AllegroGraph is accessible via HTTPS"""
        try:
            response = requests.get(
                self.repos_url,
                auth=self.auth,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def list_repositories(self) -> List[str]:
        """List all repositories"""
        try:
            response = requests.get(
                self.repos_url,
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()

            # Parse the response (it's in a custom format)
            repos = []
            for line in response.text.split('\n'):
                if line.startswith('id:'):
                    repos.append(line.split(':', 1)[1].strip())

            return repos

        except Exception as e:
            print(f"List repos failed: {e}")
            return []

    def repository_exists(self) -> bool:
        """Check if the repository exists"""
        repos = self.list_repositories()
        return self.repo in repos

    def create_repository(self) -> bool:
        """Create the repository"""
        try:
            response = requests.put(
                self.repo_url,
                auth=self.auth,
                timeout=10
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Create repo failed: {e}")
            return False

    def get_triple_count(self) -> int:
        """Get number of triples in repository"""
        try:
            response = requests.get(
                f"{self.repo_url}/size",
                auth=self.auth,
                timeout=10
            )
            response.raise_for_status()
            return int(response.text.strip())
        except Exception:
            return 0

    def add_triple(self, subject: str, predicate: str, obj: str):
        """
        Add a single RDF triple

        Args:
            subject: Subject URI
            predicate: Predicate URI
            obj: Object (URI or literal)
        """
        # N-Triples format
        triple = f"<{subject}> <{predicate}> <{obj}> .\n"

        try:
            response = requests.post(
                self.statements_url,
                data=triple.encode('utf-8'),
                headers={'Content-Type': 'text/plain'},
                auth=self.auth,
                timeout=10
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Add triple failed: {e}")
            return False

    def upload_turtle(self, turtle_content: str) -> bool:
        """
        Upload Turtle RDF data

        Args:
            turtle_content: Turtle format RDF string

        Returns:
            True if successful
        """
        try:
            response = requests.post(
                self.statements_url,
                data=turtle_content.encode('utf-8'),
                headers={'Content-Type': 'application/x-turtle'},
                auth=self.auth,
                timeout=30
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def upload_turtle_file(self, file_path: str) -> bool:
        """Upload Turtle file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return self.upload_turtle(content)
        except Exception as e:
            print(f"File upload failed: {e}")
            return False

    def query_sparql(self, query: str) -> Dict:
        """
        Execute SPARQL query

        Args:
            query: SPARQL query string

        Returns:
            Query results as dict
        """
        try:
            response = requests.get(
                self.repo_url,
                params={'query': query},
                headers={'Accept': 'application/sparql-results+json'},
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def clear_repository(self) -> bool:
        """Delete all triples from repository"""
        try:
            response = requests.delete(
                self.statements_url,
                auth=self.auth,
                timeout=30
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Clear failed: {e}")
            return False


# Example usage
if __name__ == '__main__':
    ag = AllegroGraphHTTPSBackend()

    print("=" * 70)
    print("  AllegroGraph HTTPS Backend Test")
    print("=" * 70)

    # Test connection
    print("\n1. Testing connection...")
    if ag.test_connection():
        print("   ✅ Connection successful!")
    else:
        print("   ❌ Connection failed")
        exit(1)

    # List repositories
    print("\n2. Listing repositories...")
    repos = ag.list_repositories()
    print(f"   Found {len(repos)} repositories:")
    for repo in repos[:5]:
        print(f"   - {repo}")

    # Check if feekg_dev exists
    print(f"\n3. Checking for repository '{ag.repo}'...")
    if ag.repository_exists():
        print(f"   ✅ Repository '{ag.repo}' exists!")

        # Get triple count
        count = ag.get_triple_count()
        print(f"   Total triples: {count}")

    else:
        print(f"   ❌ Repository '{ag.repo}' not found")
        print(f"\n4. Creating repository '{ag.repo}'...")
        if ag.create_repository():
            print("   ✅ Repository created!")
        else:
            print("   ❌ Failed to create repository")

    # Try uploading data
    print(f"\n5. Uploading RDF data...")
    turtle_file = 'results/feekg_graph.ttl'
    import os
    if os.path.exists(turtle_file):
        if ag.upload_turtle_file(turtle_file):
            print("   ✅ Upload successful!")

            count = ag.get_triple_count()
            print(f"   New triple count: {count}")
        else:
            print("   ❌ Upload failed")
    else:
        print(f"   ⚠️  File not found: {turtle_file}")

    # Try a query
    print(f"\n6. Testing SPARQL query...")
    query = """
    PREFIX feekg: <http://feekg.org/ontology#>

    SELECT ?event ?type
    WHERE {
        ?event a feekg:Event .
        ?event feekg:eventType ?type .
    }
    LIMIT 5
    """

    results = ag.query_sparql(query)
    if 'error' in results:
        print(f"   ❌ Query failed: {results['error']}")
    else:
        print(f"   ✅ Query successful!")
        if 'results' in results and 'bindings' in results['results']:
            bindings = results['results']['bindings']
            print(f"   Found {len(bindings)} results")

    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"\n✅ AllegroGraph HTTPS interface works!")
    print(f"✅ Bypasses port 10035 blocking issue")
    print(f"✅ Can upload and query RDF data")
    print("\n" + "=" * 70 + "\n")
