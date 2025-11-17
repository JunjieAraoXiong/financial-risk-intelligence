# FE-EKG Project Guide for Claude

## Project Overview

This is a complete implementation of the **FE-EKG (Financial Event Evolution Knowledge Graph)** system based on the paper:
> "Risk identification and management through knowledge Association: A financial event evolution knowledge graph approach" (Liu et al., 2024)

**Purpose:** Build a three-layer knowledge graph for financial risk analysis using the Evergrande crisis as a case study.

## Architecture

```
┌─────────────────────────────────────────────┐
│         Risk Layer (Top)                    │
│  [LiquidityRisk] → [CreditRisk]            │
│         ↓                ↓                   │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         Event Layer (Middle)                │
│  [DebtDefault] → [CreditDowngrade]         │
│         ↓                ↓                   │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         Entity Layer (Bottom)               │
│  [Evergrande] ←→ [MinshengBank]            │
└─────────────────────────────────────────────┘
```

## Technology Stack

- **Database:** Neo4j (via Docker) + AllegroGraph fallback
- **Backend:** Python 3.10+
- **Graph Library:** NetworkX, py2neo, neo4j-driver
- **Visualization:** Matplotlib, Pandas
- **API:** Flask + CORS
- **Data:** Hand-crafted Evergrande crisis events (2020-2022)

## Project Structure

```
feekg/
├── .env                      # Neo4j credentials (NOT in git)
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
├── CLAUDE.md                 # This file
├── STAGE6_SUMMARY.md         # Latest stage summary
│
├── config/                   # Configuration
│   ├── graph_backend.py      # Dual backend (Neo4j/AllegroGraph)
│   └── secrets.py            # Credential management
│
├── data/                     # Input data
│   └── evergrande_crisis.json  # 20 events, 10 entities, 10 risks
│
├── ontology/                 # Schema definitions
│   ├── feekg_minimal.ttl     # RDF/OWL schema
│   └── neo4j_schema.cypher   # Neo4j schema
│
├── ingestion/                # Data loading
│   └── load_evergrande.py    # Loader script
│
├── evolution/                # Event evolution methods
│   ├── methods.py            # 6 evolution algorithms
│   └── run_evolution.py      # Apply methods to data
│
├── query/                    # Query interface
│   ├── risk_queries.cypher   # 80+ Cypher templates
│   └── risk_analyzer.py      # Python query API
│
├── viz/                      # Visualizations
│   ├── graph_viz.py          # ThreeLayerVisualizer
│   └── plot_utils.py         # Plotting utilities
│
├── api/                      # REST API
│   ├── app.py                # Flask application (20+ endpoints)
│   ├── demo.html             # Interactive test page
│   └── README.md             # API documentation
│
├── scripts/                  # Utility scripts
│   ├── start_neo4j.sh        # Start Neo4j Docker
│   ├── verify_stage*.py      # Stage verification scripts
│   ├── demo_risk_queries.py  # Query demo
│   └── demo_visualizations.py # Visualization demo
│
└── results/                  # Output files
    ├── *.png                 # Generated visualizations
    └── evolution_links.json  # Computed evolution links
```

## Quick Start Commands

### 1. View Visualizations (PNG files)

```bash
# Generate all visualizations
./venv/bin/python scripts/demo_visualizations.py

# View the generated files (Mac)
open results/three_layer_graph.png
open results/evolution_network.png
open results/evolution_heatmap.png

# View all at once (Mac)
open results/*.png

# Or use any image viewer
```

### 2. Start the REST API

```bash
# Start the API server
./venv/bin/python api/app.py

# In another terminal, test it
curl http://localhost:5000/health
curl http://localhost:5000/api/info

# Or open the demo page in browser
open http://localhost:5000
# Then navigate to: api/demo.html
```

**Open in browser:** `file:///Users/hansonxiong/Desktop/DDP/feekg/api/demo.html`

### 3. Query the Database Directly

```bash
# Run interactive demo
./venv/bin/python scripts/demo_risk_queries.py

# Or use Neo4j Browser
open http://localhost:7474
# Username: neo4j, Password: feekg2024
```

## Implementation Stages

### ✅ Stage 1: Infrastructure
- Set up project structure
- Configure Neo4j via Docker
- Test database connection

### ✅ Stage 2: Schema
- Define three-layer ontology
- Create Neo4j schema with 12 risk types
- Implement dual backend support

### ✅ Stage 3: Data
- Hand-craft Evergrande crisis data
- 20 events spanning Aug 2020 - Aug 2022
- 10 entities, 10 risk instances
- Load into Neo4j

### ✅ Stage 4: Evolution Methods
Implemented 6 evolution algorithms from paper:
1. **Temporal Correlation** - TCDI formula: `TCDI(ΔT) = Ke^(-αΔT)`
2. **Entity Overlap** - Jaccard similarity of shared entities
3. **Semantic Similarity** - Keyword matching + event type
4. **Topic Relevance** - Event type categories (credit, market, etc.)
5. **Event Type Causality** - Domain-specific causal patterns
6. **Emotional Consistency** - Sentiment analysis (EVI score)

Results: 154 enhanced evolution links (avg score: 0.366)

### ✅ Stage 5: Queries
- 80+ Cypher query templates
- RiskAnalyzer Python class with 20+ methods
- Interactive demo script

### ✅ Stage 6: Visualizations & API
- ThreeLayerVisualizer class
- 8 types of visualizations
- Flask REST API with 20+ endpoints
- Interactive HTML demo page

### 🔜 Stage 7: ABM (Optional)
- Agent-Based Model simulation
- Risk propagation dynamics

