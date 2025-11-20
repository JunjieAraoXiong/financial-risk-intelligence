"""
Interactive Knowledge Graph Visualization for AllegroGraph

Creates interactive HTML visualization using SPARQL queries
"""

import sys
import os
from typing import Optional
from pyvis.network import Network

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class InteractiveKnowledgeGraphAG:
    """Create interactive web-based knowledge graph from AllegroGraph data"""

    def __init__(self):
        """Initialize with AllegroGraph connection"""
        self.backend = get_connection()

        # Color scheme
        self.colors = {
            'entity': '#3498db',      # Blue
            'event': '#e74c3c',       # Red
            'risk': '#f39c12',        # Orange
            'evolution': 'rgba(231, 76, 60, 0.6)'
        }

    def close(self):
        """Close database connection"""
        self.backend.close()

    def create_entity_event_graph(self,
                                  max_events: int = 100,
                                  height: str = "900px",
                                  width: str = "100%",
                                  save_path: Optional[str] = None) -> Network:
        """
        Create interactive visualization of entities and events

        Args:
            max_events: Maximum number of events to visualize
            height: Height of visualization
            width: Width of visualization
            save_path: Path to save HTML file

        Returns:
            Network object
        """
        print("Fetching AllegroGraph data...")

        if save_path is None:
            save_path = "results/interactive_kg_lehman.html"

        # Create network
        net = Network(height=height, width=width,
                     bgcolor="#ffffff",
                     font_color="#000000",
                     directed=True)

        # Configure physics
        net.set_options("""
        {
          "nodes": {
            "font": {"size": 14, "face": "Arial"},
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
            "color": {"inherit": "from"},
            "smooth": {"type": "curvedCW", "roundness": 0.2},
            "shadow": true
          },
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 200},
            "barnesHut": {
              "gravitationalConstant": -5000,
              "centralGravity": 0.2,
              "springLength": 150,
              "springConstant": 0.02,
              "damping": 0.09,
              "avoidOverlap": 0.1
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        # Fetch entities
        print("Adding entities...")
        entity_query = """
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?entity ?label ?type
        WHERE {
          ?entity a feekg:Entity .
          OPTIONAL { ?entity rdfs:label ?label }
          OPTIONAL { ?entity feekg:entityType ?type }
        }
        """
        entities = self.backend.execute_query(entity_query)

        # Track unique entities by label (to handle duplicates)
        entity_map = {}
        for entity in entities:
            label = entity.get('label', 'Unknown')
            entity_type = entity.get('type', 'unknown')

            # Use label as node ID
            if label not in entity_map:
                entity_map[label] = {
                    'uri': entity['entity'],
                    'type': entity_type
                }

                net.add_node(
                    label,
                    label=label,
                    title=f"<b>Entity: {label}</b><br>Type: {entity_type}",
                    color=self.colors['entity'],
                    shape='box',
                    size=30,
                    group='entity'
                )

        print(f"Added {len(entity_map)} unique entities")

        # Fetch sample events with date ordering
        print(f"Adding up to {max_events} events...")
        event_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?label ?type ?date ?desc
        WHERE {{
          ?event a feekg:Event .
          OPTIONAL {{ ?event rdfs:label ?label }}
          OPTIONAL {{ ?event feekg:eventType ?type }}
          OPTIONAL {{ ?event feekg:date ?date }}
          OPTIONAL {{ ?event feekg:description ?desc }}
        }}
        ORDER BY ?date
        LIMIT {max_events}
        """
        events = self.backend.execute_query(event_query)

        event_nodes = {}
        for i, event in enumerate(events):
            event_id = f"event_{i}"
            label = event.get('label', f"Event {i}")
            event_type = event.get('type', 'unknown')
            date = event.get('date', 'unknown')
            desc = event.get('desc', '')[:100]

            title = f"""<b>Event: {label}</b><br>
            Type: {event_type}<br>
            Date: {date}<br>
            Description: {desc}..."""

            net.add_node(
                event_id,
                label=label[:30],
                title=title,
                color=self.colors['event'],
                shape='ellipse',
                size=20,
                group='event'
            )

            event_nodes[event['event']] = event_id

        print(f"Added {len(events)} events")

        # Fetch event-entity relationships (actor)
        print("Adding event-entity relationships...")
        actor_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?actor ?actorLabel
        WHERE {{
          ?event a feekg:Event .
          ?event feekg:actor ?actor .
          ?actor rdfs:label ?actorLabel .
          FILTER(?event IN ({', '.join([f'<{e["event"]}>' for e in events])}))
        }}
        LIMIT 500
        """

        try:
            actors = self.backend.execute_query(actor_query)
            for rel in actors:
                event_uri = rel['event']
                actor_label = rel['actorLabel']

                if event_uri in event_nodes and actor_label in entity_map:
                    net.add_edge(
                        event_nodes[event_uri],
                        actor_label,
                        title='HAS_ACTOR',
                        color='#e74c3c',
                        width=1.5
                    )
            print(f"Added {len(actors)} actor relationships")
        except Exception as e:
            print(f"No actor relationships found: {e}")

        # Fetch event-entity involvement relationships
        involves_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?entity ?entityLabel
        WHERE {{
          ?event a feekg:Event .
          ?event feekg:involves ?entity .
          ?entity rdfs:label ?entityLabel .
          FILTER(?event IN ({', '.join([f'<{e["event"]}>' for e in events])}))
        }}
        LIMIT 500
        """

        try:
            involves = self.backend.execute_query(involves_query)
            for rel in involves:
                event_uri = rel['event']
                entity_label = rel['entityLabel']

                if event_uri in event_nodes and entity_label in entity_map:
                    net.add_edge(
                        event_nodes[event_uri],
                        entity_label,
                        title='INVOLVES',
                        color='#3498db',
                        width=1.5,
                        dashes=True
                    )
            print(f"Added {len(involves)} involvement relationships")
        except Exception as e:
            print(f"No involvement relationships found: {e}")

        # Fetch evolution links if they exist
        print("Checking for evolution links...")
        evolution_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT ?from ?to ?score ?causality ?temporal ?semantic
        WHERE {{
          ?from feekg:evolvesTo ?to .
          OPTIONAL {{ ?to feekg:score ?score }}
          OPTIONAL {{ ?to feekg:causalityScore ?causality }}
          OPTIONAL {{ ?to feekg:temporalScore ?temporal }}
          OPTIONAL {{ ?to feekg:semanticScore ?semantic }}
          FILTER(?from IN ({', '.join([f'<{e["event"]}>' for e in events])}))
          FILTER(?to IN ({', '.join([f'<{e["event"]}>' for e in events])}))
        }}
        LIMIT 200
        """

        try:
            evolutions = self.backend.execute_query(evolution_query)
            if evolutions:
                for rel in evolutions:
                    from_uri = rel['from']
                    to_uri = rel['to']
                    score = float(rel.get('score', '0.5').split('^^')[0].strip('"'))

                    if from_uri in event_nodes and to_uri in event_nodes:
                        title = f"Evolution Score: {score:.3f}"
                        if 'causality' in rel:
                            causality = float(rel['causality'].split('^^')[0].strip('"'))
                            title += f"<br>Causality: {causality:.3f}"

                        width = 1 + score * 4
                        net.add_edge(
                            event_nodes[from_uri],
                            event_nodes[to_uri],
                            title=title,
                            color=self.colors['evolution'],
                            width=width,
                            value=score
                        )
                print(f"Added {len(evolutions)} evolution links")
            else:
                print("No evolution links found (need to compute them)")
        except Exception as e:
            print(f"No evolution links: {e}")

        # Save
        print(f"Saving to {save_path}...")
        net.save_graph(save_path)
        self._enhance_html(save_path, len(entity_map), len(events))

        print(f"\n✅ Interactive knowledge graph created!")
        print(f"📂 Open in browser: file://{os.path.abspath(save_path)}")

        return net

    def create_entity_network(self,
                             save_path: Optional[str] = None) -> Network:
        """
        Create focused visualization of entity relationships only

        Args:
            save_path: Path to save HTML file

        Returns:
            Network object
        """
        print("Creating entity network...")

        if save_path is None:
            save_path = "results/interactive_entities.html"

        # Create network
        net = Network(height="800px", width="100%",
                     bgcolor="#ffffff",
                     font_color="#000000",
                     directed=False)

        # Simpler physics for entity graph
        net.set_options("""
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3000,
              "springLength": 200
            }
          }
        }
        """)

        # Fetch entities with type
        query = """
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?entity ?label ?type
        WHERE {
          ?entity a feekg:Entity .
          OPTIONAL { ?entity rdfs:label ?label }
          OPTIONAL { ?entity feekg:entityType ?type }
        }
        """
        entities = self.backend.execute_query(query)

        # Group by type
        type_colors = {
            'investment_bank': '#e74c3c',
            'bank': '#3498db',
            'regulator': '#9b59b6',
            'unknown': '#95a5a6'
        }

        entity_map = {}
        for entity in entities:
            label = entity.get('label', 'Unknown')
            entity_type = entity.get('type', 'unknown')

            if label not in entity_map:
                entity_map[label] = entity_type
                color = type_colors.get(entity_type, type_colors['unknown'])

                net.add_node(
                    label,
                    label=label,
                    title=f"<b>{label}</b><br>Type: {entity_type}",
                    color=color,
                    size=35,
                    shape='dot'
                )

        print(f"Added {len(entity_map)} entities")

        # Save
        net.save_graph(save_path)
        self._enhance_html(save_path, len(entity_map), 0, entity_only=True)

        print(f"✅ Entity network created!")
        print(f"📂 Open in browser: file://{os.path.abspath(save_path)}")

        return net

    def _enhance_html(self, html_path: str, num_entities: int, num_events: int, entity_only: bool = False):
        """Add custom styling and legend"""

        with open(html_path, 'r') as f:
            html = f.read()

        title_text = "Entity Network" if entity_only else f"Lehman Brothers Case Study Knowledge Graph"
        subtitle = f"{num_entities} Entities" if entity_only else f"{num_entities} Entities • {num_events} Events"

        custom_html = f"""
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            #header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            #header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            #header p {{
                margin: 10px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            #legend {{
                position: absolute;
                top: 80px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                z-index: 1000;
                min-width: 200px;
            }}
            #legend h3 {{
                margin: 0 0 10px 0;
                font-size: 16px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 5px;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 8px 0;
                font-size: 13px;
            }}
            .legend-color {{
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 10px;
                border: 1px solid #ddd;
            }}
            #controls {{
                position: absolute;
                top: 80px;
                left: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                z-index: 1000;
            }}
            #controls h3 {{
                margin: 0 0 10px 0;
                font-size: 16px;
            }}
            #controls button {{
                margin: 5px 0;
                padding: 8px 15px;
                border: none;
                background: #667eea;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                font-size: 13px;
            }}
            #controls button:hover {{
                background: #764ba2;
            }}
        </style>

        <div id="header">
            <h1>{title_text}</h1>
            <p>{subtitle} | Drag nodes • Zoom • Click for details</p>
        </div>

        <div id="legend">
            <h3>Legend</h3>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Entities / Banks</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e74c3c;"></div>
                <span>Events / Inv. Banks</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #9b59b6;"></div>
                <span>Regulators</span>
            </div>
        </div>

        <div id="controls">
            <h3>Controls</h3>
            <button onclick="network.fit()">Fit to Screen</button>
            <button onclick="network.moveTo({{scale: 1.0}})">Reset Zoom</button>
            <button onclick="togglePhysics()">Toggle Physics</button>
        </div>

        <script>
            var physicsEnabled = true;
            function togglePhysics() {{
                physicsEnabled = !physicsEnabled;
                network.setOptions({{physics: {{enabled: physicsEnabled}}}});
            }}
        </script>
        """

        html = html.replace('<body>', '<body>' + custom_html)

        with open(html_path, 'w') as f:
            f.write(html)


if __name__ == "__main__":
    viz = InteractiveKnowledgeGraphAG()

    print("=" * 70)
    print("Creating Interactive Knowledge Graphs for Lehman Brothers Data")
    print("=" * 70)
    print()

    # Create full graph with limited events
    viz.create_entity_event_graph(
        max_events=50,  # Start with 50 events for faster rendering
        save_path="results/interactive_kg_lehman_50.html"
    )

    print()
    print("-" * 70)
    print()

    # Create larger graph
    viz.create_entity_event_graph(
        max_events=200,
        save_path="results/interactive_kg_lehman_200.html"
    )

    print()
    print("-" * 70)
    print()

    # Create entity-only network
    viz.create_entity_network(
        save_path="results/interactive_entities_lehman.html"
    )

    viz.close()

    print()
    print("=" * 70)
    print("✅ All interactive visualizations created!")
    print("=" * 70)
    print()
    print("Open these files in your browser:")
    print(f"  • results/interactive_kg_lehman_50.html - 50 events")
    print(f"  • results/interactive_kg_lehman_200.html - 200 events")
    print(f"  • results/interactive_entities_lehman.html - Entities only")
    print()
