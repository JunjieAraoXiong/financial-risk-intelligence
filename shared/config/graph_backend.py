"""
Graph Backend Abstraction Layer for FE-EKG.
Uses AllegroGraph (RDF) as the primary database.
"""

import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class GraphBackend(ABC):
    """Abstract base class for graph database backends"""

    @abstractmethod
    def connect(self):
        """Establish connection to graph database"""
        pass

    @abstractmethod
    def close(self):
        """Close connection"""
        pass

    @abstractmethod
    def size(self):
        """Return number of triples/nodes"""
        pass

    @abstractmethod
    def clear(self):
        """Clear all data (use with caution!)"""
        pass

    @abstractmethod
    def load_schema(self, schema_path):
        """Load schema/ontology"""
        pass

    @abstractmethod
    def execute_query(self, query, params=None):
        """Execute query (SPARQL or Cypher)"""
        pass

    @abstractmethod
    def add_triple(self, subject, predicate, obj):
        """Add a single triple/relationship"""
        pass

    @abstractmethod
    def add_triples(self, triples):
        """Add multiple triples/relationships"""
        pass


class AllegroGraphBackend(GraphBackend):
    """AllegroGraph implementation of graph backend"""

    def __init__(self):
        self.url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/')
        self.user = os.getenv('AG_USER')
        self.password = os.getenv('AG_PASS')
        self.catalog = os.getenv('AG_CATALOG', 'mycatalog')
        self.repo = os.getenv('AG_REPO', 'feekg_dev')

        # Ensure URL has explicit port 443 for HTTPS
        if ':443' not in self.url and self.url.startswith('https://'):
            self.url = self.url.rstrip('/') + ':443'

        self.conn = None

    def connect(self):
        """Connect to AllegroGraph using HTTPS (port 443)"""
        from franz.openrdf.connect import ag_connect

        try:
            # Use ag_connect with full HTTPS URL including port 443
            # This works through firewalls that block port 10035
            self.conn = ag_connect(
                self.repo,
                catalog=self.catalog,
                user=self.user,
                host=self.url,  # Full URL with :443
                password=self.password
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to AllegroGraph: {e}")

    def close(self):
        """Close AllegroGraph connection"""
        if self.conn:
            self.conn.close()

    def size(self):
        """Return triple count"""
        if not self.conn:
            raise RuntimeError("Not connected")
        return self.conn.size()

    def clear(self):
        """Delete all triples"""
        if not self.conn:
            raise RuntimeError("Not connected")
        self.conn.clear()

    def load_schema(self, schema_path):
        """Load TTL ontology"""
        if not self.conn:
            raise RuntimeError("Not connected")

        with open(schema_path, 'r') as f:
            ttl_content = f.read()

        self.conn.addData(ttl_content, format='turtle')

    def execute_query(self, query, params=None):
        """Execute SPARQL query"""
        if not self.conn:
            raise RuntimeError("Not connected")

        result = self.conn.prepareTupleQuery(query=query).evaluate()
        rows = []
        for binding in result:
            row = {}
            for var in binding.getBindingNames():
                value = binding.getValue(var)
                row[var] = str(value) if value else None
            rows.append(row)
        return rows

    def add_triple(self, subject, predicate, obj):
        """Add single triple"""
        if not self.conn:
            raise RuntimeError("Not connected")
        self.conn.addTriple(subject, predicate, obj)

    def add_triples(self, triples):
        """Add multiple triples"""
        if not self.conn:
            raise RuntimeError("Not connected")
        self.conn.addTriples(triples)


def get_backend():
    """
    Factory function to get the configured backend.

    Returns:
        GraphBackend: AllegroGraph backend instance
    """
    return AllegroGraphBackend()


def get_connection():
    """
    Convenience function to get a connected backend.

    Returns:
        GraphBackend: Connected backend instance

    Example:
        >>> backend = get_connection()
        >>> size = backend.size()
        >>> backend.close()
    """
    backend = get_backend()
    backend.connect()
    return backend


if __name__ == "__main__":
    # Test backend
    backend = get_backend()
    print(f"Backend class: {backend.__class__.__name__}")
