"""
RDF Backend for FE-EKG using AllegroGraph

Converts FE-EKG data to RDF triples and stores in AllegroGraph.
Can work alongside Neo4j or as standalone backend.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from franz.openrdf.connect import ag_connect
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.sail.allegrographserver import AllegroGraphServer


class RDFBackend:
    """
    RDF/SPARQL backend using AllegroGraph

    Converts FE-EKG entities, events, and risks to RDF triples
    """

    def __init__(self):
        """Initialize AllegroGraph connection"""
        self.ag_url = os.getenv('AG_URL', 'https://qa-agraph.nelumbium.ai/')
        self.ag_user = os.getenv('AG_USER', 'sadmin')
        self.ag_pass = os.getenv('AG_PASS')
        self.ag_repo = os.getenv('AG_REPO', 'feekg_dev')

        # Ensure URL has explicit port 443 for HTTPS
        if ':443' not in self.ag_url and self.ag_url.startswith('https://'):
            self.ag_url = self.ag_url.rstrip('/') + ':443'

        # FE-EKG namespace
        self.FEEKG = "http://feekg.org/ontology#"

        self.conn = None

    def connect(self):
        """Establish connection to AllegroGraph using HTTPS (port 443)"""
        try:
            # Use ag_connect with full HTTPS URL including port 443
            # This works through firewalls that block port 10035
            self.conn = ag_connect(
                self.ag_repo,
                user=self.ag_user,
                host=self.ag_url,  # Full URL with :443
                password=self.ag_pass
            )
            print(f"✅ Connected to AllegroGraph: {self.ag_repo}")
            print(f"✅ Triple count: {self.conn.size()}")
            return True
        except Exception as e:
            print(f"❌ AllegroGraph connection failed: {e}")
            return False

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()

    def create_event_triple(self, event: Dict):
        """
        Convert event to RDF triples

        Args:
            event: Event dict from data/evergrande_crisis.json
        """
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        event_id = event['eventId']
        event_uri = self.conn.createURI(f"{self.FEEKG}{event_id}")

        # Type triple
        self.conn.add(event_uri, RDF.TYPE, self.conn.createURI(f"{self.FEEKG}Event"))

        # Properties
        self.conn.add(event_uri,
                     self.conn.createURI(f"{self.FEEKG}eventType"),
                     self.conn.createLiteral(event['type']))

        self.conn.add(event_uri,
                     self.conn.createURI(f"{self.FEEKG}date"),
                     self.conn.createLiteral(event['date'], datatype=XMLSchema.DATE))

        if 'description' in event:
            self.conn.add(event_uri,
                         self.conn.createURI(f"{self.FEEKG}description"),
                         self.conn.createLiteral(event['description']))

        # Actor relationship
        if 'actor' in event:
            actor_uri = self.conn.createURI(f"{self.FEEKG}{event['actor']}")
            self.conn.add(event_uri,
                         self.conn.createURI(f"{self.FEEKG}hasActor"),
                         actor_uri)

        # Target relationship
        if 'target' in event:
            target_uri = self.conn.createURI(f"{self.FEEKG}{event['target']}")
            self.conn.add(event_uri,
                         self.conn.createURI(f"{self.FEEKG}hasTarget"),
                         target_uri)

    def create_entity_triple(self, entity: Dict):
        """Convert entity to RDF triples"""
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        entity_id = entity['entityId']
        entity_uri = self.conn.createURI(f"{self.FEEKG}{entity_id}")

        # Type
        self.conn.add(entity_uri, RDF.TYPE, self.conn.createURI(f"{self.FEEKG}Entity"))

        # Properties
        self.conn.add(entity_uri,
                     self.conn.createURI(f"{self.FEEKG}name"),
                     self.conn.createLiteral(entity['name']))

        self.conn.add(entity_uri,
                     self.conn.createURI(f"{self.FEEKG}entityType"),
                     self.conn.createLiteral(entity['type']))

        if 'sector' in entity:
            self.conn.add(entity_uri,
                         self.conn.createURI(f"{self.FEEKG}sector"),
                         self.conn.createLiteral(entity['sector']))

    def create_risk_triple(self, risk: Dict):
        """Convert risk to RDF triples"""
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        risk_id = risk['riskId']
        risk_uri = self.conn.createURI(f"{self.FEEKG}{risk_id}")

        # Type
        self.conn.add(risk_uri, RDF.TYPE, self.conn.createURI(f"{self.FEEKG}Risk"))

        # Properties
        self.conn.add(risk_uri,
                     self.conn.createURI(f"{self.FEEKG}riskType"),
                     self.conn.createLiteral(risk['type']))

        self.conn.add(risk_uri,
                     self.conn.createURI(f"{self.FEEKG}score"),
                     self.conn.createLiteral(risk['score'], datatype=XMLSchema.FLOAT))

        self.conn.add(risk_uri,
                     self.conn.createURI(f"{self.FEEKG}severity"),
                     self.conn.createLiteral(risk['severity']))

        # Target entity relationship
        if 'targetEntity' in risk:
            entity_uri = self.conn.createURI(f"{self.FEEKG}{risk['targetEntity']}")
            self.conn.add(risk_uri,
                         self.conn.createURI(f"{self.FEEKG}targetsEntity"),
                         entity_uri)

    def create_evolution_triple(self, from_event: str, to_event: str, score: float, metadata: Dict):
        """
        Create evolution relationship triple

        Args:
            from_event: Source event ID
            to_event: Target event ID
            score: Evolution score
            metadata: Additional properties (causality, temporal, etc.)
        """
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        from_uri = self.conn.createURI(f"{self.FEEKG}{from_event}")
        to_uri = self.conn.createURI(f"{self.FEEKG}{to_event}")

        # Main evolution relationship
        self.conn.add(from_uri,
                     self.conn.createURI(f"{self.FEEKG}evolvesTo"),
                     to_uri)

        # RDF doesn't support properties on relationships directly
        # Use reification or named graph
        edge_id = f"{from_event}_to_{to_event}"
        edge_uri = self.conn.createURI(f"{self.FEEKG}{edge_id}")

        # Reification pattern
        self.conn.add(edge_uri, RDF.TYPE, self.conn.createURI(f"{self.FEEKG}EvolutionLink"))
        self.conn.add(edge_uri, self.conn.createURI(f"{self.FEEKG}fromEvent"), from_uri)
        self.conn.add(edge_uri, self.conn.createURI(f"{self.FEEKG}toEvent"), to_uri)
        self.conn.add(edge_uri,
                     self.conn.createURI(f"{self.FEEKG}score"),
                     self.conn.createLiteral(score, datatype=XMLSchema.FLOAT))

        # Add component scores
        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                self.conn.add(edge_uri,
                             self.conn.createURI(f"{self.FEEKG}{key}"),
                             self.conn.createLiteral(float(value), datatype=XMLSchema.FLOAT))

    def query_sparql(self, query: str) -> List[Dict]:
        """
        Execute SPARQL query

        Args:
            query: SPARQL query string

        Returns:
            List of result bindings
        """
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        result = self.conn.prepareTupleQuery(query=query).evaluate()

        results = []
        for binding in result:
            row = {}
            for var in result.getBindingNames():
                value = binding.getValue(var)
                if value:
                    row[var] = str(value)
            results.append(row)

        return results

    def export_to_turtle(self, output_file: str):
        """Export all triples to Turtle format"""
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        with open(output_file, 'w') as f:
            # Write prefixes
            f.write(f"@prefix feekg: <{self.FEEKG}> .\n")
            f.write(f"@prefix rdf: <{RDF.NAMESPACE}> .\n")
            f.write(f"@prefix xsd: <{XMLSchema.NAMESPACE}> .\n\n")

            # Export all triples
            statements = self.conn.getStatements(None, None, None)
            for stmt in statements:
                subject = stmt.getSubject()
                predicate = stmt.getPredicate()
                obj = stmt.getObject()

                f.write(f"{subject} {predicate} {obj} .\n")

        print(f"✅ Exported to {output_file}")

    def get_stats(self) -> Dict:
        """Get repository statistics"""
        if not self.conn:
            raise ConnectionError("Not connected to AllegroGraph")

        return {
            'total_triples': self.conn.size(),
            'repository': self.ag_repo,
            'timestamp': datetime.utcnow().isoformat()
        }


# Example usage
if __name__ == '__main__':
    backend = RDFBackend()

    if backend.connect():
        # Example: Add an event
        event = {
            'eventId': 'evt_test',
            'type': 'debt_default',
            'date': '2021-12-01',
            'description': 'Test event',
            'actor': 'ent_evergrande',
            'target': 'ent_minsheng'
        }

        backend.create_event_triple(event)

        # Query
        query = """
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT ?event ?type ?date
        WHERE {
            ?event a feekg:Event .
            ?event feekg:eventType ?type .
            ?event feekg:date ?date .
        }
        LIMIT 10
        """

        results = backend.query_sparql(query)
        print(f"Found {len(results)} events")

        # Stats
        stats = backend.get_stats()
        print(f"Total triples: {stats['total_triples']}")

        backend.close()
