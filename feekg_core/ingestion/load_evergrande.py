"""
Load Evergrande crisis data into Neo4j (or AllegroGraph).
Creates entities, events, risks, and their relationships.
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


def load_evergrande_data(json_path='data/evergrande_crisis.json'):
    """Load Evergrande crisis data into graph database"""

    backend_type = os.getenv('GRAPH_BACKEND', 'neo4j')

    print("=" * 60)
    print("FE-EKG Data Ingestion: Evergrande Crisis")
    print("=" * 60)
    print(f"\n📊 Backend: {backend_type}")
    print(f"📁 Data file: {json_path}\n")

    # Load JSON data
    print("1️⃣  Loading JSON data...")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        print(f"   ✅ Loaded {data['metadata']['events_count']} events")
        print(f"   ✅ Loaded {data['metadata']['entities_count']} entities")
        print(f"   ✅ Loaded {data['metadata']['risks_count']} risks")
    except Exception as e:
        print(f"   ❌ Failed to load JSON: {e}")
        return False

    # Connect to backend
    print("\n2️⃣  Connecting to graph database...")
    try:
        backend = get_connection()
        print(f"   ✅ Connected to {backend.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

    # Ingest data (Neo4j specific for MVP)
    if backend_type.lower() == 'neo4j':
        success = load_to_neo4j(backend, data)
    else:
        print("   ⚠️  AllegroGraph ingestion not yet implemented")
        success = False

    # Close connection
    backend.close()
    print("\n🔒 Connection closed")

    return success


def load_to_neo4j(backend, data):
    """Load data into Neo4j using Cypher queries"""

    # Step 1: Load Entities
    print("\n3️⃣  Loading entities...")
    entity_count = 0
    for entity in data['entities']:
        query = """
        MERGE (e:Entity {entityId: $entityId})
        SET e.name = $name,
            e.type = $type,
            e.description = $description,
            e.createdAt = datetime()
        RETURN e.entityId as id
        """
        try:
            result = backend.execute_query(query, entity)
            entity_count += 1
        except Exception as e:
            print(f"   ⚠️  Failed to create entity {entity['entityId']}: {e}")

    print(f"   ✅ Created {entity_count} entities")

    # Step 2: Load Events
    print("\n4️⃣  Loading events...")
    event_count = 0
    for event in data['events']:
        query = """
        MERGE (ev:Event {eventId: $eventId})
        SET ev.type = $type,
            ev.date = date($date),
            ev.description = $description,
            ev.source = $source,
            ev.confidence = $confidence,
            ev.createdAt = datetime()
        """

        # Add actor relationship
        if event.get('actor'):
            query += """
            WITH ev
            MATCH (actor:Entity {entityId: $actor})
            MERGE (ev)-[:HAS_ACTOR]->(actor)
            """

        # Add target relationship
        if event.get('target'):
            query += """
            WITH ev
            MATCH (target:Entity {entityId: $target})
            MERGE (ev)-[:HAS_TARGET]->(target)
            """

        query += " RETURN ev.eventId as id"

        try:
            result = backend.execute_query(query, event)
            event_count += 1
        except Exception as e:
            print(f"   ⚠️  Failed to create event {event['eventId']}: {e}")

    print(f"   ✅ Created {event_count} events")

    # Step 3: Load Risks
    print("\n5️⃣  Loading risks...")
    risk_count = 0
    for risk in data['risks']:
        query = """
        MERGE (r:Risk {riskId: $riskId})
        SET r.score = $initialScore,
            r.severity = $severity,
            r.probability = $probability,
            r.status = $status,
            r.detectedDate = date($detectedDate),
            r.description = $description,
            r.createdAt = datetime()
        WITH r
        MATCH (rt:RiskType {name: $riskType})
        MERGE (r)-[:HAS_RISK_TYPE]->(rt)
        WITH r
        MATCH (e:Entity {entityId: $targetEntity})
        MERGE (r)-[:TARGETS_ENTITY]->(e)
        WITH r
        MATCH (ev:Event {eventId: $triggeredBy})
        MERGE (ev)-[:INCREASES_RISK_OF]->(r)
        RETURN r.riskId as id
        """

        try:
            result = backend.execute_query(query, risk)
            risk_count += 1

            # Create initial risk snapshot
            snapshot_query = """
            MATCH (r:Risk {riskId: $riskId})
            CREATE (rs:RiskSnapshot {
                snapshotId: $snapshotId,
                time: datetime($time),
                score: $score,
                severity: $severity
            })
            MERGE (rs)-[:SNAP_OF]->(r)
            """

            snapshot_data = {
                'riskId': risk['riskId'],
                'snapshotId': f"{risk['riskId']}_snap_001",
                'time': f"{risk['detectedDate']}T00:00:00Z",
                'score': risk['initialScore'],
                'severity': risk['severity']
            }
            backend.execute_query(snapshot_query, snapshot_data)

        except Exception as e:
            print(f"   ⚠️  Failed to create risk {risk['riskId']}: {e}")

    print(f"   ✅ Created {risk_count} risks with snapshots")

    # Step 4: Create event evolution links (based on temporal proximity)
    print("\n6️⃣  Creating event evolution links...")
    evolution_query = """
    MATCH (e1:Event), (e2:Event)
    WHERE e1.date < e2.date
      AND duration.between(e1.date, e2.date).days <= 30
      AND e1.eventId < e2.eventId
    MERGE (e1)-[r:EVOLVES_TO]->(e2)
    SET r.confidence = 0.7,
        r.type = 'temporal'
    RETURN count(r) as count
    """

    try:
        result = backend.execute_query(evolution_query)
        evolution_count = result[0]['count'] if result else 0
        print(f"   ✅ Created {evolution_count} evolution links")
    except Exception as e:
        print(f"   ⚠️  Failed to create evolution links: {e}")

    # Step 5: Summary statistics
    print("\n7️⃣  Generating summary...")
    summary_queries = {
        "Total nodes": "MATCH (n) RETURN count(n) as count",
        "Total relationships": "MATCH ()-[r]->() RETURN count(r) as count",
        "Entities": "MATCH (e:Entity) RETURN count(e) as count",
        "Events": "MATCH (ev:Event) RETURN count(ev) as count",
        "Risks": "MATCH (r:Risk) RETURN count(r) as count",
        "Risk Snapshots": "MATCH (rs:RiskSnapshot) RETURN count(rs) as count"
    }

    print("\n   📊 Database Summary:")
    for label, query in summary_queries.items():
        try:
            result = backend.execute_query(query)
            count = result[0]['count'] if result else 0
            print(f"      {label}: {count}")
        except:
            pass

    print("\n" + "=" * 60)
    print("✅ Data Ingestion Complete!")
    print("=" * 60)
    print("\n🎯 Next Steps:")
    print("   1. Open Neo4j Browser: http://localhost:7474")
    print("   2. Run verification queries")
    print("   3. Visualize event evolution chains")
    print()

    return True


def print_example_queries():
    """Print example Cypher queries for exploration"""

    print("\n📝 Example Queries to Run in Neo4j Browser:")
    print("\n" + "=" * 60)

    queries = [
        ("Show all events in chronological order", """
