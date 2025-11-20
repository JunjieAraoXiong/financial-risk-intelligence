"""
Three-Layer Knowledge Graph Visualization

Implements visualizations for Entity, Event, and Risk layers
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class ThreeLayerVisualizer:
    """Visualize the three-layer FE-EKG architecture"""

    def __init__(self):
        """Initialize with database connection"""
        self.backend = get_connection()

        # Color scheme for different layers
        self.colors = {
            'entity': '#3498db',      # Blue
            'event': '#e74c3c',       # Red
            'risk': '#f39c12',        # Orange
            'risk_type': '#9b59b6'    # Purple
        }

    def close(self):
        """Close database connection"""
        self.backend.close()

    def fetch_graph_data(self, limit_events: int = 20) -> Dict:
        """
        Fetch data for visualization from Neo4j

        Args:
            limit_events: Maximum number of events to include

        Returns:
            Dict with nodes and edges for all three layers
        """
        # Fetch entities
        entity_query = """
        MATCH (e:Entity)
        RETURN e.entityId as id, e.name as name, e.type as type
        """
        entities = self.backend.execute_query(entity_query)

        # Fetch events with date ordering
        event_query = f"""
        MATCH (ev:Event)
        RETURN ev.eventId as id, ev.type as type, ev.date as date, ev.description as description
        ORDER BY ev.date
        LIMIT {limit_events}
        """
        events = self.backend.execute_query(event_query)

        # Fetch risks
        risk_query = """
        MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN r.riskId as id, rt.label as type, r.score as score, r.severity as severity
        """
        risks = self.backend.execute_query(risk_query)

        # Fetch risk types
        risk_type_query = """
        MATCH (rt:RiskType)
        RETURN rt.name as id, rt.label as label
        """
        risk_types = self.backend.execute_query(risk_type_query)

        # Fetch relationships
        # Entity relationships
        entity_rel_query = """
        MATCH (e1:Entity)-[r:RELATED_TO]-(e2:Entity)
        RETURN e1.entityId as source, e2.entityId as target, r.relationshipType as type
        """
        entity_rels = self.backend.execute_query(entity_rel_query) or []

        # Event-Entity relationships
        event_entity_query = f"""
        MATCH (ev:Event)-[r]->(e:Entity)
        WHERE type(r) IN ['HAS_ACTOR', 'HAS_TARGET']
        AND ev.eventId IN [{', '.join([f"'{e['id']}'" for e in events])}]
        RETURN ev.eventId as source, e.entityId as target, type(r) as type
        """
        event_entity_rels = self.backend.execute_query(event_entity_query) or []

        # Event evolution relationships
        evolution_query = f"""
        MATCH (e1:Event)-[r:EVOLVES_TO {{type: 'enhanced'}}]->(e2:Event)
        WHERE e1.eventId IN [{', '.join([f"'{e['id']}'" for e in events])}]
        AND e2.eventId IN [{', '.join([f"'{e['id']}'" for e in events])}]
        AND r.score > 0.4
        RETURN e1.eventId as source, e2.eventId as target, r.score as score, r.causality as causality
        """
        evolution_rels = self.backend.execute_query(evolution_query) or []

        # Risk-Entity relationships
        risk_entity_query = """
        MATCH (r:Risk)-[:TARGETS_ENTITY]->(e:Entity)
        RETURN r.riskId as source, e.entityId as target
        """
        risk_entity_rels = self.backend.execute_query(risk_entity_query) or []

        # Risk-RiskType relationships
        risk_type_rel_query = """
        MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN r.riskId as source, rt.name as target
        """
        risk_type_rels = self.backend.execute_query(risk_type_rel_query) or []

        return {
            'nodes': {
                'entities': entities,
                'events': events,
                'risks': risks,
                'risk_types': risk_types
            },
            'edges': {
                'entity_relations': entity_rels,
                'event_entity': event_entity_rels,
                'evolution': evolution_rels,
                'risk_entity': risk_entity_rels,
                'risk_type': risk_type_rels
            }
        }

    def create_three_layer_graph(self, limit_events: int = 15, save_path: Optional[str] = None):
        """
        Create comprehensive three-layer visualization

        Args:
            limit_events: Maximum events to show
            save_path: Optional path to save the figure
        """
        print("Fetching graph data...")
        data = self.fetch_graph_data(limit_events=limit_events)

        # Create figure with three subplots (layers)
        fig = plt.figure(figsize=(20, 18))

        # Title
        fig.suptitle('FE-EKG: Three-Layer Financial Event Knowledge Graph',
                     fontsize=20, fontweight='bold', y=0.98)

        # Layer 1: Entity Layer (bottom)
        ax1 = plt.subplot(3, 1, 3)
        self._draw_entity_layer(ax1, data)

        # Layer 2: Event Layer (middle)
        ax2 = plt.subplot(3, 1, 2)
        self._draw_event_layer(ax2, data)

        # Layer 3: Risk Layer (top)
        ax3 = plt.subplot(3, 1, 1)
        self._draw_risk_layer(ax3, data)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved to {save_path}")

        return fig

    def _draw_entity_layer(self, ax, data):
        """Draw the entity layer"""
        ax.set_title('Layer 1: Entity Layer (Companies, Institutions)',
                     fontsize=14, fontweight='bold', pad=20)

        G = nx.Graph()

        # Add entity nodes
        for entity in data['nodes']['entities']:
            G.add_node(entity['id'],
                      label=entity['name'][:30],
                      node_type='entity',
                      entity_type=entity['type'])

        # Add entity relationships
        for rel in data['edges']['entity_relations']:
            G.add_edge(rel['source'], rel['target'],
                      relationship=rel.get('type', 'RELATED_TO'))

        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Draw nodes
        node_colors = [self.colors['entity'] for _ in G.nodes()]
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              node_color=node_colors,
                              node_size=2000,
                              alpha=0.9)

        # Draw edges
        nx.draw_networkx_edges(G, pos, ax=ax,
                              edge_color='#95a5a6',
                              width=2,
                              alpha=0.5)

        # Draw labels
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=9,
                               font_weight='bold')

        ax.axis('off')
        ax.set_aspect('equal')

    def _draw_event_layer(self, ax, data):
        """Draw the event layer with evolution relationships"""
        ax.set_title('Layer 2: Event Layer (Financial Events & Evolution)',
                     fontsize=14, fontweight='bold', pad=20)

        G = nx.DiGraph()

        # Add event nodes
        for event in data['nodes']['events']:
            G.add_node(event['id'],
                      label=event['type'].replace('_', ' ').title()[:20],
                      date=event['date'],
                      node_type='event')

        # Add evolution relationships
        for rel in data['edges']['evolution']:
            G.add_edge(rel['source'], rel['target'],
                      score=rel['score'],
                      causality=rel.get('causality', 0))

        if len(G.nodes()) == 0:
            ax.text(0.5, 0.5, 'No events to display',
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            return

        # Layout - hierarchical by date
        pos = self._hierarchical_layout_by_date(G, data['nodes']['events'])

        # Draw edges with varying thickness based on score
        edge_weights = [G[u][v].get('score', 0.5) * 3 for u, v in G.edges()]
        nx.draw_networkx_edges(G, pos, ax=ax,
                              edge_color='#e74c3c',
                              width=edge_weights,
                              alpha=0.4,
                              arrows=True,
                              arrowsize=15,
                              arrowstyle='->')

        # Draw nodes
        node_colors = [self.colors['event'] for _ in G.nodes()]
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              node_color=node_colors,
                              node_size=1500,
                              alpha=0.9)

        # Draw labels
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=8,
                               font_weight='bold')

        ax.axis('off')
        ax.set_aspect('equal')

    def _draw_risk_layer(self, ax, data):
        """Draw the risk layer"""
        ax.set_title('Layer 3: Risk Layer (Risk Types & Instances)',
                     fontsize=14, fontweight='bold', pad=20)

        G = nx.Graph()

        # Add risk type nodes
        for rt in data['nodes']['risk_types']:
            G.add_node(rt['id'],
                      label=rt['label'],
                      node_type='risk_type')

        # Add risk instance nodes
        for risk in data['nodes']['risks']:
            risk_node_id = risk['id']
            G.add_node(risk_node_id,
                      label=f"{risk['type']}\n{risk['score']:.2f}",
                      node_type='risk',
                      score=risk['score'],
                      severity=risk['severity'])

        # Add risk-type relationships
        for rel in data['edges']['risk_type']:
            G.add_edge(rel['source'], rel['target'])

        # Layout
        pos = nx.spring_layout(G, k=3, iterations=50)

        # Draw nodes - different colors for types vs instances
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            if node_data['node_type'] == 'risk_type':
                node_colors.append(self.colors['risk_type'])
                node_sizes.append(2500)
            else:
                node_colors.append(self.colors['risk'])
                score = node_data.get('score', 0.5)
                node_sizes.append(1000 + score * 2000)

        nx.draw_networkx_nodes(G, pos, ax=ax,
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9)

        # Draw edges
        nx.draw_networkx_edges(G, pos, ax=ax,
                              edge_color='#95a5a6',
                              width=2,
                              alpha=0.5)

        # Draw labels
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=8,
                               font_weight='bold')

        # Legend
        legend_elements = [
            mpatches.Patch(color=self.colors['risk_type'], label='Risk Types'),
            mpatches.Patch(color=self.colors['risk'], label='Risk Instances')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        ax.axis('off')
        ax.set_aspect('equal')

    def _hierarchical_layout_by_date(self, G, events):
        """Create hierarchical layout based on event dates"""
        # Sort events by date
        date_map = {e['id']: datetime.strptime(str(e['date']), '%Y-%m-%d')
                    for e in events}

        sorted_nodes = sorted(G.nodes(), key=lambda n: date_map.get(n, datetime.min))

        pos = {}
        y_levels = {}

        # Assign y-coordinate based on date (earlier = lower)
        for i, node in enumerate(sorted_nodes):
            date = date_map.get(node)
            if date not in y_levels:
                y_levels[date] = len(y_levels)

            y = y_levels[date]
            # Spread x based on position within same date
            nodes_at_date = [n for n in sorted_nodes if date_map.get(n) == date]
            x_offset = nodes_at_date.index(node) - len(nodes_at_date) / 2

            pos[node] = (x_offset * 2, y * 2)

        return pos

    def create_evolution_network(self, min_score: float = 0.4,
                                 save_path: Optional[str] = None):
        """
        Create focused visualization of event evolution network

        Args:
            min_score: Minimum evolution score to include
            save_path: Optional path to save the figure
        """
        print(f"Creating evolution network (min_score={min_score})...")

        # Fetch evolution data
        query = f"""
        MATCH (e1:Event)-[r:EVOLVES_TO {{type: 'enhanced'}}]->(e2:Event)
        WHERE r.score >= {min_score}
        RETURN e1.eventId as source,
               e1.type as source_type,
               e1.date as source_date,
               e2.eventId as target,
               e2.type as target_type,
               e2.date as target_date,
               r.score as score,
               r.causality as causality,
               r.emotional as emotional
        ORDER BY r.score DESC
        """

        edges = self.backend.execute_query(query)

        if not edges:
            print(f"No evolution links with score >= {min_score}")
            return None

        # Build graph
        G = nx.DiGraph()

        for edge in edges:
            G.add_node(edge['source'],
                      event_type=edge['source_type'],
                      date=edge['source_date'])
            G.add_node(edge['target'],
                      event_type=edge['target_type'],
                      date=edge['target_date'])
            G.add_edge(edge['source'], edge['target'],
                      score=edge['score'],
                      causality=edge['causality'],
                      emotional=edge['emotional'])

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_title(f'Event Evolution Network (Evolution Score ≥ {min_score})',
                    fontsize=16, fontweight='bold', pad=20)

        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Draw edges with varying thickness
        edge_widths = [G[u][v]['score'] * 5 for u, v in G.edges()]
        edge_colors = [G[u][v].get('causality', 0.5) for u, v in G.edges()]

        edges_drawn = nx.draw_networkx_edges(
            G, pos, ax=ax,
            width=edge_widths,
            edge_color=edge_colors,
            edge_cmap=plt.cm.Reds,
            edge_vmin=0,
            edge_vmax=1,
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            alpha=0.6,
            connectionstyle='arc3,rad=0.1'
        )

        # Draw nodes
        node_colors = [self.colors['event'] for _ in G.nodes()]
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              node_color=node_colors,
                              node_size=2000,
                              alpha=0.9)

        # Draw labels
        labels = {node: G.nodes[node]['event_type'].replace('_', '\n')
                 for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=9,
                               font_weight='bold')

        # Colorbar for causality
        sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds,
                                   norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Causality Score', rotation=270, labelpad=20)

        ax.axis('off')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved to {save_path}")

        return fig

    def create_risk_propagation_view(self, save_path: Optional[str] = None):
        """
        Visualize risk propagation from entities to risks

        Args:
            save_path: Optional path to save the figure
        """
        print("Creating risk propagation visualization...")

        # Fetch data
        query = """
        MATCH (e:Entity)<-[:TARGETS_ENTITY]-(r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
        RETURN e.entityId as entity_id,
               e.name as entity_name,
               r.riskId as risk_id,
               r.score as risk_score,
               r.severity as severity,
               rt.label as risk_type
        """

        data = self.backend.execute_query(query)

        if not data:
            print("No risk data found")
            return None

        # Build bipartite graph
        G = nx.Graph()

        for row in data:
            # Add entity node
            G.add_node(row['entity_id'],
                      label=row['entity_name'][:25],
                      node_type='entity',
                      bipartite=0)

            # Add risk node
            risk_label = f"{row['risk_type']}\n{row['risk_score']:.2f}"
            G.add_node(row['risk_id'],
                      label=risk_label,
                      node_type='risk',
                      score=row['risk_score'],
                      severity=row['severity'],
                      bipartite=1)

            # Add edge
            G.add_edge(row['entity_id'], row['risk_id'],
                      score=row['risk_score'])

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_title('Risk Propagation: Entities ← Risks',
                    fontsize=16, fontweight='bold', pad=20)

        # Bipartite layout
        entity_nodes = [n for n, d in G.nodes(data=True) if d['node_type'] == 'entity']
        risk_nodes = [n for n, d in G.nodes(data=True) if d['node_type'] == 'risk']

        pos = {}
        for i, node in enumerate(entity_nodes):
            pos[node] = (0, i * 2)
        for i, node in enumerate(risk_nodes):
            pos[node] = (3, i * 1.5)

        # Draw edges
        edge_widths = [G[u][v].get('score', 0.5) * 5 for u, v in G.edges()]
        nx.draw_networkx_edges(G, pos, ax=ax,
                              width=edge_widths,
                              edge_color='#e74c3c',
                              alpha=0.4)

        # Draw entity nodes
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              nodelist=entity_nodes,
                              node_color=self.colors['entity'],
                              node_size=2500,
                              alpha=0.9,
                              label='Entities')

        # Draw risk nodes with size based on score
        risk_sizes = [1000 + G.nodes[n]['score'] * 2000 for n in risk_nodes]
        nx.draw_networkx_nodes(G, pos, ax=ax,
                              nodelist=risk_nodes,
                              node_color=self.colors['risk'],
                              node_size=risk_sizes,
                              alpha=0.9,
                              label='Risks')

        # Draw labels
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=9,
                               font_weight='bold')

        ax.legend(loc='upper right')
        ax.axis('off')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved to {save_path}")

        return fig


if __name__ == "__main__":
    # Test the visualizer
    viz = ThreeLayerVisualizer()

    print("Creating three-layer graph...")
    viz.create_three_layer_graph(limit_events=15,
                                 save_path='results/three_layer_graph.png')

    print("\nCreating evolution network...")
    viz.create_evolution_network(min_score=0.5,
                                 save_path='results/evolution_network.png')

    print("\nCreating risk propagation view...")
    viz.create_risk_propagation_view(save_path='results/risk_propagation.png')

    viz.close()

    print("\n✅ Visualizations created!")
    plt.show()