## Key Files to Know

### Data
- `data/evergrande_crisis.json` - All input data (events, entities, risks)
- `results/evolution_links.json` - Computed evolution links

### Core Logic
- `evolution/methods.py` - 6 evolution algorithms (500+ lines)
- `query/risk_analyzer.py` - High-level query API (600+ lines)
- `viz/graph_viz.py` - Visualization engine (500+ lines)

### API
- `api/app.py` - REST API server (600+ lines)
- `api/demo.html` - Interactive test page

### Verification
- `scripts/verify_stage4.py` - Verify evolution methods
- `scripts/verify_stage5.py` - Verify queries
- `scripts/verify_stage6.py` - Verify visualizations + API

## Database Schema (Neo4j)

**Node Labels:**
- `Entity` - Companies, banks, regulators (10 instances)
- `Event` - Financial events (20 instances)
- `Risk` - Risk instances (10 instances)
- `RiskType` - Risk categories (12 types)
- `RiskSnapshot` - Temporal risk data

**Relationship Types:**
- `HAS_ACTOR` - Event → Entity (actor)
- `HAS_TARGET` - Event → Entity (target)
- `EVOLVES_TO` - Event → Event (154 enhanced links)
- `TARGETS_ENTITY` - Risk → Entity
- `HAS_RISK_TYPE` - Risk → RiskType
- `HAS_SNAPSHOT` - Risk → RiskSnapshot
- `INCREASES_RISK_OF` - Risk → Risk

## Evolution Link Properties

Each `EVOLVES_TO` relationship has:
- `score` - Overall evolution score (0-1)
- `type` - "enhanced" (vs old "temporal")
- `temporal` - Temporal correlation score
- `entity_overlap` - Entity overlap score
- `semantic` - Semantic similarity score
- `topic` - Topic relevance score
- `causality` - Event type causality score
- `emotional` - Emotional consistency score

## Common Tasks

### Add New Events

1. Edit `data/evergrande_crisis.json`
2. Add event to `events` array
3. Reload: `./venv/bin/python ingestion/load_evergrande.py`
4. Recompute evolution: `./venv/bin/python evolution/run_evolution.py`

### Create Custom Visualizations

```python
from viz.graph_viz import ThreeLayerVisualizer

viz = ThreeLayerVisualizer()
viz.create_evolution_network(min_score=0.6, save_path='my_viz.png')
viz.close()
```

### Run Custom Queries

```python
from query.risk_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer()
links = analyzer.get_strongest_evolution_links(min_score=0.5)
chains = analyzer.get_causal_chains(min_causality=0.7)
analyzer.close()
```

### Access API Programmatically

```python
import requests

# Get entities
response = requests.get('http://localhost:5000/api/entities')
entities = response.json()['data']

# Get evolution links
response = requests.get('http://localhost:5000/api/evolution/links?min_score=0.5')
links = response.json()['data']
```

## Environment Variables (.env)

```bash
# Backend selection
GRAPH_BACKEND=neo4j

# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=feekg2024
NEO4J_DB=neo4j

# AllegroGraph (fallback)
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_REPO=feekg_dev
```

## Troubleshooting

### Neo4j Not Running
```bash
# Check if Docker is running
docker ps

# Start Neo4j
./scripts/start_neo4j.sh

# Or manually
docker start feekg-neo4j
```

### Module Import Errors
```bash
# Ensure you're using venv
./venv/bin/python script.py

# Or activate venv
source venv/bin/activate  # Mac/Linux
python script.py
```

### API CORS Errors
- CORS is already enabled in `api/app.py`
- If issues persist, check browser console for specific errors

### Visualization Display Issues
- Ensure matplotlib backend is set correctly
- Use `plt.show()` for interactive display
- Or save to file and open separately

## Performance Notes

- **Small dataset**: 20 events = fast queries
- **Evolution computation**: ~154 links in <1 second
- **Visualization generation**: 1-3 seconds per image
- **API response time**: <100ms for queries, 1-3s for visualizations

## Future Development Ideas

1. **More Data Sources**
   - Integrate with EventKG
   - Pull from news APIs (GDELT, NewsAPI)
   - Add more case studies (Lehman, SVB, etc.)

2. **Advanced Analytics**
   - Time series risk forecasting
   - Monte Carlo simulations
   - Network centrality analysis

3. **Frontend**
   - React dashboard
   - Interactive D3.js graphs
   - Real-time updates via WebSockets

4. **Deployment**
   - Docker Compose for full stack
   - Kubernetes for scaling
   - Cloud deployment (AWS/GCP)

## References

- **Paper**: Liu et al. (2024) "Risk identification and management through knowledge Association"
- **Neo4j Docs**: https://neo4j.com/docs/
- **NetworkX**: https://networkx.org/
- **Flask**: https://flask.palletsprojects.com/

## Contact & Contributing

This is a research implementation. For questions or improvements:
1. Check documentation in `README.md` and `api/README.md`
2. Review stage summaries (`STAGE*_SUMMARY.md`)
3. Examine verification scripts in `scripts/`

## Current Status

**Stages 1-6: Complete ✅**
- ✅ Infrastructure working
- ✅ Data loaded (20 events, 10 entities, 10 risks)
- ✅ Evolution methods implemented (6 algorithms)
- ✅ Query system complete (80+ templates)
- ✅ Visualizations working (8 types)
- ✅ REST API running (20+ endpoints)

**Ready for:**
- Research analysis and publication
- Frontend development
- Real-world deployment
- Further extensions

---

Last Updated: 2025-11-10
Version: 1.0.0
Status: Production Ready
