"""
Apache Jena Fuseki Backend for FE-EKG

Free, open-source RDF database with full SPARQL support.
Easier to set up than AllegroGraph.
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime


class FusekiBackend:
    """
    Apache Jena Fuseki RDF backend

    Connects to a Fuseki server running locally or remotely
    """

    def __init__(self, base_url: str = 'http://localhost:3030', dataset: str = 'feekg'):
        """
        Initialize Fuseki connection

        Args:
            base_url: Fuseki server URL (default: http://localhost:3030)
            dataset: Dataset name (default: feekg)
        """
        self.base_url = base_url.rstrip('/')
        self.dataset = dataset
        self.sparql_endpoint = f"{self.base_url}/{dataset}/sparql"
        self.update_endpoint = f"{self.base_url}/{dataset}/update"
        self.data_endpoint = f"{self.base_url}/{dataset}/data"

        # FE-EKG namespace
        self.FEEKG = "http://feekg.org/ontology#"

    def test_connection(self) -> bool:
        """Test if Fuseki server is accessible"""
        try:
            response = requests.get(f"{self.base_url}/$/ping", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def upload_turtle_file(self, file_path: str) -> bool:
        """
        Upload Turtle (.ttl) file to Fuseki

        Args:
            file_path: Path to .ttl file

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'rb') as f:
                headers = {'Content-Type': 'text/turtle'}
                response = requests.post(
                    self.data_endpoint,
                    data=f,
                    headers=headers,
                    timeout=30
                )
                return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def upload_rdf_xml(self, file_path: str) -> bool:
        """Upload RDF/XML file to Fuseki"""
        try:
            with open(file_path, 'rb') as f:
                headers = {'Content-Type': 'application/rdf+xml'}
                response = requests.post(
                    self.data_endpoint,
                    data=f,
                    headers=headers,
                    timeout=30
                )
                return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def query_sparql(self, query: str, output_format: str = 'json') -> Dict:
        """
        Execute SPARQL SELECT query

        Args:
            query: SPARQL query string
            output_format: 'json', 'xml', 'csv', or 'tsv'

        Returns:
            Query results as dict (for JSON) or raw text
        """
        try:
            headers = {
                'Accept': self._get_accept_header(output_format)
            }

            response = requests.post(
                self.sparql_endpoint,
                data={'query': query},
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            if output_format == 'json':
                return response.json()
            else:
                return {'raw': response.text}

        except Exception as e:
            return {'error': str(e)}

    def execute_update(self, update: str) -> bool:
        """
        Execute SPARQL UPDATE (INSERT/DELETE)

        Args:
            update: SPARQL UPDATE string

        Returns:
            True if successful
        """
        try:
            response = requests.post(
                self.update_endpoint,
                data={'update': update},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            return response.status_code in [200, 201, 204]
        except Exception as e:
            print(f"Update failed: {e}")
            return False

    def insert_triple(self, subject: str, predicate: str, obj: str, is_literal: bool = False):
        """
        Insert a single RDF triple

        Args:
            subject: Subject URI (e.g., 'feekg:evt_001')
            predicate: Predicate URI (e.g., 'feekg:eventType')
            obj: Object (URI or literal)
            is_literal: True if object is a literal, False if URI
        """
        if is_literal:
            obj_str = f'"{obj}"'
        else:
            obj_str = obj

        update = f"""
        PREFIX feekg: <{self.FEEKG}>

        INSERT DATA {{
            {subject} {predicate} {obj_str} .
        }}
        """

        return self.execute_update(update)

    def clear_dataset(self) -> bool:
        """Clear all data from the dataset"""
        update = "CLEAR DEFAULT"
        return self.execute_update(update)

    def get_stats(self) -> Dict:
        """Get dataset statistics"""
        query = """
        SELECT (COUNT(*) as ?count)
        WHERE {
            ?s ?p ?o .
        }
        """

        result = self.query_sparql(query)

        if 'results' in result:
            bindings = result['results']['bindings']
            if bindings:
                count = int(bindings[0]['count']['value'])
                return {
                    'total_triples': count,
                    'dataset': self.dataset,
                    'endpoint': self.sparql_endpoint
                }

        return {'total_triples': 0, 'dataset': self.dataset}

    def _get_accept_header(self, output_format: str) -> str:
        """Get appropriate Accept header for format"""
        formats = {
            'json': 'application/sparql-results+json',
            'xml': 'application/sparql-results+xml',
            'csv': 'text/csv',
            'tsv': 'text/tab-separated-values'
        }
        return formats.get(output_format, formats['json'])


# Example usage
if __name__ == '__main__':
    import sys
    import os

    fuseki = FusekiBackend()

    # Test connection
    print("Testing Fuseki connection...")
    if fuseki.test_connection():
        print("✅ Fuseki is running!")
    else:
        print("❌ Fuseki not accessible")
        print("\nTo start Fuseki:")
        print("  chmod +x scripts/setup_fuseki.sh")
        print("  ./scripts/setup_fuseki.sh")
        sys.exit(1)

    # Upload RDF file
    turtle_file = 'results/feekg_graph.ttl'
    if os.path.exists(turtle_file):
        print(f"\nUploading {turtle_file}...")
        if fuseki.upload_turtle_file(turtle_file):
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed")

    # Get stats
    print("\nDataset statistics:")
    stats = fuseki.get_stats()
    print(f"  Total triples: {stats['total_triples']}")
    print(f"  Dataset: {stats['dataset']}")
    print(f"  Endpoint: {stats['endpoint']}")

    # Example query
    print("\nQuerying for events...")
    query = """
    PREFIX feekg: <http://feekg.org/ontology#>

    SELECT ?event ?type ?date
    WHERE {
        ?event a feekg:Event .
        ?event feekg:eventType ?type .
        ?event feekg:date ?date .
    }
    ORDER BY ?date
    LIMIT 5
    """

    result = fuseki.query_sparql(query)

    if 'results' in result:
        print("\nFirst 5 events:")
        for binding in result['results']['bindings']:
            event_type = binding['type']['value']
            date = binding['date']['value']
            print(f"  - {event_type} on {date}")
    else:
        print(f"Query error: {result.get('error', 'Unknown error')}")
