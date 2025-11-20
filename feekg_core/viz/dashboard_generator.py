"""
Unified Dashboard Generator
Creates a multi-view dashboard with navigation between visualizations
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def create_dashboard(save_path: str = "results/dashboard.html"):
    """Create unified dashboard HTML"""

    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FE-EKG Visualization Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #fff;
            min-height: 100vh;
        }

        .header {
            background: rgba(255, 255, 255, 0.98);
            padding: 32px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            color: #333;
        }

        .header h1 {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .header .subtitle {
            font-size: 16px;
            color: #666;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 48px 32px;
        }

        .intro {
            background: rgba(255, 255, 255, 0.95);
            padding: 32px;
            border-radius: 16px;
            margin-bottom: 32px;
            color: #333;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }

        .intro h2 {
            font-size: 20px;
            margin-bottom: 16px;
            color: #667eea;
        }

        .intro p {
            line-height: 1.6;
            margin-bottom: 12px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 24px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            color: white;
        }

        .stat-card .value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .stat-card .label {
            font-size: 14px;
            opacity: 0.9;
        }

        .viz-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-top: 32px;
        }

        .viz-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }

        .viz-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
        }

        .viz-card .preview {
            height: 250px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 64px;
        }

        .viz-card .content {
            padding: 24px;
            color: #333;
        }

        .viz-card h3 {
            font-size: 20px;
            margin-bottom: 12px;
            color: #667eea;
        }

        .viz-card p {
            font-size: 14px;
            line-height: 1.6;
            color: #666;
            margin-bottom: 16px;
        }

        .viz-card .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            transition: transform 0.2s;
        }

        .viz-card .btn:hover {
            transform: scale(1.05);
        }

        .features {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .feature-tag {
            background: #f1f5f9;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            color: #667eea;
            font-weight: 600;
        }

        .documentation {
            background: rgba(255, 255, 255, 0.95);
            padding: 32px;
            border-radius: 16px;
            margin-top: 32px;
            color: #333;
        }

        .documentation h2 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #667eea;
        }

        .documentation h3 {
            font-size: 18px;
            margin-top: 24px;
            margin-bottom: 12px;
            color: #333;
        }

        .documentation ul {
            margin-left: 24px;
            line-height: 1.8;
        }

        .documentation code {
            background: #f8f9fa;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 FE-EKG Visualization Dashboard</h1>
        <div class="subtitle">Financial Event Evolution Knowledge Graph - Interactive Exploration Suite</div>
    </div>

    <div class="container">
        <div class="intro">
            <h2>Welcome to the FE-EKG Visualization Suite</h2>
            <p>
                This dashboard provides multiple interactive views of the Financial Event Evolution Knowledge Graph,
                built with complete CSV traceability and data provenance.
            </p>
            <p>
                All visualizations are generated from <strong>AllegroGraph</strong> using <strong>SPARQL queries</strong>
                and rendered with <strong>D3.js</strong> for interactive exploration.
            </p>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">4,398</div>
                    <div class="label">Total Events</div>
                </div>
                <div class="stat-card">
                    <div class="value">18</div>
                    <div class="label">Entities</div>
                </div>
                <div class="stat-card">
                    <div class="value">74K+</div>
                    <div class="label">RDF Triples</div>
                </div>
                <div class="stat-card">
                    <div class="value">100%</div>
                    <div class="label">CSV Traceable</div>
                </div>
            </div>
        </div>

        <div class="viz-grid">
            <!-- Optimized Knowledge Graph -->
            <div class="viz-card" onclick="window.location.href='optimized_knowledge_graph.html'">
                <div class="preview">🕸️</div>
                <div class="content">
                    <h3>Interactive Knowledge Graph</h3>
                    <p>
                        Force-directed graph showing entities and events with their relationships.
                        Features search, filtering, and CSV provenance tooltips.
                    </p>
                    <div class="features">
                        <span class="feature-tag">Drag & Drop</span>
                        <span class="feature-tag">Search</span>
                        <span class="feature-tag">Zoom & Pan</span>
                        <span class="feature-tag">Provenance</span>
                    </div>
                    <a href="optimized_knowledge_graph.html" class="btn">Open Visualization →</a>
                </div>
            </div>

            <!-- Timeline View -->
            <div class="viz-card" onclick="window.location.href='timeline_view.html'">
                <div class="preview">📅</div>
                <div class="content">
                    <h3>Timeline Explorer</h3>
                    <p>
                        Chronological view of financial events with date-based filtering.
                        Explore events over time with an interactive time slider.
                    </p>
                    <div class="features">
                        <span class="feature-tag">Time Slider</span>
                        <span class="feature-tag">Type Filters</span>
                        <span class="feature-tag">Date Range</span>
                    </div>
                    <a href="timeline_view.html" class="btn">Open Timeline →</a>
                </div>
            </div>

            <!-- Original Clean Graph -->
            <div class="viz-card" onclick="window.location.href='clean_knowledge_graph.html'">
                <div class="preview">🎯</div>
                <div class="content">
                    <h3>Basic Network View</h3>
                    <p>
                        Simplified network visualization with essential controls.
                        Good for quick exploration and sharing.
                    </p>
                    <div class="features">
                        <span class="feature-tag">Lightweight</span>
                        <span class="feature-tag">Fast Loading</span>
                        <span class="feature-tag">Simple UI</span>
                    </div>
                    <a href="clean_knowledge_graph.html" class="btn">Open View →</a>
                </div>
            </div>
        </div>

        <div class="documentation">
            <h2>📖 Documentation</h2>

            <h3>About the Data</h3>
            <ul>
                <li><strong>Source:</strong> Capital IQ financial events dataset</li>
                <li><strong>Coverage:</strong> 2007-2009 financial crisis events</li>
                <li><strong>Entities:</strong> Banks, investment banks, regulators, rating agencies</li>
                <li><strong>Events:</strong> Bankruptcy, credit downgrades, mergers, regulatory actions, etc.</li>
                <li><strong>Provenance:</strong> Every event includes CSV row number and classification confidence</li>
            </ul>

            <h3>Features</h3>
            <ul>
                <li><strong>Interactive Exploration:</strong> Drag, zoom, pan, and click to explore</li>
                <li><strong>Search & Filter:</strong> Find specific entities or events</li>
                <li><strong>Temporal Analysis:</strong> View events chronologically with timeline</li>
                <li><strong>Data Quality:</strong> 87.1% average classification confidence</li>
                <li><strong>Full Traceability:</strong> Every data point links back to source CSV</li>
            </ul>

            <h3>Controls</h3>
            <ul>
                <li><strong>Mouse wheel:</strong> Zoom in/out</li>
                <li><strong>Click & drag (background):</strong> Pan the view</li>
                <li><strong>Click & drag (node):</strong> Move individual nodes</li>
                <li><strong>Hover:</strong> See detailed information</li>
                <li><strong>Search box:</strong> Filter by entity/event name</li>
            </ul>

            <h3>Technology Stack</h3>
            <ul>
                <li><strong>Database:</strong> AllegroGraph 8.4.0 (RDF triple store)</li>
                <li><strong>Query Language:</strong> SPARQL 1.1</li>
                <li><strong>Visualization:</strong> D3.js v7 (force-directed graphs)</li>
                <li><strong>Data Processing:</strong> Python 3.13 with Franz AllegroGraph client</li>
                <li><strong>Total Triples:</strong> 74,012 in knowledge graph</li>
            </ul>

            <h3>How to Regenerate</h3>
            <p>To regenerate these visualizations with updated data:</p>
            <ul>
                <li><code>python viz/optimized_visualizer.py</code> - Optimized knowledge graph</li>
                <li><code>python viz/timeline_visualizer.py</code> - Timeline view</li>
                <li><code>python viz/dashboard_generator.py</code> - This dashboard</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    with open(save_path, 'w') as f:
        f.write(dashboard_html)

    print(f"✅ Dashboard created: {os.path.abspath(save_path)}")
    return save_path


if __name__ == "__main__":
    print("=" * 70)
    print("Creating Unified Dashboard")
    print("=" * 70)
    print()

    dashboard_path = create_dashboard()

    print()
    print("=" * 70)
    print("✅ Done! Open in browser:")
    print(f"   {dashboard_path}")
    print("=" * 70)
    print()
    print("Available visualizations:")
    print("  • dashboard.html - Main dashboard with all views")
    print("  • optimized_knowledge_graph.html - Interactive network")
    print("  • timeline_view.html - Chronological explorer")
    print("  • clean_knowledge_graph.html - Basic network view")
