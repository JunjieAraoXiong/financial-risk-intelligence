"""
Timeline Visualization for Financial Events
Chronological view of events with date-based filtering
"""

import sys
import os
import json
from typing import Optional, Dict
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config.graph_backend import get_connection


class TimelineVisualizer:
    """Create timeline-based event visualizations"""

    def __init__(self):
        self.backend = get_connection()

    def close(self):
        self.backend.close()

    def fetch_timeline_data(self, limit: int = 300) -> Dict:
        """Fetch events with temporal data"""
        print(f"Fetching timeline data (limit={limit})...")

        # Get all events with dates and involved entities
        query = f"""
        PREFIX feekg: <http://feekg.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?event ?label ?type ?date ?desc
               ?csvRow ?confidence
        WHERE {{
          ?event a feekg:Event .
          ?event feekg:date ?date .
          OPTIONAL {{ ?event rdfs:label ?label }}
          OPTIONAL {{ ?event feekg:eventType ?type }}
          OPTIONAL {{ ?event feekg:description ?desc }}
          OPTIONAL {{ ?event feekg:csvRowNumber ?csvRow }}
          OPTIONAL {{ ?event feekg:classificationConfidence ?confidence }}
          FILTER(?date != "unknown")
        }}
        ORDER BY ?date
        LIMIT {limit}
        """

        events = self.backend.execute_query(query)

        # Process events
        timeline_events = []
        dates_set = set()

        for e in events:
            label = (e.get('label') or '').strip(' "')
            if not label:
                label = "Untitled Event"

            event_type = (e.get('type') or 'unknown').strip(' "')
            date_raw = (e.get('date') or '').strip(' "')
            desc = (e.get('desc') or '').strip(' "')[:300]
            csv_row = (e.get('csvRow') or '').strip(' "')
            confidence = (e.get('confidence') or '').strip(' "')

            # Extract date from RDF literal (e.g., "2008-07-24"^^<http://...>)
            date_str = date_raw.split('^^')[0].strip(' "') if '^^' in date_raw else date_raw

            if date_str and date_str != 'unknown':
                try:
                    # Parse date
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    dates_set.add(date_str)

                    timeline_events.append({
                        'id': f"evt_{len(timeline_events)}",
                        'label': label,
                        'type': event_type,
                        'date': date_str,
                        'timestamp': int(date_obj.timestamp() * 1000),
                        'description': desc,
                        'csvRow': csv_row,
                        'confidence': confidence,
                        'uri': e['event']
                    })
                except ValueError:
                    continue

        print(f"  ✓ Loaded {len(timeline_events)} dated events")
        print(f"  ✓ Date range: {min(dates_set)} to {max(dates_set)}")

        return {
            'events': timeline_events,
            'stats': {
                'total': len(timeline_events),
                'dateRange': [min(dates_set), max(dates_set)]
            }
        }

    def create_timeline_view(self, limit: int = 300, save_path: Optional[str] = None) -> str:
        """Create interactive timeline visualization"""

        if save_path is None:
            save_path = "results/timeline_view.html"

        data = self.fetch_timeline_data(limit)
        html_content = self._generate_timeline_html(data)

        with open(save_path, 'w') as f:
            f.write(html_content)

        print(f"\n✅ Timeline visualization created!")
        print(f"📊 {data['stats']['total']} events from {data['stats']['dateRange'][0]} to {data['stats']['dateRange'][1]}")
        print(f"📂 Open: file://{os.path.abspath(save_path)}")

        return save_path

    def _generate_timeline_html(self, data: Dict) -> str:
        """Generate timeline HTML"""

        data_json = json.dumps(data, indent=2)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Timeline - Financial Crisis</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #fff;
            overflow-x: hidden;
        }}

        .header {{
            background: rgba(255, 255, 255, 0.98);
            padding: 24px 32px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            color: #333;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .header .subtitle {{
            font-size: 14px;
            color: #666;
            margin-top: 4px;
        }}

        .timeline-container {{
            padding: 32px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .controls {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            color: #333;
        }}

        .controls h3 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #667eea;
        }}

        .slider-container {{
            margin: 16px 0;
        }}

        .slider {{
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #e9ecef;
            outline: none;
            -webkit-appearance: none;
        }}

        .slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
        }}

        .slider::-moz-range-thumb {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
        }}

        .date-display {{
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 13px;
            color: #666;
        }}

        .filter-buttons {{
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            background: #667eea;
            color: white;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}

        #timeline {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
            min-height: 600px;
        }}

        .event-node {{
            cursor: pointer;
            transition: all 0.2s;
        }}

        .event-node:hover {{
            transform: scale(1.2);
        }}

        .event-label {{
            pointer-events: none;
            font-size: 11px;
            fill: #fff;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        }}

        .axis {{
            font-size: 12px;
            color: #94a3b8;
        }}

        .axis line,
        .axis path {{
            stroke: #475569;
        }}

        .axis text {{
            fill: #94a3b8;
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
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            color: #333;
        }}

        .tooltip.show {{
            opacity: 1;
        }}

        .tooltip strong {{
            color: #667eea;
            font-size: 14px;
            display: block;
            margin-bottom: 8px;
        }}

        .tooltip .date {{
            color: #666;
            font-size: 11px;
            margin-bottom: 8px;
        }}

        .stats {{
            display: flex;
            gap: 24px;
            margin-top: 24px;
            flex-wrap: wrap;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            flex: 1;
            min-width: 200px;
            color: #333;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .stat-card h4 {{
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📅 Financial Crisis Timeline</h1>
        <div class="subtitle">Chronological Event Explorer with CSV Provenance</div>
    </div>

    <div class="timeline-container">
        <div class="controls">
            <h3>🎚️ Time Range Filter</h3>
            <div class="slider-container">
                <input type="range" class="slider" id="dateSlider" min="0" max="100" value="100">
                <div class="date-display">
                    <span id="startDate">Start</span>
                    <span id="endDate">End</span>
                </div>
            </div>

            <h3 style="margin-top: 20px;">🏷️ Event Type Filter</h3>
            <div class="filter-buttons" id="typeFilters"></div>
        </div>

        <svg id="timeline"></svg>

        <div class="stats">
            <div class="stat-card">
                <h4>Total Events</h4>
                <div class="value" id="totalEvents">0</div>
            </div>
            <div class="stat-card">
                <h4>Visible Events</h4>
                <div class="value" id="visibleEvents">0</div>
            </div>
            <div class="stat-card">
                <h4>Date Range</h4>
                <div class="value" style="font-size: 16px;" id="dateRangeText">-</div>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const timelineData = {data_json};
        const events = timelineData.events;

        // Event type colors
        const typeColors = {{
            'bankruptcy': '#ef4444',
            'credit_downgrade': '#f59e0b',
            'merger_acquisition': '#3b82f6',
            'regulatory_pressure': '#8b5cf6',
            'stock_decline': '#ec4899',
            'debt_default': '#dc2626',
            'missed_payment': '#f97316',
            'default': '#6b7280'
        }};

        // Setup SVG
        const margin = {{top: 40, right: 40, bottom: 60, left: 60}};
        const width = 1300 - margin.left - margin.right;
        const height = 600 - margin.top - margin.bottom;

        const svg = d3.select('#timeline')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

        // Scales
        const xScale = d3.scaleTime()
            .domain(d3.extent(events, d => new Date(d.date)))
            .range([0, width]);

        const yScale = d3.scaleLinear()
            .domain([0, 1])
            .range([height, 0]);

        // Axes
        const xAxis = d3.axisBottom(xScale)
            .ticks(10)
            .tickFormat(d3.timeFormat('%b %Y'));

        svg.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,${{height}})`)
            .call(xAxis)
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end');

        // Draw events
        let filteredEvents = events;
        const tooltip = d3.select('#tooltip');

        function render() {{
            // Clear existing
            svg.selectAll('.event-node').remove();
            svg.selectAll('.event-label').remove();

            // Distribute events vertically to avoid overlap
            const eventsByDate = d3.group(filteredEvents, d => d.date);
            const positioned = [];

            eventsByDate.forEach((evts, date) => {{
                evts.forEach((evt, i) => {{
                    positioned.push({{
                        ...evt,
                        y: (i % 5) / 5 // Distribute across 5 vertical levels
                    }});
                }});
            }});

            // Draw event nodes
            svg.selectAll('.event-node')
                .data(positioned)
                .join('circle')
                .attr('class', 'event-node')
                .attr('cx', d => xScale(new Date(d.date)))
                .attr('cy', d => yScale(d.y))
                .attr('r', 8)
                .attr('fill', d => typeColors[d.type] || typeColors['default'])
                .attr('stroke', '#fff')
                .attr('stroke-width', 2)
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip);

            // Update stats
            document.getElementById('visibleEvents').textContent = filteredEvents.length;
        }}

        function showTooltip(event, d) {{
            let html = `<strong>${{d.label}}</strong>`;
            html += `<div class="date">${{d.date}}</div>`;
            html += `<div style="margin-top: 8px; font-size: 12px;">${{d.description || 'No description'}}</div>`;
            html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e9ecef; font-size: 11px; color: #666;">`;
            html += `Type: ${{d.type}}<br>`;
            if (d.csvRow) html += `CSV Row: ${{d.csvRow}}<br>`;
            if (d.confidence) html += `Confidence: ${{(parseFloat(d.confidence) * 100).toFixed(1)}}%`;
            html += `</div>`;

            tooltip
                .html(html)
                .style('left', (event.pageX + 15) + 'px')
                .style('top', (event.pageY - 15) + 'px')
                .classed('show', true);
        }}

        function hideTooltip() {{
            tooltip.classed('show', false);
        }}

        // Date range filter
        const allDates = events.map(e => new Date(e.date)).sort((a, b) => a - b);
        const dateSlider = document.getElementById('dateSlider');
        const startDateEl = document.getElementById('startDate');
        const endDateEl = document.getElementById('endDate');

        startDateEl.textContent = d3.timeFormat('%b %Y')(allDates[0]);
        endDateEl.textContent = d3.timeFormat('%b %Y')(allDates[allDates.length - 1]);

        dateSlider.addEventListener('input', (e) => {{
            const percent = e.target.value / 100;
            const cutoffIndex = Math.floor(allDates.length * percent);
            const cutoffDate = allDates[cutoffIndex];

            endDateEl.textContent = d3.timeFormat('%b %Y')(cutoffDate);

            filteredEvents = events.filter(ev => new Date(ev.date) <= cutoffDate);
            render();
        }});

        // Type filters
        const types = [...new Set(events.map(e => e.type))].sort();
        const typeFiltersEl = document.getElementById('typeFilters');
        const selectedTypes = new Set(types);

        types.forEach(type => {{
            const btn = document.createElement('button');
            btn.className = 'filter-btn active';
            btn.textContent = type.replace(/_/g, ' ');
            btn.onclick = () => {{
                if (selectedTypes.has(type)) {{
                    selectedTypes.delete(type);
                    btn.classList.remove('active');
                }} else {{
                    selectedTypes.add(type);
                    btn.classList.add('active');
                }}

                filteredEvents = events.filter(e =>
                    selectedTypes.has(e.type) &&
                    new Date(e.date) <= allDates[Math.floor(allDates.length * (dateSlider.value / 100))]
                );
                render();
            }};
            typeFiltersEl.appendChild(btn);
        }});

        // Initial render
        document.getElementById('totalEvents').textContent = events.length;
        document.getElementById('dateRangeText').textContent =
            `${{d3.timeFormat('%b %Y')(allDates[0])}} - ${{d3.timeFormat('%b %Y')(allDates[allDates.length - 1])}}`;
        render();
    </script>
</body>
</html>"""


if __name__ == "__main__":
    viz = TimelineVisualizer()

    print("=" * 70)
    print("Creating Timeline Visualization")
    print("=" * 70)
    print()

    viz.create_timeline_view(
        limit=300,
        save_path="results/timeline_view.html"
    )

    viz.close()

    print()
    print("=" * 70)
    print("✅ Done! Open in browser:")
    print("   results/timeline_view.html")
    print("=" * 70)
