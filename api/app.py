"""
FE-EKG REST API Application

Flask REST API for serving knowledge graph data and visualizations
"""

import sys
import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from query.risk_analyzer import RiskAnalyzer
from query.optimized_graph_queries import OptimizedGraphBackend
from viz.graph_viz import ThreeLayerVisualizer
from viz.plot_utils import (plot_risk_timeline, plot_evolution_heatmap,
                            plot_event_network, plot_component_breakdown,
                            plot_risk_distribution)


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend access

    # ==========================================================================
    # STATIC FILE ROUTES
    # ==========================================================================

    @app.route('/')
    def index():
        """Serve timeline visualization by default"""
        return send_file('timeline.html')

    @app.route('/timeline.html')
    def timeline():
        """Serve timeline visualization"""
        return send_file('timeline.html')

    @app.route('/demo.html')
    def demo():
        """Serve API demo page"""
        return send_file('demo.html')

    @app.route('/triple_example.html')
    def triple_example():
        """Serve triple conversion example"""
        return send_file('triple_example.html')

    @app.route('/docs_hub.html')
    def docs_hub():
        """Serve documentation hub"""
        import os
        docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs_hub.html')
        return send_file(docs_path)

    @app.route('/<path:filepath>')
    def serve_markdown(filepath):
        """Serve markdown files and other static files from project root"""
        import os
        # Only serve .md files and specific directories
        if filepath.endswith('.md') or filepath.startswith('docs/') or filepath.startswith('logs/') or filepath.startswith('api/') or filepath.startswith('data/') or filepath.startswith('evolution/'):
            file_path = os.path.join(os.path.dirname(__file__), '..', filepath)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
        return jsonify({'error': 'File not found'}), 404

    # ==========================================================================
    # HEALTH & INFO ENDPOINTS
    # ==========================================================================

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'FE-EKG API',
            'version': '1.0.0'
        })

    @app.route('/api/info', methods=['GET'])
    def info():
        """Get database information"""
        try:
            analyzer = RiskAnalyzer()
            overview = analyzer.get_database_overview()
            analyzer.close()

            return jsonify({
                'status': 'success',
                'data': overview
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get accurate graph statistics from AllegroGraph"""
        try:
            backend = OptimizedGraphBackend()
            stats = backend.get_graph_stats()

            return jsonify({
                'status': 'success',
                'data': stats
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # ENTITY ENDPOINTS
    # ==========================================================================

    @app.route('/api/entities', methods=['GET'])
    def get_entities():
        """Get all entities (using SPARQL)"""
        try:
            backend = OptimizedGraphBackend()
            entities = backend.get_all_entities()

            return jsonify({
                'status': 'success',
                'count': len(entities),
                'data': entities
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/entities/<entity_id>', methods=['GET'])
    def get_entity(entity_id):
        """Get specific entity details (using SPARQL)"""
        try:
            backend = OptimizedGraphBackend()
            entity = backend.get_entity_by_id(entity_id)

            if not entity:
                return jsonify({
                    'status': 'error',
                    'message': 'Entity not found'
                }), 404

            return jsonify({
                'status': 'success',
                'data': entity
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/entities/<entity_id>/risks', methods=['GET'])
    def get_entity_risks(entity_id):
        """Get risks for a specific entity"""
        try:
            analyzer = RiskAnalyzer()
            query = """
            MATCH (e:Entity {entityId: $entityId})
            MATCH (r:Risk)-[:TARGETS_ENTITY]->(e)
            MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
            RETURN r.riskId as id, rt.label as type, r.score as score,
                   r.severity as severity, r.status as status
            ORDER BY r.score DESC
            """
            risks = analyzer.backend.execute_query(query, {'entityId': entity_id})
            analyzer.close()

            return jsonify({
                'status': 'success',
                'count': len(risks),
                'data': risks
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # EVENT ENDPOINTS
    # ==========================================================================

    @app.route('/api/events', methods=['GET'])
    def get_events():
        """Get all events with optional filtering (using SPARQL)"""
        try:
            # Query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            offset = int(request.args.get('offset', 0))
            limit = int(request.args.get('limit', 100))

            backend = OptimizedGraphBackend()

            # Use time window filter if dates provided
            if start_date and end_date:
                events = backend.get_events_by_timewindow(start_date, end_date, limit=limit)
                # For time window queries, return count (no pagination info)
                return jsonify({
                    'status': 'success',
                    'count': len(events),
                    'data': events
                })
            else:
                # Use pagination for all events
                result = backend.get_events_paginated(offset=offset, limit=limit)

                # Return complete paginated response
                return jsonify({
                    'status': 'success',
                    'data': result['events'],
                    'total': result['total'],
                    'offset': result['offset'],
                    'limit': result['limit'],
                    'count': len(result['events'])
                })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/events/<event_id>', methods=['GET'])
    def get_event(event_id):
        """Get specific event details (using SPARQL)"""
        try:
            backend = OptimizedGraphBackend()
            event = backend.get_event_by_id(event_id)

            if not event:
                return jsonify({
                    'status': 'error',
                    'message': 'Event not found'
                }), 404

            return jsonify({
                'status': 'success',
                'data': event
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # EVOLUTION ENDPOINTS
    # ==========================================================================

    @app.route('/api/evolution/links', methods=['GET'])
    def get_evolution_links():
        """Get evolution links with optional filtering"""
        try:
            min_score = float(request.args.get('min_score', 0.0))
            limit = int(request.args.get('limit', 1000))
            event_id = request.args.get('event_id')  # Optional filter by event

            backend = OptimizedGraphBackend()
            all_links = backend.get_evolution_links(limit=limit, min_score=min_score)

            # Filter by event_id if provided
            if event_id:
                links = [link for link in all_links if link['from'] == event_id or link['to'] == event_id]
            else:
                links = all_links

            return jsonify({
                'status': 'success',
                'count': len(links),
                'data': links
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/evolution/chains', methods=['GET'])
    def get_causal_chains():
        """Get causal event chains"""
        try:
            min_causality = float(request.args.get('min_causality', 0.5))
            min_length = int(request.args.get('min_length', 2))
            max_length = int(request.args.get('max_length', 5))

            analyzer = RiskAnalyzer()
            chains = analyzer.get_causal_chains(
                min_causality=min_causality,
                min_length=min_length,
                max_length=max_length
            )
            analyzer.close()

            return jsonify({
                'status': 'success',
                'count': len(chains),
                'data': chains
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/evolution/stats', methods=['GET'])
    def get_evolution_stats():
        """Get evolution statistics"""
        try:
            analyzer = RiskAnalyzer()
            stats = analyzer.get_evolution_statistics()
            analyzer.close()

            return jsonify({
                'status': 'success',
                'data': stats
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # RISK ENDPOINTS
    # ==========================================================================

    @app.route('/api/risks', methods=['GET'])
    def get_risks():
        """Get all risks"""
        try:
            analyzer = RiskAnalyzer()
            query = """
            MATCH (r:Risk)-[:HAS_RISK_TYPE]->(rt:RiskType)
            MATCH (r)-[:TARGETS_ENTITY]->(e:Entity)
            RETURN r.riskId as id, rt.label as type, r.score as score,
                   r.severity as severity, r.status as status,
                   e.name as targetEntity
            ORDER BY r.score DESC
            """
            risks = analyzer.backend.execute_query(query)
            analyzer.close()

            return jsonify({
                'status': 'success',
                'count': len(risks),
                'data': risks
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/risks/systemic', methods=['GET'])
    def get_systemic_risks():
        """Get systemic/contagion risks"""
        try:
            analyzer = RiskAnalyzer()
            systemic = analyzer.detect_systemic_risk()
            analyzer.close()

            return jsonify({
                'status': 'success',
                'count': len(systemic),
                'data': systemic
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/risks/distribution', methods=['GET'])
    def get_risk_distribution():
        """Get risk distribution statistics"""
        try:
            analyzer = RiskAnalyzer()
            distribution = analyzer.get_risk_distribution()
            analyzer.close()

            return jsonify({
                'status': 'success',
                'data': distribution
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # VISUALIZATION ENDPOINTS
    # ==========================================================================

    @app.route('/api/visualizations/three-layer', methods=['GET'])
    def get_three_layer_viz():
        """Generate three-layer graph visualization"""
        try:
            limit_events = int(request.args.get('limit', 15))

            viz = ThreeLayerVisualizer()
            fig = viz.create_three_layer_graph(limit_events=limit_events)
            viz.close()

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/visualizations/evolution-network', methods=['GET'])
    def get_evolution_network():
        """Generate evolution network visualization"""
        try:
            min_score = float(request.args.get('min_score', 0.4))

            viz = ThreeLayerVisualizer()
            fig = viz.create_evolution_network(min_score=min_score)
            viz.close()

            if fig is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No evolution links found'
                }), 404

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/visualizations/risk-propagation', methods=['GET'])
    def get_risk_propagation():
        """Generate risk propagation visualization"""
        try:
            viz = ThreeLayerVisualizer()
            fig = viz.create_risk_propagation_view()
            viz.close()

            if fig is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No risk data found'
                }), 404

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/visualizations/risk-timeline', methods=['GET'])
    def get_risk_timeline():
        """Generate risk timeline plot"""
        try:
            entity_name = request.args.get('entity', 'China Evergrande Group')

            fig = plot_risk_timeline(entity_name=entity_name)

            if fig is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No timeline data found'
                }), 404

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/visualizations/evolution-heatmap', methods=['GET'])
    def get_evolution_heatmap():
        """Generate evolution heatmap"""
        try:
            fig = plot_evolution_heatmap()

            if fig is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No evolution data found'
                }), 404

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/visualizations/component-breakdown', methods=['GET'])
    def get_component_breakdown():
        """Generate component breakdown plot"""
        try:
            fig = plot_component_breakdown()

            if fig is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No statistics found'
                }), 404

            # Convert to base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

            return jsonify({
                'status': 'success',
                'image': f'data:image/png;base64,{img_base64}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ==========================================================================
    # GRAPH DATA ENDPOINTS (for D3.js/Cytoscape.js frontend)
    # ==========================================================================

    @app.route('/api/graph/data', methods=['GET'])
    def get_graph_data():
        """Get graph data in nodes/edges format for frontend visualization"""
        try:
            limit_events = int(request.args.get('limit', 500))
            min_score = float(request.args.get('min_score', 0.3))
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # Use OptimizedGraphBackend for SPARQL queries (works with AllegroGraph)
            backend = OptimizedGraphBackend()
            data = backend.get_graph_data_for_viz(
                limit_events=limit_events,
                min_evolution_score=min_score,
                start_date=start_date,
                end_date=end_date
            )

            # Transform to nodes/edges format
            nodes = []
            edges = []

            # Add entity nodes
            for entity in data['nodes']['entities']:
                nodes.append({
                    'id': entity['id'],
                    'label': entity['name'],
                    'type': 'entity',
                    'group': 'entity',
                    'data': entity
                })

            # Add event nodes
            for event in data['nodes']['events']:
                nodes.append({
                    'id': event['eventId'],
                    'label': event['label'],
                    'type': event['type'],
                    'group': 'event',
                    'data': event
                })

            # Add evolution edges (event → event)
            for edge in data['edges']['evolution']:
                edges.append({
                    'id': f"{edge['from']}-{edge['to']}",
                    'source': edge['from'],
                    'target': edge['to'],
                    'type': 'evolves_to',
                    'weight': edge['score'],
                    'data': edge
                })

            # Add event-entity edges
            for edge in data['edges']['event_entity']:
                edges.append({
                    'id': f"{edge['event']}-{edge['entity']}",
                    'source': edge['event'],
                    'target': edge['entity'],
                    'type': edge['type'],
                    'data': edge
                })

            return jsonify({
                'status': 'success',
                'nodes': nodes,
                'edges': edges,
                'stats': data['stats']
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/api/graph/timeline', methods=['GET'])
    def get_timeline_graph():
        """Get time-filtered graph data for timeline visualization"""
        try:
            end_date = request.args.get('end_date')  # Filter up to this date
            min_score = float(request.args.get('min_score', 0.3))

            if not end_date:
                return jsonify({
                    'status': 'error',
                    'message': 'end_date parameter required (format: YYYY-MM-DD)'
                }), 400

            analyzer = RiskAnalyzer()

            # Get events up to end_date
            events_query = """
            MATCH (e:Event)
            WHERE e.date <= date($endDate)
            OPTIONAL MATCH (e)-[:HAS_ACTOR]->(actor:Entity)
            OPTIONAL MATCH (e)-[:HAS_TARGET]->(target:Entity)
            RETURN e.eventId as id, e.type as type, toString(e.date) as date,
                   e.description as description, e.confidence as confidence,
                   actor.entityId as actorId, actor.name as actorName,
                   target.entityId as targetId, target.name as targetName
            ORDER BY e.date
            """
            events = analyzer.backend.execute_query(events_query, {'endDate': end_date})

            # Get evolution links between events up to end_date
            evolution_query = """
            MATCH (e1:Event)-[r:EVOLVES_TO]->(e2:Event)
            WHERE e1.date <= date($endDate) AND e2.date <= date($endDate)
              AND r.score >= $minScore
            RETURN e1.eventId as source, e2.eventId as target,
                   r.score as score, r.temporal as temporal,
                   r.entity_overlap as entityOverlap, r.semantic as semantic,
                   r.topic as topic, r.causality as causality,
                   r.emotional as emotional
            ORDER BY r.score DESC
            """
            evolution_links = analyzer.backend.execute_query(
                evolution_query,
                {'endDate': end_date, 'minScore': min_score}
            )

            # Get all entities (they exist throughout the timeline)
            entities_query = """
            MATCH (ent:Entity)
            RETURN ent.entityId as id, ent.name as name,
                   ent.type as type, ent.description as description
            ORDER BY ent.name
            """
            entities = analyzer.backend.execute_query(entities_query)

            # Get risks associated with events up to end_date
            risks_query = """
            MATCH (r:Risk)-[:TARGETS_ENTITY]->(e:Entity)
            MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
            OPTIONAL MATCH (evt:Event)-[:HAS_TARGET|HAS_ACTOR]->(e)
            WHERE evt.date <= date($endDate)
            WITH r, rt, e, count(DISTINCT evt) as eventCount
            WHERE eventCount > 0
            RETURN DISTINCT r.riskId as id, rt.label as type,
                   r.score as score, r.severity as severity,
                   e.entityId as targetEntityId, e.name as targetEntityName
            ORDER BY r.score DESC
            """
            risks = analyzer.backend.execute_query(risks_query, {'endDate': end_date})

            analyzer.close()

            # Build nodes/edges structure
            nodes = []
            edges = []

            # Add entity nodes
            for entity in entities:
                nodes.append({
                    'id': entity['id'],
                    'label': entity['name'],
                    'type': 'entity',
                    'group': 'entity',
                    'title': f"{entity['name']}<br>{entity['type']}",
                    'data': entity
                })

            # Add event nodes
            for event in events:
                nodes.append({
                    'id': event['id'],
                    'label': event['type'],
                    'type': 'event',
                    'group': 'event',
                    'title': f"{event['type']}<br>{event['date']}<br>{event['description'][:50]}...",
                    'data': event
                })

                # Add event-entity edges
                if event.get('actorId'):
                    edges.append({
                        'from': event['id'],
                        'to': event['actorId'],
                        'type': 'has_actor',
                        'arrows': 'to',
                        'dashes': False,
                        'color': {'color': '#64748b', 'opacity': 0.6},  # Slate gray
                        'width': 1.5
                    })
                if event.get('targetId'):
                    edges.append({
                        'from': event['id'],
                        'to': event['targetId'],
                        'type': 'has_target',
                        'arrows': 'to',
                        'dashes': False,
                        'color': {'color': '#64748b', 'opacity': 0.6},  # Slate gray
                        'width': 1.5
                    })

            # Add risk nodes
            for risk in risks:
                nodes.append({
                    'id': risk['id'],
                    'label': risk['type'],
                    'type': 'risk',
                    'group': 'risk',
                    'title': f"{risk['type']}<br>Score: {risk['score']}<br>Severity: {risk['severity']}",
                    'data': risk
                })

                # Add risk-entity edges
                if risk.get('targetEntityId'):
                    edges.append({
                        'from': risk['id'],
                        'to': risk['targetEntityId'],
                        'type': 'targets',
                        'arrows': 'to',
                        'dashes': True,
                        'color': {'color': '#f472b6', 'opacity': 0.5},  # Pink (lighter)
                        'width': 1.5
                    })

            # Add evolution edges
            for link in evolution_links:
                edges.append({
                    'from': link['source'],
                    'to': link['target'],
                    'type': 'evolves_to',
                    'arrows': 'to',
                    'width': max(1.5, link['score'] * 3),  # Min width 1.5
                    'color': {
                        'color': '#8b5cf6',  # Purple (matches app theme)
                        'opacity': 0.7 + (link['score'] * 0.3)  # Opacity based on score
                    },
                    'title': f"Score: {link['score']:.3f}<br>Causality: {link['causality']:.3f}",
                    'data': link
                })

            return jsonify({
                'status': 'success',
                'endDate': end_date,
                'nodes': nodes,
                'edges': edges,
                'stats': {
                    'entities': len(entities),
                    'events': len(events),
                    'risks': len(risks),
                    'evolution_links': len(evolution_links)
                }
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    return app


if __name__ == '__main__':
    import os
    app = create_app()

    # Get port from environment variable (for Railway/Heroku) or default to 5001
    port = int(os.environ.get('PORT', 5001))

    print("\n" + "=" * 70)
    print("FE-EKG REST API Server")
    print("=" * 70)
    print(f"\nStarting server on http://0.0.0.0:{port}")
    print("\nAPI Documentation:")
    print("  Health:       GET  /health")
    print("  Info:         GET  /api/info")
    print("  Entities:     GET  /api/entities")
    print("  Events:       GET  /api/events")
    print("  Evolution:    GET  /api/evolution/links")
    print("  Risks:        GET  /api/risks")
    print("  Graph Data:   GET  /api/graph/data")
    print("  Timeline:     GET  /api/graph/timeline?end_date=YYYY-MM-DD")
    print("  Viz (3-layer):GET  /api/visualizations/three-layer")
    print("\nInteractive Demos:")
    print(f"  API Demo:     http://localhost:{port}/demo.html")
    print(f"  Timeline:     http://localhost:{port}/timeline.html")
    print("\nPress Ctrl+C to stop")
    print("=" * 70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=port)