MATCH (ev:Event)
RETURN ev.eventId, ev.type, ev.date, ev.description
ORDER BY ev.date
        """),

        ("Show event evolution chain", """
MATCH path = (e1:Event)-[:EVOLVES_TO*1..5]->(e2:Event)
RETURN path
LIMIT 10
        """),

        ("Show risks by severity", """
MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
RETURN rt.label as RiskType, r.severity, r.score, r.status
ORDER BY r.score DESC
        """),

        ("Show Evergrande's risk profile", """
MATCH (e:Entity {name: 'China Evergrande Group'})<-[:TARGETS_ENTITY]-(r:Risk)
MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
RETURN rt.label as RiskType, r.score, r.severity, r.status
ORDER BY r.score DESC
        """),

        ("Full three-layer graph for one event", """
MATCH (ev:Event {eventId: 'evt_006'})-[:HAS_ACTOR]->(actor:Entity)
MATCH (ev)-[:INCREASES_RISK_OF]->(r:Risk)-[:TARGETS_ENTITY]->(target:Entity)
MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
RETURN ev, actor, r, rt, target
        """),

        ("Contagion analysis", """
MATCH (e1:Entity)<-[:TARGETS_ENTITY]-(r:Risk)<-[:INCREASES_RISK_OF]-(ev:Event)
WHERE r.riskType = 'ContagionRisk'
MATCH (ev)-[:HAS_TARGET]->(e2:Entity)
RETURN e1.name as Source, r.score, e2.name as Affected
        """)
    ]

    for i, (title, query) in enumerate(queries, 1):
        print(f"\n{i}. {title}:")
        print("-" * 60)
        print(query.strip())
        print()


if __name__ == "__main__":
    success = load_evergrande_data()

    if success:
        print_example_queries()
        sys.exit(0)
    else:
        sys.exit(1)
