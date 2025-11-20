"""
Graph Backend Abstraction Layer for FE-EKG.
Supports both AllegroGraph (RDF) and Neo4j (Property Graph).
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


class Neo4jBackend(GraphBackend):
    """Neo4j implementation of graph backend"""

    def __init__(self):
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASS', 'feekg2024')
        self.database = os.getenv('NEO4J_DB', 'neo4j')  # Use 'neo4j' as default
        self.driver = None
        self.session = None

    def connect(self):
        """Connect to Neo4j"""
        from neo4j import GraphDatabase

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def size(self):
        """Return total node count"""
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()['count']

    def clear(self):
        """Delete all nodes and relationships"""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")

    def load_schema(self, schema_path):
        """Execute Cypher schema file"""
        with open(schema_path, 'r') as f:
            cypher_script = f.read()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in cypher_script.split(';') if s.strip()]

        with self.driver.session(database=self.database) as session:
            for stmt in statements:
                # Skip comments
                if stmt.startswith('//') or not stmt:
                    continue
                try:
                    session.run(stmt)
                except Exception as e:
                    # Some statements might fail if constraints already exist
                    print(f"Warning: {e}")

    def execute_query(self, query, params=None):
        """Execute Cypher query"""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    def add_triple(self, subject, predicate, obj):
        """
        Add a triple as a relationship in Neo4j.
        subject and obj should be node IDs or dicts with node properties.
        """
        # Simplified: assume subject/obj are node IDs
        query = f"""
        MATCH (s {{id: $subject}})
        MATCH (o {{id: $obj}})
        MERGE (s)-[:{predicate}]->(o)
        """
        with self.driver.session(database=self.database) as session:
            session.run(query, {'subject': subject, 'obj': obj})

    def add_triples(self, triples):
        """Add multiple triples"""
        for subj, pred, obj in triples:
            self.add_triple(subj, pred, obj)


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
        GraphBackend: Configured backend instance (Neo4j or AllegroGraph)
    """
    backend_type = os.getenv('GRAPH_BACKEND', 'neo4j').lower()

    if backend_type == 'neo4j':
        return Neo4jBackend()
    elif backend_type == 'allegrograph' or backend_type == 'ag':
        return AllegroGraphBackend()
    else:
        raise ValueError(f"Unknown backend: {backend_type}. Use 'neo4j' or 'allegrograph'")


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
    # Test backend selection
    print(f"Selected backend: {os.getenv('GRAPH_BACKEND', 'neo4j')}")
    backend = get_backend()
    print(f"Backend class: {backend.__class__.__name__}")
