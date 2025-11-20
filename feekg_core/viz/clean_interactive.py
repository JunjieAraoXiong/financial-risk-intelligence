"""
Clean, optimized D3.js visualizations for FE-EKG
Professional design with performance optimizations
"""

import sys
import os
import json
from typing import Optional, Dict, List
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class CleanVisualizer:
    """Generate clean, efficient D3.js visualizations"""

    def __init__(self):
        """Initialize with AllegroGraph connection"""
        self.backend = get_connection()

    def close(self):
        """Close database connection"""
        self.backend.close()

    def fetch_optimized_graph_data(self, max_events: int = 100) -> Dict:
        """
        Fetch graph data efficiently with smart sampling

        Args:
            max_events: Maximum events to include

        Returns:
            Dictionary with nodes and links optimized for D3.js
        """
        print(f"Fetching optimized data (max {max_events} events)...")

        # Fetch all entities (usually small number)
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

        # Normalize entity types
        entity_nodes = {}
        for e in entities:
            label = e.get('label', 'Unknown')
            entity_type = e.get('type', 'unknown').lower()

            if label not in entity_nodes:
                entity_nodes[label] = {
                    'id': label,
                    'label': label,
                    'type': entity_type,
                    'group': 'entity',
                    'uri': e['entity']
                }

        print(f"  ✓ Loaded {len(entity_nodes)} entities")

        # Fetch sample of events with temporal distribution
        # Use DISTINCT and ORDER BY date for representative sample
        event_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?event ?label ?type ?date ?desc
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
        event_uri_to_id = {}
        for i, e in enumerate(events):
            event_id = f"evt_{i}"
            label = (e.get('label') or f"Event {i}")[:40]
            event_type = e.get('type') or 'unknown'
            date = e.get('date') or 'unknown'
            desc = (e.get('desc') or '')[:150]

            event_nodes[event_id] = {
                'id': event_id,
                'label': label,
                'type': event_type,
                'date': date,
                'description': desc,
                'group': 'event',
                'uri': e['event']
            }
            event_uri_to_id[e['event']] = event_id

        print(f"  ✓ Loaded {len(event_nodes)} events")

        # Fetch relationships efficiently
        # Only fetch relationships for the sampled events
        event_uris = [e['event'] for e in events]

        links = []

        # Event -> Entity (actor) relationships
        if event_uris:
            # Use simpler approach: get all actor relationships, then filter
            actor_query = """
            PREFIX feekg: <http://feekg.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?event ?actor ?actorLabel
            WHERE {
              ?event feekg:actor ?actor .
              ?actor rdfs:label ?actorLabel .
            }
            LIMIT 500
            """

            try:
                actors = self.backend.execute_query(actor_query)
                # Filter to only our sampled events
                filtered_actors = []
                for rel in actors:
                    event_uri = rel['event']
                    actor_label = rel['actorLabel']

                    if event_uri in event_uri_to_id and actor_label in entity_nodes:
                        links.append({
                            'source': event_uri_to_id[event_uri],
                            'target': actor_label,
                            'type': 'actor',
                            'strength': 1.0
                        })
                        filtered_actors.append(rel)
                print(f"  ✓ Loaded {len(filtered_actors)} actor relationships")
            except Exception as e:
                print(f"  ⚠ Actor relationships: {str(e)[:100]}")

        # Event -> Entity (involves) relationships
        if event_uris:
            # Use simpler approach: get all involvement relationships, then filter
            involves_query = """
            PREFIX feekg: <http://feekg.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?event ?entity ?entityLabel
            WHERE {
              ?event feekg:involves ?entity .
              ?entity rdfs:label ?entityLabel .
            }
            LIMIT 500
            """

            try:
                involves = self.backend.execute_query(involves_query)
                # Filter to only our sampled events
                filtered_involves = []
                for rel in involves:
                    event_uri = rel['event']
                    entity_label = rel['entityLabel']

                    if event_uri in event_uri_to_id and entity_label in entity_nodes:
                        links.append({
                            'source': event_uri_to_id[event_uri],
                            'target': entity_label,
                            'type': 'involves',
                            'strength': 0.7
                        })
                        filtered_involves.append(rel)
                print(f"  ✓ Loaded {len(filtered_involves)} involvement relationships")
            except Exception as e:
                print(f"  ⚠ Involvement relationships: {str(e)[:100]}")

        # Combine all nodes
        all_nodes = list(entity_nodes.values()) + list(event_nodes.values())

        return {
            'nodes': all_nodes,
            'links': links,
            'stats': {
                'entities': len(entity_nodes),
                'events': len(event_nodes),
                'relationships': len(links)
            }
        }

    def create_clean_interactive(self,
                                 max_events: int = 100,
                                 save_path: Optional[str] = None) -> str:
        """
        Create clean, professional D3.js force-directed graph

        Args:
            max_events: Maximum events to visualize
            save_path: Path to save HTML file

        Returns:
            Path to generated HTML file
        """
        if save_path is None:
            save_path = "results/clean_knowledge_graph.html"

        # Fetch data
        data = self.fetch_optimized_graph_data(max_events)

        # Generate HTML with embedded D3.js visualization
        html_content = self._generate_d3_html(data)

        # Save
        with open(save_path, 'w') as f:
            f.write(html_content)

        print(f"\n✅ Clean interactive visualization created!")
        print(f"📊 {data['stats']['entities']} entities, {data['stats']['events']} events, {data['stats']['relationships']} links")
        print(f"📂 Open: file://{os.path.abspath(save_path)}")

        return save_path

    def _generate_d3_html(self, data: Dict) -> str:
        """Generate clean D3.js HTML"""

        # Convert data to JSON
        graph_json = json.dumps(data, indent=2)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Event Knowledge Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f0f1e;
            color: #fff;
            overflow: hidden;
        }}

        #graph {{
            width: 100vw;
            height: 100vh;
        }}

        .controls {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(20, 20, 40, 0.95);
            border: 1px solid rgba(100, 100, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            z-index: 1000;
            min-width: 280px;
        }}

        .controls h1 {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .controls .stats {{
            font-size: 12px;
            color: #888;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(100, 100, 255, 0.2);
        }}

        .controls button {{
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            background: rgba(100, 100, 255, 0.2);
            border: 1px solid rgba(100, 100, 255, 0.4);
            border-radius: 6px;
            color: #fff;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .controls button:hover {{
            background: rgba(100, 100, 255, 0.3);
            border-color: rgba(100, 100, 255, 0.6);
        }}

        .legend {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(100, 100, 255, 0.2);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 12px;
        }}

        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }}

        .tooltip {{
            position: fixed;
            background: rgba(20, 20, 40, 0.98);
            border: 1px solid rgba(100, 100, 255, 0.5);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 13px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 2000;
            max-width: 300px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6);
        }}

        .tooltip.show {{
            opacity: 1;
        }}

        .tooltip strong {{
            color: #667eea;
            display: block;
            margin-bottom: 6px;
        }}

        .tooltip .meta {{
            color: #888;
            font-size: 11px;
            margin-top: 6px;
        }}

        .node {{
            cursor: pointer;
            transition: all 0.2s;
        }}

        .node:hover {{
            stroke-width: 3px !important;
        }}

        .link {{
            stroke-opacity: 0.3;
            transition: stroke-opacity 0.2s;
        }}

        .link.highlight {{
            stroke-opacity: 0.8;
            stroke-width: 2px;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <h1>Financial Event KG</h1>
        <div class="stats">
            <div>Entities: <strong id="entityCount">0</strong></div>
            <div>Events: <strong id="eventCount">0</strong></div>
            <div>Links: <strong id="linkCount">0</strong></div>
        </div>
        <button onclick="resetView()">Reset View</button>
        <button onclick="togglePhysics()">Toggle Physics</button>
        <button onclick="exportData()">Export Data</button>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #3b82f6;"></div>
                <span>Banks</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #8b5cf6;"></div>
                <span>Regulators</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ec4899;"></div>
                <span>Investment Banks</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f59e0b;"></div>
                <span>Events</span>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>
    <svg id="graph"></svg>

    <script>
        // Graph data
        const graphData = {graph_json};

        // Setup
        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select('#graph')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Zoom
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});

        svg.call(zoom);

        // Color scale
        const colorMap = {{
            'bank': '#3b82f6',
            'regulator': '#8b5cf6',
            'investment_bank': '#ec4899',
            'company': '#10b981',
            'ratingagency': '#f59e0b',
            'insurance': '#06b6d4',
            'person': '#f97316',
            'exchange': '#6366f1',
            'unknown': '#6b7280',
            'event': '#f59e0b'
        }};

        function getNodeColor(d) {{
            if (d.group === 'entity') {{
                return colorMap[d.type.toLowerCase()] || colorMap['unknown'];
            }}
            return colorMap['event'];
        }}

        function getNodeSize(d) {{
            return d.group === 'entity' ? 12 : 8;
        }}

        // Force simulation
        let physicsEnabled = true;
        const simulation = d3.forceSimulation(graphData.nodes)
            .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100).strength(d => d.strength || 0.5))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 5));

        // Links
        const link = g.append('g')
            .selectAll('line')
            .data(graphData.links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke', '#4b5563')
            .attr('stroke-width', 1);

        // Nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(graphData.nodes)
            .join('circle')
            .attr('class', 'node')
            .attr('r', getNodeSize)
            .attr('fill', getNodeColor)
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended))
            .on('mouseover', showTooltip)
            .on('mouseout', hideTooltip)
            .on('click', nodeClicked);

        // Labels (only for entities)
        const labels = g.append('g')
            .selectAll('text')
            .data(graphData.nodes.filter(d => d.group === 'entity'))
            .join('text')
            .text(d => d.label)
            .attr('font-size', 10)
            .attr('fill', '#fff')
            .attr('text-anchor', 'middle')
            .attr('dy', -15)
            .style('pointer-events', 'none')
            .style('user-select', 'none');

        // Update positions
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }});

        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Tooltip
        const tooltip = d3.select('#tooltip');

        function showTooltip(event, d) {{
            let html = `<strong>${{d.label}}</strong>`;
            html += `<div class="meta">Type: ${{d.type}}</div>`;
            if (d.date) html += `<div class="meta">Date: ${{d.date}}</div>`;
            if (d.description) html += `<div style="margin-top: 8px; font-size: 12px;">${{d.description}}</div>`;

            tooltip
                .html(html)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .classed('show', true);

            // Highlight connected links
            link.classed('highlight', l => l.source === d || l.target === d);
        }}

        function hideTooltip() {{
            tooltip.classed('show', false);
            link.classed('highlight', false);
        }}

        function nodeClicked(event, d) {{
            console.log('Node clicked:', d);
        }}

        // Controls
        function resetView() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );
        }}

        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (physicsEnabled) {{
                simulation.alpha(1).restart();
            }} else {{
                simulation.stop();
            }}
        }}

        function exportData() {{
            const dataStr = JSON.stringify(graphData, null, 2);
            const blob = new Blob([dataStr], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'knowledge_graph_data.json';
            a.click();
        }}

        // Update stats
        document.getElementById('entityCount').textContent = graphData.stats.entities;
        document.getElementById('eventCount').textContent = graphData.stats.events;
        document.getElementById('linkCount').textContent = graphData.stats.relationships;

        // Initial zoom to fit
        setTimeout(() => {{
            const bounds = g.node().getBBox();
            const fullWidth = bounds.width;
            const fullHeight = bounds.height;
            const midX = bounds.x + fullWidth / 2;
            const midY = bounds.y + fullHeight / 2;

            const scale = 0.8 / Math.max(fullWidth / width, fullHeight / height);
            const translate = [width / 2 - scale * midX, height / 2 - scale * midY];

            svg.call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}, 1000);
    </script>
</body>
</html>"""

if __name__ == "__main__":
    viz = CleanVisualizer()

    print("=" * 70)
    print("Creating Clean, Optimized Knowledge Graph Visualization")
    print("=" * 70)
    print()

    # Create optimized visualization with 100 events
    viz.create_clean_interactive(
        max_events=100,
        save_path="results/clean_knowledge_graph.html"
    )

    viz.close()

    print()
    print("=" * 70)
    print("✅ Done! Open in browser:")
    print("   results/clean_knowledge_graph.html")
    print("=" * 70)
