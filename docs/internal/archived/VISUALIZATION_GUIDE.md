# FE-EKG Visualization Guide

## Overview

Professional, interactive visualizations for the Financial Event Evolution Knowledge Graph (FE-EKG) with complete CSV traceability and data provenance.

**Created:** 2025-11-15
**Status:** Production Ready ✅
**Technology:** D3.js v7 + AllegroGraph 8.4.0 + Python 3.13

---

## Quick Start

### Open the Dashboard
```bash
open results/dashboard.html
```

This is your main entry point with links to all visualizations.

### Individual Visualizations
```bash
# Optimized interactive network
open results/optimized_knowledge_graph.html

# Timeline view
open results/timeline_view.html

# Basic network view
open results/clean_knowledge_graph.html
```

---

## Available Visualizations

### 1. **Interactive Knowledge Graph** ⭐ (Recommended)

**File:** `results/optimized_knowledge_graph.html`

**What it shows:**
- Force-directed network of entities and events
- 18 entities (banks, regulators, investment banks)
- 150 events with CSV provenance
- 13 event-entity relationships

**Features:**
- ✅ **Search** - Find entities/events by name
- ✅ **Drag nodes** - Rearrange the layout
- ✅ **Zoom & Pan** - Explore large networks
- ✅ **CSV Provenance** - Every event shows source row number and confidence
- ✅ **Color-coded** - Different colors for entity types
- ✅ **Toggle Physics** - Freeze/unfreeze the simulation
- ✅ **Tooltips** - Rich information on hover

**Best for:**
- Interactive exploration
- Finding entity connections
- Understanding network structure
- Research and analysis

**Controls:**
- Mouse wheel → Zoom
- Drag background → Pan
- Drag nodes → Move
- Hover → See details
- Search box → Filter

---

### 2. **Timeline Explorer** 📅

**File:** `results/timeline_view.html`

**What it shows:**
- Chronological view of 300 events
- Events plotted by date (2007-2009)
- Distributed vertically to avoid overlap

**Features:**
- ✅ **Time Slider** - Filter events by date range
- ✅ **Type Filters** - Show/hide event types (bankruptcy, credit downgrade, etc.)
- ✅ **Statistics** - See event counts and date ranges
- ✅ **CSV Provenance** - Row numbers and confidence scores

**Best for:**
- Understanding event sequences
- Temporal analysis
- Finding patterns over time
- Crisis timeline reconstruction

**How to use:**
1. Drag slider to focus on specific time period
2. Click event type buttons to filter
3. Hover events for details

---

### 3. **Basic Network View** 🎯

**File:** `results/clean_knowledge_graph.html`

**What it shows:**
- Simplified network view
- 124 nodes (24 entities + 100 events)
- 9 relationships

**Features:**
- ✅ Lightweight (53 KB)
- ✅ Fast loading
- ✅ Simple controls
- ✅ Good for sharing

**Best for:**
- Quick views
- Presentations
- Sharing with others
- Simple exploration

---

### 4. **Dashboard** 📊

**File:** `results/dashboard.html`

**What it shows:**
- Landing page with all visualizations
- Statistics overview
- Navigation to all views
- Documentation

**Features:**
- ✅ Project overview
- ✅ Data statistics
- ✅ Quick access to all views
- ✅ Embedded documentation

**Best for:**
- Starting point
- Overview of project
- Sharing project with stakeholders

---

## Data Quality & Provenance

### CSV Traceability

Every event in the visualizations includes:

| Metadata | Description | Example |
|----------|-------------|---------|
| **csvRowNumber** | Source row in CSV | 68940 |
| **csvFilename** | Source file | capital_iq_download.csv |
| **capitalIqId** | Original Capital IQ ID | 83730941 |
| **classificationConfidence** | AI classification confidence | 0.95 (95%) |
| **classificationMethod** | How it was classified | pattern_match |

**Data Quality:**
- ✅ 0% unknown events (down from 8.6%)
- ✅ 87.1% average classification confidence
- ✅ 100% CSV traceable
- ✅ 74,012 RDF triples in AllegroGraph

---

## How It Works

### Architecture

