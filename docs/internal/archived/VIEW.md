# 👀 How to View Your FE-EKG System

## TL;DR - The Fastest Way

```bash
# 1. View visualizations (PNG images)
./venv/bin/python scripts/demo_visualizations.py
open results/*.png

# 2. View in browser (interactive)
./venv/bin/python api/app.py
# Then open: file:///Users/hansonxiong/Desktop/DDP/feekg/api/demo.html
```

---

## 🖼️ Option 1: View Visualizations (Recommended First!)

### Generate the Images

```bash
./venv/bin/python scripts/demo_visualizations.py
```

This creates **8 PNG files** in the `results/` folder:

1. **three_layer_graph.png** - Shows Entity → Event → Risk layers
2. **evolution_network.png** - Event evolution with causality scores
3. **risk_propagation.png** - How risks connect to entities
4. **evolution_heatmap.png** - Matrix of event type evolution
5. **component_breakdown.png** - Which evolution methods contribute most
6. **risk_distribution.png** - Risk severity distribution
7. **event_network_timeline.png** - Events on a timeline
8. **risk_timeline.png** - How risks evolved over time

### View the Images

**On Mac:**
```bash
# View one at a time
open results/three_layer_graph.png

# View all at once
open results/*.png
```

**On Linux:**
```bash
xdg-open results/three_layer_graph.png
```

**On Windows:**
```bash
start results\three_layer_graph.png
```

**Or just:**
- Navigate to the `results/` folder in Finder/Explorer
- Double-click any `.png` file

---

## 🌐 Option 2: Interactive Web Demo (Most Fun!)

### Step 1: Start the API Server

```bash
./venv/bin/python api/app.py
```

You'll see:
```
FE-EKG REST API Server
Starting server on http://localhost:5000
...
```

Keep this terminal window open!

### Step 2: Open the Demo Page

**Method 1 - Double-click the file:**
- Navigate to: `feekg/api/demo.html`
- Double-click it
- It opens in your default browser

**Method 2 - Command line (Mac):**
```bash
open api/demo.html
```

**Method 3 - Direct path:**
- Copy this to your browser:
- `file:///Users/hansonxiong/Desktop/DDP/feekg/api/demo.html`

### What You'll See

A beautiful purple gradient interface with:
- ✅ **Database Overview** button - Shows node/relationship counts
- ✅ **Get Entities** button - Lists all companies/banks
- ✅ **Get Events** button - Shows all financial events
- ✅ **Evolution Links** button - Shows how events connect
- ✅ **Visualization** buttons - Generate graphs live!

Click any button to see the data or visualizations!

---

## 🗄️ Option 3: Neo4j Browser (Graph Database)

### Open Neo4j Browser

```bash
open http://localhost:7474
```

Or just type `http://localhost:7474` in your browser.

### Login

- **Username:** `neo4j`
- **Password:** `feekg2024`

### Try These Queries

**1. See all events and their connections:**
```cypher
MATCH (e1:Event)-[r:EVOLVES_TO]->(e2:Event)
RETURN e1, r, e2
LIMIT 50
```

**2. See Evergrande's risks:**
```cypher
MATCH (e:Entity {name: 'China Evergrande Group'})<-[:TARGETS_ENTITY]-(r:Risk)
MATCH (r)-[:HAS_RISK_TYPE]->(rt:RiskType)
RETURN e, r, rt
```

**3. Find causal chains:**
```cypher
MATCH path = (e1:Event)-[:EVOLVES_TO*2..3]->(e2:Event)
WHERE all(r in relationships(path) WHERE r.causality > 0.7)
RETURN path
LIMIT 10
```

Click the **graph icon** in the top right to see a visual representation!

---

## 📊 Option 4: Terminal Demos (Text Output)

### Risk Analysis Demo

```bash
./venv/bin/python scripts/demo_risk_queries.py
```

This prints:
- Database overview
- Entity risk profiles
- Strongest evolution links
- Causal event chains
- Pattern detection
- Statistics

### Verification Scripts

```bash
# See if everything works
./venv/bin/python scripts/verify_stage6.py
```

---

## 🎯 Quick Start Comparison

| Method | What You See | How to Run | Best For |
|--------|--------------|------------|----------|
| **PNG Visualizations** | 8 static images | `./venv/bin/python scripts/demo_visualizations.py` then `open results/*.png` | Papers, presentations |
| **Web Demo** | Interactive interface | `./venv/bin/python api/app.py` then open `api/demo.html` | Exploring the data |
| **Neo4j Browser** | Interactive graph | `open http://localhost:7474` | Graph exploration |
| **Terminal** | Text output | `./venv/bin/python scripts/demo_risk_queries.py` | Quick checks |

---

## 🆘 Troubleshooting

### "No module named 'flask'" or similar

```bash
# Make sure you're using the venv Python
./venv/bin/python api/app.py

# NOT just:
python api/app.py
```

### API not connecting in demo.html

1. Make sure the API server is running (`./venv/bin/python api/app.py`)
2. Check that you see "Starting server on http://localhost:5000"
3. Refresh the demo page

### Neo4j not running

```bash
# Start Neo4j
./scripts/start_neo4j.sh

# Or if already created
docker start feekg-neo4j

# Check if running
docker ps | grep feekg-neo4j
```

### Images not opening

- **Mac:** Use `open results/three_layer_graph.png`
- **Linux:** Use `xdg-open results/three_layer_graph.png`
- **Windows:** Use `start results\three_layer_graph.png`
- **Or:** Just navigate to the `results/` folder and double-click

---

## 📝 Summary

**To see everything quickly:**

1. **Generate visualizations:** `./venv/bin/python scripts/demo_visualizations.py`
2. **View them:** `open results/*.png` (Mac) or just open the folder
3. **For interactive:** `./venv/bin/python api/app.py` then open `api/demo.html` in browser

That's it! Enjoy exploring your Financial Event Evolution Knowledge Graph! 🎉
