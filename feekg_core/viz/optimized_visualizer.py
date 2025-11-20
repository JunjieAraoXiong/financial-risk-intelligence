"""
Optimized Knowledge Graph Visualizations with CSV Traceability
Clean, professional D3.js visualizations leveraging full data provenance
"""

import sys
import os
import json
import re
from typing import Optional, Dict, List
from collections import defaultdict, Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection
from feekg_core.evolution.event_evolution_scorer import compute_event_evolution_links


def clean_rdf_literal(value):
    """Remove RDF datatype annotations and quotes from literals"""
    if not value:
        return ''

    # Convert to string
    s = str(value).strip()

    # Remove RDF datatype annotation (e.g., "value"^^<http://...>)
    if '^^' in s:
        s = s.split('^^')[0]

    # Remove quotes
    s = s.strip(' "\'')

    # Handle None/null values
    if s in ['None', 'null', 'undefined']:
        return ''

    return s


class OptimizedVisualizer:
    """Generate optimized, professional visualizations with data quality"""

    def __init__(self):
        """Initialize with AllegroGraph connection"""
        self.backend = get_connection()

    def close(self):
        """Close database connection"""
        self.backend.close()

    def fetch_clean_graph_data(self, max_events: int = 150) -> Dict:
        """
        Fetch clean, validated graph data with CSV provenance

        Args:
            max_events: Maximum events to include

        Returns:
            Dictionary with clean nodes and links
        """
        print(f"Fetching clean data (max {max_events} events with provenance)...")

        # Fetch entities with clean labels
        entity_query = """
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?entity ?label ?type
        WHERE {
          ?entity a feekg:Entity .
          ?entity rdfs:label ?label .
          ?entity feekg:entityType ?type .
        }
        ORDER BY ?label
        """
        entities = self.backend.execute_query(entity_query)

        # Clean and deduplicate entities
        entity_nodes = {}
        for e in entities:
            label = clean_rdf_literal(e.get('label', ''))
            if not label:
                continue

            entity_type = clean_rdf_literal(e.get('type', 'unknown')).lower()

            if label not in entity_nodes:
                entity_nodes[label] = {
                    'id': label,
                    'label': label,
                    'type': entity_type,
                    'group': 'entity',
                    'uri': e['entity']
                }

        print(f"  ✓ Loaded {len(entity_nodes)} clean entities")

        # Fetch events with CSV metadata - prioritize events involving our entities
        event_query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?event ?label ?type ?date ?desc
               ?csvRow ?csvFile ?confidence ?method
        WHERE {{
          ?event a feekg:Event .
          ?event feekg:involves ?entity .
          OPTIONAL {{ ?event rdfs:label ?label }}
          OPTIONAL {{ ?event feekg:eventType ?type }}
          OPTIONAL {{ ?event feekg:date ?date }}
          OPTIONAL {{ ?event feekg:description ?desc }}
          OPTIONAL {{ ?event feekg:csvRowNumber ?csvRow }}
          OPTIONAL {{ ?event feekg:csvFilename ?csvFile }}
          OPTIONAL {{ ?event feekg:classificationConfidence ?confidence }}
          OPTIONAL {{ ?event feekg:classificationMethod ?method }}
        }}
        ORDER BY ?date
        LIMIT {max_events}
        """
        events = self.backend.execute_query(event_query)

        event_nodes = {}
        event_uri_to_id = {}

        for i, e in enumerate(events):
            event_id = f"evt_{i}"
            label = (clean_rdf_literal(e.get('label')) or f"Event {i}")[:50]
            event_type = clean_rdf_literal(e.get('type')) or 'unknown'
            date = clean_rdf_literal(e.get('date')) or 'unknown'
            desc = clean_rdf_literal(e.get('desc'))[:200] if clean_rdf_literal(e.get('desc')) else ''

            # CSV metadata - clean ALL RDF annotations
            csv_row = clean_rdf_literal(e.get('csvRow'))
            csv_file = clean_rdf_literal(e.get('csvFile'))
            confidence = clean_rdf_literal(e.get('confidence'))
            method = clean_rdf_literal(e.get('method'))

            event_nodes[event_id] = {
                'id': event_id,
                'label': label,
                'type': event_type,
                'date': date,
                'description': desc,
                'group': 'event',
                'uri': e['event'],
                # Provenance metadata
                'csvRow': csv_row,
                'csvFile': csv_file,
                'confidence': confidence,
                'method': method
            }
            event_uri_to_id[e['event']] = event_id

        print(f"  ✓ Loaded {len(event_nodes)} events with provenance")

        # Fetch relationships
        links = []

        # Event → Entity (involves/hasTarget) - fetch ALL for our events
        # Distinguish between "involves" and "hasTarget" based on event type
        involves_query = """
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?event ?entity ?entityLabel ?eventType
        WHERE {
          ?event feekg:involves ?entity .
          ?entity rdfs:label ?entityLabel .
          ?event feekg:eventType ?eventType .
        }
        LIMIT 2000
        """

        # Event types where "involves" means "target" (affected entity)
        target_event_types = {
            'merger_acquisition', 'legal_issue', 'credit_downgrade',
            'bankruptcy', 'restructuring', 'government_intervention'
        }

        try:
            involves = self.backend.execute_query(involves_query)
            involves_count = 0
            target_count = 0
            for rel in involves:
                event_uri = rel['event']
                entity_label = clean_rdf_literal(rel.get('entityLabel'))
                event_type = clean_rdf_literal(rel.get('eventType'))

                if event_uri in event_uri_to_id and entity_label in entity_nodes:
                    # Determine relationship type based on event type
                    rel_type = 'hasTarget' if event_type in target_event_types else 'involves'

                    links.append({
                        'source': event_uri_to_id[event_uri],
                        'target': entity_label,
                        'type': rel_type,
                        'strength': 0.9 if rel_type == 'hasTarget' else 0.7
                    })

                    if rel_type == 'hasTarget':
                        target_count += 1
                    else:
                        involves_count += 1

            print(f"  ✓ Loaded {involves_count} 'involves' + {target_count} 'hasTarget' relationships")
        except Exception as e:
            print(f"  ⚠ 'involves/hasTarget' relationship loading: {str(e)[:100]}")

        # Event → Entity (actor) - stored as literal, need to match to entities
        actor_query = """
        PREFIX feekg: <http://feekg.org/ontology#>

        SELECT ?event ?actor
        WHERE {
          ?event a feekg:Event .
          ?event feekg:actor ?actor .
        }
        LIMIT 2000
        """

        try:
            actors = self.backend.execute_query(actor_query)
            actor_count = 0
            for rel in actors:
                event_uri = rel['event']
                actor_name = clean_rdf_literal(rel.get('actor'))

                if event_uri not in event_uri_to_id:
                    continue

                # Try fuzzy matching to handle corporate suffixes
                matched_entity = None

                # 1. Exact match
                if actor_name in entity_nodes:
                    matched_entity = actor_name
                else:
                    # 2. Check if any entity name is a substring of actor name
                    # e.g., "American International Group" matches "American International Group, Inc."
                    for entity_label in entity_nodes.keys():
                        if entity_label in actor_name or actor_name in entity_label:
                            matched_entity = entity_label
                            break

                if matched_entity:
                    links.append({
                        'source': event_uri_to_id[event_uri],
                        'target': matched_entity,
                        'type': 'hasActor',
                        'strength': 1.0
                    })
                    actor_count += 1

            print(f"  ✓ Loaded {actor_count} 'hasActor' relationships")
        except Exception as e:
            print(f"  ⚠ 'hasActor' relationship loading: {str(e)[:100]}")

        # Entity ↔ Entity (co-occurrence / relatedTo)
        # Connect entities that appear together in events
        entity_events = defaultdict(list)  # entity -> list of (event_id, event_type)
        for link in links:
            if link['target'] in entity_nodes:  # target is an entity
                event_id = link['source']
                # Get event type from event_nodes
                event_type = event_nodes.get(event_id, {}).get('type', 'unknown')
                entity_events[link['target']].append((event_id, event_type))

        # Create entity-entity links based on co-occurrence
        entity_list = list(entity_events.keys())
        entity_link_count = 0
        for i, entity1 in enumerate(entity_list):
            for entity2 in entity_list[i+1:]:
                # Find shared events
                events1 = set(ev[0] for ev in entity_events[entity1])
                events2 = set(ev[0] for ev in entity_events[entity2])
                shared_events = events1 & events2

                # Create link if they share at least 2 events
                if len(shared_events) >= 2:
                    links.append({
                        'source': entity1,
                        'target': entity2,
                        'type': 'relatedTo',
                        'strength': 0.5,
                        'shared_events': len(shared_events)
                    })
                    entity_link_count += 1

        print(f"  ✓ Created {entity_link_count} entity 'relatedTo' relationships")

        # Compute Event Evolution Links (evolvesTo)
        # Prepare event data with associated entities for evolution scoring
        print("\nComputing event evolution links...")
        event_list_for_evolution = []
        for event_id, event_data in event_nodes.items():
            # Collect entities associated with this event
            associated_entities = []
            for link in links:
                if link['source'] == event_id and link['target'] in entity_nodes:
                    associated_entities.append(link['target'])

            event_list_for_evolution.append({
                'id': event_id,
                'date': event_data.get('date', ''),
                'type': event_data.get('type', 'unknown'),
                'description': event_data.get('description', ''),
                'label': event_data.get('label', ''),
                'entities': associated_entities
            })

        # Compute evolution links with minimum score threshold
        # Using higher threshold (0.5) to reduce link count for visualization
        # Paper uses 0.2, but that's too many for interactive display
        evolution_links = compute_event_evolution_links(
            event_list_for_evolution,
            min_score=0.5,  # Higher threshold for cleaner visualization
            max_time_window_days=180  # 6 months window (shorter for more relevance)
        )

        # Add evolution links to main links list
        links.extend(evolution_links)
        print(f"  ✓ Total relationships: {len(links)} (including {len(evolution_links)} evolution links)")

        # Calculate statistics
        entity_type_counts = Counter(n['type'] for n in entity_nodes.values())
        event_type_counts = Counter(n['type'] for n in event_nodes.values())

        all_nodes = list(entity_nodes.values()) + list(event_nodes.values())

        return {
            'nodes': all_nodes,
            'links': links,
            'stats': {
                'entities': len(entity_nodes),
                'events': len(event_nodes),
                'relationships': len(links),
                'entityTypes': dict(entity_type_counts),
                'eventTypes': dict(event_type_counts)
            }
        }

    def create_optimized_visualization(self,
                                       max_events: int = 100,
                                       save_path: Optional[str] = None) -> str:
        """
        Create optimized D3.js visualization with CSV provenance

        Args:
            max_events: Maximum events to visualize
            save_path: Path to save HTML file

        Returns:
            Path to generated file
        """
        if save_path is None:
            save_path = "results/optimized_knowledge_graph.html"

        # Fetch clean data
        data = self.fetch_clean_graph_data(max_events)

        # Generate HTML
        html_content = self._generate_optimized_html(data)

        # Save
        with open(save_path, 'w') as f:
            f.write(html_content)

        print(f"\n✅ Optimized visualization created!")
        print(f"📊 Stats: {data['stats']['entities']} entities, {data['stats']['events']} events, {data['stats']['relationships']} links")
        print(f"📂 Open: file://{os.path.abspath(save_path)}")

        return save_path

    def _generate_optimized_html(self, data: Dict) -> str:
        """Generate optimized HTML with modern UI"""

        graph_json = json.dumps(data, indent=2)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Event Knowledge Graph - Optimized</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
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
            background: rgba(255, 255, 255, 0.98);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            min-width: 320px;
            max-height: 90vh;
            overflow-y: auto;
        }}

        .controls h1 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .controls .subtitle {{
            font-size: 13px;
            color: #666;
            margin-bottom: 20px;
        }}

        .stats {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }}

        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
            font-size: 13px;
            color: #333;
        }}

        .stat-row:last-child {{
            border-bottom: none;
        }}

        .stat-value {{
            font-weight: 600;
            color: #667eea;
        }}

        .control-section {{
            margin-bottom: 20px;
        }}

        .control-section h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 12px;
        }}

        .controls button {{
            width: 100%;
            padding: 12px;
            margin: 6px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .controls button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}

        .controls button:active {{
            transform: translateY(0);
        }}

        .controls button.secondary {{
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }}

        .search-box {{
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 13px;
            transition: border-color 0.2s;
        }}

        .search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .legend {{
            margin-top: 20px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 10px 0;
            font-size: 13px;
            color: #333;
        }}

        .legend-color {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            margin-right: 12px;
            border: 2px solid rgba(0, 0, 0, 0.1);
        }}

        .legend-line {{
            width: 30px;
            height: 3px;
            margin-right: 10px;
            border-radius: 2px;
        }}

        .tooltip {{
            position: fixed;
            background: rgba(255, 255, 255, 0.98);
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 16px;
            font-size: 13px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 2000;
            max-width: 400px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            color: #333;
        }}

        .tooltip.show {{
            opacity: 1;
        }}

        .tooltip strong {{
            color: #667eea;
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
        }}

        .tooltip .meta {{
            color: #666;
            font-size: 11px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #e9ecef;
        }}

        .tooltip .provenance {{
            background: #f8f9fa;
            padding: 8px;
            border-radius: 6px;
            margin-top: 8px;
            font-size: 11px;
        }}

        .node {{
            cursor: pointer;
            transition: all 0.2s;
        }}

        .node:hover {{
            stroke-width: 4px !important;
        }}

        .node.highlighted {{
            stroke: #ffd700 !important;
            stroke-width: 5px !important;
        }}

        .link {{
            stroke-opacity: 0.4;
            transition: stroke-opacity 0.2s;
        }}

        .link.highlight {{
            stroke-opacity: 0.9;
            stroke-width: 3px;
            stroke: #667eea;
        }}

        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 32px 48px;
            border-radius: 16px;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
            z-index: 3000;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="controls">
        <h1>📊 FE-EKG Knowledge Graph</h1>
        <div class="subtitle">Financial Event Evolution with CSV Provenance</div>

        <div class="stats">
            <div class="stat-row">
                <span>Entities</span>
                <span class="stat-value" id="entityCount">0</span>
            </div>
            <div class="stat-row">
                <span>Events</span>
                <span class="stat-value" id="eventCount">0</span>
            </div>
            <div class="stat-row">
                <span>Relationships</span>
                <span class="stat-value" id="linkCount">0</span>
            </div>
        </div>

        <div class="control-section">
            <h3>🔍 Search</h3>
            <input type="text" class="search-box" id="search" placeholder="Search entities or events...">
        </div>

        <div class="control-section">
            <h3>🎮 Controls</h3>
            <button onclick="resetView()">Reset View</button>
            <button onclick="togglePhysics()" class="secondary">Toggle Physics</button>
            <button onclick="centerOnEntity()" class="secondary">Center on Entity</button>
        </div>

        <div class="legend">
            <h3 style="font-size: 14px; color: #333; margin-bottom: 12px;">Node Types</h3>
            <div class="legend-item">
                <div class="legend-color" style="background: #3b82f6;"></div>
                <span>Banks & Financial Institutions</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #8b5cf6;"></div>
                <span>Regulators & Government</span>
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

        <div class="legend">
            <h3 style="font-size: 14px; color: #333; margin-bottom: 12px;">Relationship Types</h3>
            <div class="legend-item">
                <div class="legend-line" style="background: #10b981;"></div>
                <span style="font-size: 11px;"><strong>hasActor</strong> - performs action</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #ef4444;"></div>
                <span style="font-size: 11px;"><strong>hasTarget</strong> - affected/targeted</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #3b82f6;"></div>
                <span style="font-size: 11px;"><strong>involves</strong> - related to</span>
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #a855f7;"></div>
                <span style="font-size: 11px;"><strong>relatedTo</strong> - co-occurs</span>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>
    <svg id="graph"></svg>

    <script>
        // Graph data with CSV provenance
        const graphData = {graph_json};

        // Setup
        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select('#graph')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});

        svg.call(zoom);

        // Color mapping
        const colorMap = {{
            'bank': '#3b82f6',
            'regulator': '#8b5cf6',
            'investment_bank': '#ec4899',
            'company': '#10b981',
            'ratingagency': '#f59e0b',
            'insurance': '#06b6d4',
            'person': '#f97316',
            'exchange': '#6366f1',
            'unknown': '#94a3b8',
            'event': '#f59e0b'
        }};

        function getNodeColor(d) {{
            if (d.group === 'entity') {{
                return colorMap[d.type] || colorMap['unknown'];
            }}
            return colorMap['event'];
        }}

        function getNodeSize(d) {{
            return d.group === 'entity' ? 14 : 9;
        }}

        // Force simulation
        let physicsEnabled = true;
        const simulation = d3.forceSimulation(graphData.nodes)
            .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(120).strength(d => d.strength || 0.6))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 10));

        // Relationship type color mapping
        const relationshipColors = {{
            'hasActor': '#10b981',      // Green - entity performs action
            'hasTarget': '#ef4444',     // Red - entity is affected/targeted
            'involves': '#3b82f6',      // Blue - entity is involved/related
            'relatedTo': '#a855f7',     // Purple - entities are connected
            'evolvesTo': '#f59e0b'      // Orange - event evolution (future)
        }};

        function getLinkColor(d) {{
            return relationshipColors[d.type] || '#64748b';  // Default gray
        }}

        // Draw links
        const link = g.append('g')
            .selectAll('line')
            .data(graphData.links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke', getLinkColor)
            .attr('stroke-width', d => d.strength * 2)
            .attr('opacity', 0.6);

        // Draw link labels
        const linkLabels = g.append('g')
            .selectAll('text')
            .data(graphData.links)
            .join('text')
            .attr('class', 'link-label')
            .attr('font-size', 9)
            .attr('fill', '#94a3b8')
            .attr('text-anchor', 'middle')
            .attr('dy', -3)
            .style('pointer-events', 'none')
            .style('text-shadow', '0 0 3px rgba(0,0,0,0.8)')
            .text(d => d.type || 'related');

        // Draw nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(graphData.nodes)
            .join('circle')
            .attr('class', 'node')
            .attr('r', getNodeSize)
            .attr('fill', getNodeColor)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended))
            .on('mouseover', showTooltip)
            .on('mouseout', hideTooltip)
            .on('click', nodeClicked);

        // Labels for entities only
        const labels = g.append('g')
            .selectAll('text')
            .data(graphData.nodes.filter(d => d.group === 'entity'))
            .join('text')
            .text(d => d.label)
            .attr('font-size', 11)
            .attr('font-weight', 600)
            .attr('fill', '#fff')
            .attr('text-anchor', 'middle')
            .attr('dy', -18)
            .style('pointer-events', 'none')
            .style('text-shadow', '0 1px 3px rgba(0,0,0,0.5)');

        // Update positions on tick
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

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

            if (d.date && d.date !== 'unknown') {{
                html += `<div class="meta">Date: ${{d.date}}</div>`;
            }}

            if (d.description) {{
                html += `<div style="margin-top: 8px; font-size: 12px; line-height: 1.5;">${{d.description}}</div>`;
            }}

            // CSV Provenance
            if (d.csvRow && d.csvRow !== 'None') {{
                html += `<div class="provenance">`;
                html += `<strong style="font-size: 11px;">📄 Data Source</strong><br>`;
                html += `Row: ${{d.csvRow}}<br>`;
                if (d.confidence) html += `Confidence: ${{(parseFloat(d.confidence) * 100).toFixed(1)}}%<br>`;
                if (d.method) html += `Method: ${{d.method}}`;
                html += `</div>`;
            }}

            tooltip
                .html(html)
                .style('left', (event.pageX + 15) + 'px')
                .style('top', (event.pageY - 15) + 'px')
                .classed('show', true);

            // Highlight connected links
            link.classed('highlight', l => l.source === d || l.target === d);
            node.classed('highlighted', n => n === d);
        }}

        function hideTooltip() {{
            tooltip.classed('show', false);
            link.classed('highlight', false);
            node.classed('highlighted', false);
        }}

        function nodeClicked(event, d) {{
            console.log('Node clicked:', d);
            // Could add more interaction here
        }}

        // Controls
        function resetView() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
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

        function centerOnEntity() {{
            const lehman = graphData.nodes.find(n => n.label.includes('Lehman'));
            if (lehman) {{
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity
                        .translate(width/2, height/2)
                        .scale(1.5)
                        .translate(-lehman.x, -lehman.y)
                );
            }}
        }}

        // Search functionality
        document.getElementById('search').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();

            node.attr('opacity', d => {{
                if (!searchTerm) return 1;
                return d.label.toLowerCase().includes(searchTerm) ? 1 : 0.2;
            }});

            labels.attr('opacity', d => {{
                if (!searchTerm) return 1;
                return d.label.toLowerCase().includes(searchTerm) ? 1 : 0.2;
            }});
        }});

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

            const scale = 0.9 / Math.max(fullWidth / width, fullHeight / height);
            const translate = [width / 2 - scale * midX, height / 2 - scale * midY];

            svg.call(zoom.transform, d3.zoomIdentity
                .translate(translate[0], translate[1])
                .scale(scale));
        }}, 1000);
    </script>
</body>
</html>"""


if __name__ == "__main__":
    viz = OptimizedVisualizer()

    print("=" * 70)
    print("Creating Optimized Knowledge Graph Visualization")
    print("=" * 70)
    print()

    viz.create_optimized_visualization(
        max_events=100,
        save_path="results/optimized_knowledge_graph.html"
    )

    viz.close()

    print()
    print("=" * 70)
    print("✅ Done! Open in browser:")
    print("   results/optimized_knowledge_graph.html")
    print("=" * 70)