```
┌──────────────┐   SPARQL    ┌──────────┐   Process   ┌──────────┐
│ AllegroGraph │ ←────────── │  Python  │ ──────────→ │   HTML   │
│  (Database)  │             │  Script  │             │  (D3.js) │
└──────────────┘             └──────────┘             └──────────┘
    74K triples               Fetch & Clean           Interactive Viz
```

**Step 1: Query AllegroGraph**
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?label ?type ?date
WHERE {
  ?event a feekg:Event .
  ?event rdfs:label ?label .
  ?event feekg:eventType ?type .
  ?event feekg:date ?date .
}
ORDER BY ?date
LIMIT 150
```

**Step 2: Process in Python**
```python
# Clean data
label = e.get('label', '').strip(' "')
event_type = e.get('type', 'unknown').strip(' "')

# Create JSON structure
node = {
    'id': event_id,
    'label': label,
    'type': event_type,
    'group': 'event'
}
```

**Step 3: Embed in HTML**
```javascript
// Data embedded as JavaScript
const graphData = {
    "nodes": [...],
    "links": [...]
};
```

**Step 4: Render with D3.js**
```javascript
// Force simulation
d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links))
    .force('charge', d3.forceManyBody())
    .force('center', d3.forceCenter())
```

---

## Regenerating Visualizations

### Prerequisites
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# or
./venv/bin/python  # Direct execution

# AllegroGraph should be running and accessible
```

### Generate Individual Visualizations

**Optimized Knowledge Graph:**
```bash
./venv/bin/python viz/optimized_visualizer.py
# Output: results/optimized_knowledge_graph.html
```

**Timeline View:**
```bash
./venv/bin/python viz/timeline_visualizer.py
# Output: results/timeline_view.html
```

**Dashboard:**
```bash
./venv/bin/python viz/dashboard_generator.py
# Output: results/dashboard.html
```

### Generate All Visualizations

Create a simple script:
```bash
#!/bin/bash
echo "Generating all visualizations..."
./venv/bin/python viz/optimized_visualizer.py
./venv/bin/python viz/timeline_visualizer.py
./venv/bin/python viz/dashboard_generator.py
echo "Done! Open results/dashboard.html"
```

---

## Customization

### Change Maximum Events

Edit the Python scripts:

```python
# viz/optimized_visualizer.py
viz.create_optimized_visualization(
    max_events=200,  # Change from 150 to 200
    save_path="results/optimized_knowledge_graph.html"
)
```

### Change Colors

Edit the HTML file directly or modify the generator:

```python
# In optimized_visualizer.py, _generate_optimized_html()
const colorMap = {
    'bank': '#YOUR_COLOR',
    'regulator': '#YOUR_COLOR',
    'investment_bank': '#YOUR_COLOR',
    ...
};
```

### Adjust Force Simulation

```python
# Stronger repulsion
.force('charge', d3.forceManyBody().strength(-500))  # Default: -400

# Longer links
.force('link', d3.forceLink(links).distance(150))  # Default: 120
```

---

## File Structure

```
feekg/
├── viz/
│   ├── optimized_visualizer.py     ← Generate optimized graph
│   ├── timeline_visualizer.py      ← Generate timeline
│   ├── dashboard_generator.py      ← Generate dashboard
│   ├── clean_interactive.py        ← Old version
│   └── graph_viz.py                ← Old static visualizations
│
├── results/
│   ├── dashboard.html               ← 🎯 START HERE
│   ├── optimized_knowledge_graph.html  ← Interactive network
│   ├── timeline_view.html           ← Timeline view
│   └── clean_knowledge_graph.html   ← Basic network
│
└── VISUALIZATION_GUIDE.md          ← This file
```

---

## Performance

### Benchmarks

| Visualization | File Size | Load Time | Nodes | Rendering |
|---------------|-----------|-----------|-------|-----------|
| Optimized Graph | 95 KB | < 1s | 168 | 60 fps |
| Timeline | 110 KB | < 1s | 300 | 60 fps |
| Basic Graph | 53 KB | < 500ms | 124 | 60 fps |
| Dashboard | 8 KB | < 200ms | - | - |

**Tested on:**
- Chrome 120+
- Safari 17+
- Firefox 121+

### Optimization Tips

**For faster loading:**
- Reduce `max_events` parameter
- Use Basic Network View for quick sharing

**For larger datasets:**
- Increase `max_events` to 300-500
- May need to adjust force simulation parameters
- Consider pagination or filtering

