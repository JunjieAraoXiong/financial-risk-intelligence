"""
Interactive Knowledge Graph Visualization using Pyvis

Creates an interactive HTML visualization of the FE-EKG three-layer knowledge graph
that can be opened in a web browser with full interactivity.
"""

import sys
import os
from typing import Optional, Dict, List
from pyvis.network import Network

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class InteractiveKnowledgeGraph:
    """Create interactive web-based knowledge graph visualizations"""

    def __init__(self):
        """Initialize with database connection"""
        self.backend = get_connection()

        # Color scheme matching the static visualizations
        self.colors = {
            'entity': '#3498db',      # Blue
            'event': '#e74c3c',       # Red
            'risk': '#f39c12',        # Orange
            'risk_type': '#9b59b6'    # Purple
        }

    def close(self):
        """Close database connection"""
        self.backend.close()

    def create_full_knowledge_graph(self,
                                    height: str = "900px",
                                    width: str = "100%",
                                    save_path: Optional[str] = None) -> Network:
        """
        Create interactive visualization of the complete three-layer knowledge graph

        Args:
            height: Height of the visualization
            width: Width of the visualization
            save_path: Path to save the HTML file (defaults to results/interactive_kg.html)

        Returns:
            Network object with the visualization
        """
        print("Fetching knowledge graph data...")

        if save_path is None:
            save_path = "results/interactive_kg.html"

        # Create network with physics enabled for interactive layout
        net = Network(height=height, width=width,
                     bgcolor="#ffffff",
                     font_color="#000000",
                     directed=True)

        # Configure physics for better interaction
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
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 150,
              "springConstant": 0.04,
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

        # Fetch and add entities
        print("Adding entities...")
        entity_query = """
        MATCH (e:Entity)
        RETURN e.entityId as id, e.name as name, e.type as type
        """
        entities = self.backend.execute_query(entity_query)

        for entity in entities:
            net.add_node(
                entity['id'],
                label=entity['name'],
                title=f"<b>Entity: {entity['name']}</b><br>Type: {entity['type']}<br>ID: {entity['id']}",
                color=self.colors['entity'],
                shape='box',
                size=25,
                group='entity'
            )

        # Fetch and add events
        print("Adding events...")
        event_query = """
        MATCH (ev:Event)
        RETURN ev.eventId as id, ev.type as type, ev.date as date,
               ev.description as description, ev.sentiment as sentiment
        ORDER BY ev.date
        """
        events = self.backend.execute_query(event_query)

        for event in events:
            sentiment = event.get('sentiment', 'neutral')
            title = f"""<b>Event: {event['type']}</b><br>
            Date: {event['date']}<br>
            Sentiment: {sentiment}<br>
            ID: {event['id']}<br>
            Description: {event.get('description', 'N/A')[:100]}..."""

            net.add_node(
                event['id'],
                label=event['type'].replace('_', '\n'),
                title=title,
                color=self.colors['event'],
                shape='ellipse',
                size=20,
                group='event'
            )

        # Fetch and add risks
        print("Adding risks...")
        risk_query = """
        MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN r.riskId as id, rt.label as type, r.score as score,
               r.severity as severity, r.description as description
        """
        risks = self.backend.execute_query(risk_query)

        for risk in risks:
            score = risk.get('score', 0.5)
            severity = risk.get('severity', 'medium')
            title = f"""<b>Risk: {risk['type']}</b><br>
            Score: {score:.2f}<br>
            Severity: {severity}<br>
            ID: {risk['id']}<br>
            Description: {risk.get('description', 'N/A')[:100]}..."""

            net.add_node(
                risk['id'],
                label=f"{risk['type']}\n({score:.2f})",
                title=title,
                color=self.colors['risk'],
                shape='diamond',
                size=15 + score * 15,  # Size based on risk score
                group='risk'
            )

        # Fetch and add risk types
        print("Adding risk types...")
        risk_type_query = """
        MATCH (rt:RiskType)
        RETURN rt.name as id, rt.label as label, rt.description as description
        """
        risk_types = self.backend.execute_query(risk_type_query)

        for rt in risk_types:
            title = f"""<b>Risk Type: {rt['label']}</b><br>
            ID: {rt['id']}<br>
            Description: {rt.get('description', 'N/A')[:100]}..."""

            net.add_node(
                rt['id'],
                label=rt['label'],
                title=title,
                color=self.colors['risk_type'],
                shape='star',
                size=30,
                group='risk_type'
            )

        # Add entity relationships
        print("Adding entity relationships...")
        entity_rel_query = """
        MATCH (e1:Entity)-[r:RELATED_TO]-(e2:Entity)
        RETURN e1.entityId as source, e2.entityId as target,
               r.relationshipType as type
        """
        entity_rels = self.backend.execute_query(entity_rel_query) or []

        for rel in entity_rels:
            net.add_edge(
                rel['source'],
                rel['target'],
                title=rel.get('type', 'RELATED_TO'),
                color='#95a5a6',
                width=2
            )

        # Add event-entity relationships
        print("Adding event-entity relationships...")
        event_entity_query = """
        MATCH (ev:Event)-[r]->(e:Entity)
        WHERE type(r) IN ['HAS_ACTOR', 'HAS_TARGET']
        RETURN ev.eventId as source, e.entityId as target, type(r) as type
        """
        event_entity_rels = self.backend.execute_query(event_entity_query) or []

        for rel in event_entity_rels:
            net.add_edge(
                rel['source'],
                rel['target'],
                title=rel['type'],
                color='#e74c3c' if rel['type'] == 'HAS_ACTOR' else '#3498db',
                width=1.5
            )

        # Add event evolution relationships
        print("Adding event evolution relationships...")
        evolution_query = """
        MATCH (e1:Event)-[r:EVOLVES_TO {type: 'enhanced'}]->(e2:Event)
        WHERE r.score > 0.3
        RETURN e1.eventId as source, e2.eventId as target,
               r.score as score, r.causality as causality,
               r.temporal as temporal, r.semantic as semantic
        ORDER BY r.score DESC
        """
        evolution_rels = self.backend.execute_query(evolution_query) or []

        for rel in evolution_rels:
            score = rel['score']
            causality = rel.get('causality', 0)
            title = f"""Evolution Score: {score:.3f}<br>
            Causality: {causality:.3f}<br>
            Temporal: {rel.get('temporal', 0):.3f}<br>
            Semantic: {rel.get('semantic', 0):.3f}"""

            # Edge width and color intensity based on score
            width = 1 + score * 3
            opacity = int(100 + score * 155)
            color = f'rgba(231, 76, 60, {opacity/255:.2f})'

            net.add_edge(
                rel['source'],
                rel['target'],
                title=title,
                color=color,
                width=width,
                value=score  # Used for physics
            )

        # Add risk-entity relationships
        print("Adding risk-entity relationships...")
        risk_entity_query = """
        MATCH (r:Risk)-[:TARGETS_ENTITY]->(e:Entity)
        RETURN r.riskId as source, e.entityId as target
        """
        risk_entity_rels = self.backend.execute_query(risk_entity_query) or []

        for rel in risk_entity_rels:
            net.add_edge(
                rel['source'],
                rel['target'],
                title='TARGETS_ENTITY',
                color='#f39c12',
                width=1.5,
                dashes=True
            )

        # Add risk-type relationships
        print("Adding risk-type relationships...")
        risk_type_rel_query = """
        MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN r.riskId as source, rt.name as target
        """
        risk_type_rels = self.backend.execute_query(risk_type_rel_query) or []

        for rel in risk_type_rels:
            net.add_edge(
                rel['source'],
                rel['target'],
                title='HAS_RISK_TYPE',
                color='#9b59b6',
                width=1.5,
                dashes=True
            )

        # Save the visualization
        print(f"Saving interactive graph to {save_path}...")
        net.save_graph(save_path)

        # Add custom styling and legend to the HTML file
        self._enhance_html(save_path)

        print(f"✅ Interactive knowledge graph created!")
        print(f"📂 Open in browser: {os.path.abspath(save_path)}")

        return net

    def create_evolution_focus(self,
                              min_score: float = 0.5,
                              save_path: Optional[str] = None) -> Network:
        """
        Create focused interactive visualization of event evolution network

        Args:
            min_score: Minimum evolution score to include
            save_path: Path to save the HTML file

        Returns:
            Network object with the visualization
        """
        print(f"Creating evolution network (min_score={min_score})...")

        if save_path is None:
            save_path = f"results/interactive_evolution_{int(min_score*100)}.html"

        # Create network
        net = Network(height="900px", width="100%",
                     bgcolor="#ffffff",
                     font_color="#000000",
                     directed=True)

        # Configure for evolution view
        net.set_options("""
        {
          "nodes": {
            "font": {"size": 16, "face": "Arial"},
            "borderWidth": 3,
            "shadow": true
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}},
            "smooth": {"type": "curvedCW", "roundness": 0.15},
            "shadow": true
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -5000,
              "springLength": 200,
              "springConstant": 0.02
            }
          }
        }
        """)

        # Fetch evolution relationships
        query = f"""
        MATCH (e1:Event)-[r:EVOLVES_TO {{type: 'enhanced'}}]->(e2:Event)
        WHERE r.score >= {min_score}
        RETURN e1.eventId as source, e1.type as source_type, e1.date as source_date,
               e2.eventId as target, e2.type as target_type, e2.date as target_date,
               r.score as score, r.causality as causality, r.emotional as emotional,
               r.temporal as temporal, r.semantic as semantic
        ORDER BY r.score DESC
        """

        edges = self.backend.execute_query(query)

        if not edges:
            print(f"No evolution links with score >= {min_score}")
            return None

        # Track nodes to add
        nodes_data = {}

        for edge in edges:
            # Add source node
            if edge['source'] not in nodes_data:
                nodes_data[edge['source']] = {
                    'type': edge['source_type'],
                    'date': edge['source_date']
                }

            # Add target node
            if edge['target'] not in nodes_data:
                nodes_data[edge['target']] = {
                    'type': edge['target_type'],
                    'date': edge['target_date']
                }

        # Add nodes
        for node_id, data in nodes_data.items():
            title = f"""<b>Event: {data['type']}</b><br>
            Date: {data['date']}<br>
            ID: {node_id}"""

            net.add_node(
                node_id,
                label=data['type'].replace('_', '\n'),
                title=title,
                color=self.colors['event'],
                shape='ellipse',
                size=25
            )

        # Add edges
        for edge in edges:
            score = edge['score']
            causality = edge.get('causality', 0)
            title = f"""<b>Evolution Link</b><br>
            Overall Score: {score:.3f}<br>
            Causality: {causality:.3f}<br>
            Temporal: {edge.get('temporal', 0):.3f}<br>
            Semantic: {edge.get('semantic', 0):.3f}<br>
            Emotional: {edge.get('emotional', 0):.3f}"""

            width = 2 + score * 8
            opacity = int(150 + score * 105)
            color = f'rgba(231, 76, 60, {opacity/255:.2f})'

            net.add_edge(
                edge['source'],
                edge['target'],
                title=title,
                color=color,
                width=width,
                value=score
            )

        # Save
        print(f"Saving to {save_path}...")
        net.save_graph(save_path)
        self._enhance_html(save_path)

        print(f"✅ Evolution network created!")
        print(f"📂 Open in browser: {os.path.abspath(save_path)}")

        return net

    def _enhance_html(self, html_path: str):
        """Add custom styling and legend to the HTML file"""

        # Read the generated HTML
        with open(html_path, 'r') as f:
            html = f.read()

        # Add custom CSS and legend
        custom_html = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            #header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            #header h1 {
                margin: 0;
                font-size: 28px;
            }
            #header p {
                margin: 10px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }
            #legend {
                position: absolute;
                top: 80px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                z-index: 1000;
                min-width: 200px;
            }
            #legend h3 {
                margin: 0 0 10px 0;
                font-size: 16px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 5px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin: 8px 0;
                font-size: 13px;
            }
            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 10px;
                border: 1px solid #ddd;
            }
            #controls {
                position: absolute;
                top: 80px;
                left: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                z-index: 1000;
            }
            #controls h3 {
                margin: 0 0 10px 0;
                font-size: 16px;
            }
            #controls button {
                margin: 5px 0;
                padding: 8px 15px;
                border: none;
                background: #667eea;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
            }
            #controls button:hover {
                background: #764ba2;
            }
        </style>

        <div id="header">
            <h1>FE-EKG Interactive Knowledge Graph</h1>
            <p>Financial Event Evolution Knowledge Graph | Drag nodes • Zoom • Click for details</p>
        </div>

        <div id="legend">
            <h3>Node Types</h3>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Entities (Companies)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e74c3c;"></div>
                <span>Events</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #f39c12;"></div>
                <span>Risk Instances</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #9b59b6;"></div>
                <span>Risk Types</span>
            </div>
        </div>

        <div id="controls">
            <h3>Controls</h3>
            <button onclick="network.fit()">Fit to Screen</button>
            <button onclick="network.moveTo({scale: 1.0})">Reset Zoom</button>
            <button onclick="togglePhysics()">Toggle Physics</button>
        </div>

        <script>
            var physicsEnabled = true;
            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
                network.setOptions({physics: {enabled: physicsEnabled}});
            }
        </script>
        """

        # Insert after <body> tag
        html = html.replace('<body>', '<body>' + custom_html)

        # Write back
        with open(html_path, 'w') as f:
            f.write(html)


if __name__ == "__main__":
    viz = InteractiveKnowledgeGraph()

    print("=" * 60)
    print("Creating Interactive Knowledge Graph Visualizations")
    print("=" * 60)
    print()

    # Create full knowledge graph
    viz.create_full_knowledge_graph(
        save_path="results/interactive_kg.html"
    )

    print()
    print("-" * 60)
    print()

    # Create evolution-focused view
    viz.create_evolution_focus(
        min_score=0.5,
        save_path="results/interactive_evolution_50.html"
    )

    print()
    print("-" * 60)
    print()

    # Create high-confidence evolution view
    viz.create_evolution_focus(
        min_score=0.7,
        save_path="results/interactive_evolution_70.html"
    )

    viz.close()

    print()
    print("=" * 60)
    print("✅ All interactive visualizations created!")
    print("=" * 60)
    print()
    print("Open these files in your browser:")
    print("  • results/interactive_kg.html - Full knowledge graph")
    print("  • results/interactive_evolution_50.html - Evolution network (score ≥ 0.5)")
    print("  • results/interactive_evolution_70.html - Evolution network (score ≥ 0.7)")
    print()