**For presentations:**
- Use dashboard as landing page
- Timeline view shows temporal progression well
- Export screenshots for static documents

---

## Troubleshooting

### Issue: Visualization doesn't load

**Solution:**
1. Check browser console for errors (F12)
2. Ensure D3.js CDN is accessible
3. Try different browser

### Issue: No nodes appear

**Solution:**
1. Check if AllegroGraph has data
2. Verify SPARQL queries return results
3. Regenerate visualization

### Issue: Performance is slow

**Solution:**
1. Reduce `max_events` parameter
2. Toggle physics off (button in controls)
3. Use simpler Basic Network View

### Issue: Dates not parsing

**Solution:**
- Already handled! RDF datatype annotations are stripped
- Format: `"2008-07-24"^^<http://...>` → `2008-07-24`

---

## Comparison: Static vs. Dynamic

### Current (Static - What You Have)

**Pros:**
- ✅ Fast loading (no API calls)
- ✅ Works offline
- ✅ Easy to share (just send HTML)
- ✅ Self-contained
- ✅ Production-ready now

**Cons:**
- ❌ Data frozen at generation time
- ❌ Need to regenerate for updates
- ❌ File size grows with data

### Future (Dynamic - Optional)

**Pros:**
- ✅ Always shows latest data
- ✅ Smaller file sizes
- ✅ Can filter/query in real-time

**Cons:**
- ❌ Requires server running
- ❌ Network latency
- ❌ More complex setup

**Recommendation:** Keep static for now, switch to dynamic if you build a web application later.

---

## Integration with AllegroGraph

### GraphQL (Optional Future Enhancement)

If you want to add GraphQL later:

1. **Define schema in AllegroGraph UI**
2. **Query from frontend:**

```javascript
const query = `
    query {
        events(limit: 100) {
            id
            label
            date
            type
        }
    }
`;

fetch('http://localhost:10035/repositories/FEEKG/graphql', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query})
})
```

**But this is NOT needed for your current static visualizations!**

---

## Best Practices

### For Research/Analysis
1. Start with **Dashboard** for overview
2. Use **Optimized Graph** for exploration
3. Use **Timeline** for temporal patterns
4. Export findings as screenshots

### For Presentations
1. Use **Dashboard** as main page
2. **Timeline** shows progression well
3. **Optimized Graph** for interactive demo
4. Take screenshots for slides

### For Sharing
1. Send **dashboard.html** (includes links to all views)
2. All files are self-contained
3. Works on any browser
4. No installation needed

---

## Future Enhancements

### Easy Additions
- [  ] Export graph as PNG/SVG
- [  ] More entity type colors
- [  ] Better mobile responsiveness
- [  ] Dark/light mode toggle

### Advanced Features
- [  ] Entity-centric view (focus on one entity)
- [  ] Risk propagation visualization
- [  ] Evolution link visualization
- [  ] Multi-hop path finding
- [  ] Clustering by event type/date
- [  ] Mini-map overview

### Dynamic Features (Require Flask API)
- [  ] Live data updates
- [  ] User authentication
- [  ] Save/load custom views
- [  ] Collaborative annotations
- [  ] Real-time collaboration

---

## Support & Documentation

### Files to Reference
- `README.md` - Project overview
- `CLAUDE.md` - Development guide
- `DATA_QUALITY_REPORT.md` - Data quality metrics
- `CLEAN_VISUALS.md` - Visualization comparison

### Key Python Files
- `config/graph_backend.py` - AllegroGraph connection
- `viz/optimized_visualizer.py` - Main visualization generator
- `viz/timeline_visualizer.py` - Timeline generator

### HTML/CSS/JS
- All visualizations are in `results/*.html`
- Fully self-contained (no external dependencies except D3.js CDN)
- Modern ES6+ JavaScript
- Responsive CSS Grid layouts

---

## Summary

**You now have:**
- ✅ 4 professional visualizations
- ✅ CSV provenance in all views
- ✅ Interactive exploration capabilities
- ✅ Clean, modern UI
- ✅ Production-ready code
- ✅ Complete documentation

**Start here:**
```bash
open results/dashboard.html
```

**Questions?**
- Check this guide
- Review code comments
- See `CLAUDE.md` for architecture

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
**Status:** Production Ready ✅
