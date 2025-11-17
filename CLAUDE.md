# FE-EKG Project Guide for Claude

## Project Overview

This is a complete implementation of the **FE-EKG (Financial Event Evolution Knowledge Graph)** system based on the paper:
> "Risk identification and management through knowledge Association: A financial event evolution knowledge graph approach" (Liu et al., 2024)

**Purpose:** Build a three-layer knowledge graph for financial risk analysis using real Capital IQ data from the 2007-2009 Lehman Brothers financial crisis.

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

- **Database:** AllegroGraph 8.4.0 (cloud-hosted RDF triplestore) ⭐ **PRIMARY**
- **Backend:** Python 3.10+
- **Graph Library:** NetworkX, RDFLib, requests (SPARQL)
- **Visualization:** Matplotlib, Pandas
- **API:** Flask + CORS
- **Data:** Capital IQ Lehman Brothers crisis (2007-2009) - 4,000 real financial events

> **⚠️ Note:** Neo4j has been **retired**. We now use AllegroGraph exclusively. See [ALLEGROGRAPH_MIGRATION.md](ALLEGROGRAPH_MIGRATION.md).

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
│   ├── graph_backend.py      # Backend abstraction
│   ├── rdf_backend.py        # AllegroGraph RDF client
│   └── secrets.py            # Credential management
│
├── data/                     # Input data
│   ├── capital_iq_raw/       # Raw Capital IQ CSV files
│   ├── capital_iq_processed/ # Processed JSON (4,000 events)
│   └── evergrande_crisis.json  # Legacy: 20 events (not in AllegroGraph)
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

### 1. Check AllegroGraph Connection

```bash
# Verify connection and data
./venv/bin/python scripts/check_feekg_mycatalog.py
```

### 2. View Visualizations (PNG files)

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

### 3. Query AllegroGraph (SPARQL)

```python
# Query using SPARQL
import requests
from requests.auth import HTTPBasicAuth

url = 'https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG'
auth = HTTPBasicAuth('sadmin', '279H-Dt<>,YU')

query = '''
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?entity ?label ?type
WHERE {
    ?entity a feekg:Entity .
    ?entity feekg:label ?label .
    ?entity feekg:entityType ?type .
}
LIMIT 10
'''

response = requests.post(url, data={'query': query},
                        headers={'Accept': 'application/sparql-results+json'},
                        auth=auth)
results = response.json()['results']['bindings']
```

See [ALLEGROGRAPH_MIGRATION.md](ALLEGROGRAPH_MIGRATION.md) for more SPARQL examples.

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

## Database Schema (AllegroGraph RDF)

**RDF Classes:**
- `feekg:Entity` - Companies, banks, regulators (22 institutions)
- `feekg:Event` - Financial events (4,000 events from 2007-2009)
- `feekg:Risk` - Risk instances (as available)

**RDF Properties:**
- `feekg:label` - Human-readable name
- `feekg:entityType` - Type (investment_bank, bank, insurance, etc.)
- `feekg:eventType` - Event category (merger_acquisition, capital_raising, etc.)
- `feekg:date` - Event date
- `feekg:description` - Event description
- `feekg:actor` - Event → Entity (actor)
- `feekg:involves` - Event → Entity (participant)
- `feekg:evolvesTo` - Event → Event (evolution link)

**CSV Traceability Properties:**
- `feekg:csvRowNumber` - Original CSV row number
- `feekg:csvFilename` - Source CSV file
- `feekg:capitalIqId` - Capital IQ unique identifier
- `feekg:classificationConfidence` - Classification confidence score
- `feekg:classificationMethod` - Classification method used

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

### Query AllegroGraph Data

See [ALLEGROGRAPH_MIGRATION.md](ALLEGROGRAPH_MIGRATION.md) for comprehensive SPARQL examples.

```bash
# Quick check
./venv/bin/python scripts/check_feekg_mycatalog.py
```

### Load More Capital IQ Data

```bash
# Process new CSV data
./venv/bin/python ingestion/process_capital_iq_v3.py

# Load to AllegroGraph
./venv/bin/python ingestion/load_capital_iq_to_allegrograph.py
```

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
# Backend Selection - AllegroGraph Only (Production)
GRAPH_BACKEND=allegrograph

# AllegroGraph Connection Details (Primary Database)
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_CATALOG=mycatalog
AG_REPO=FEEKG

# Neo4j Connection Details (DEPRECATED - Not in use)
# Neo4j has been retired in favor of AllegroGraph
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASS=feekg2024
# NEO4J_DB=neo4j
```

## Troubleshooting

### AllegroGraph Connection Issues
```bash
# Test connection
./venv/bin/python scripts/check_feekg_mycatalog.py

# Or manual test with curl
curl -u sadmin:PASSWORD \
  "https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG/size"
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

- **Production dataset**: 4,000 events from Capital IQ
- **AllegroGraph**: Cloud-hosted, fast SPARQL queries
- **Triple count**: 59,090 triples
- **Query response time**: <500ms for most SPARQL queries
- **Visualization generation**: 1-3 seconds per image
- **Data traceability**: Full CSV lineage for all events

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
- **AllegroGraph Docs**: https://franz.com/agraph/support/documentation/
- **SPARQL Tutorial**: https://www.w3.org/TR/sparql11-query/
- **NetworkX**: https://networkx.org/
- **Flask**: https://flask.palletsprojects.com/
- **Capital IQ**: Professional financial data source

## Contact & Contributing

This is a research implementation. For questions or improvements:
1. Check documentation in `README.md` and `api/README.md`
2. Review stage summaries (`STAGE*_SUMMARY.md`)
3. Examine verification scripts in `scripts/`

## Current Status

**AllegroGraph Migration: Complete ✅ (2025-11-15)**
- ✅ Neo4j retired, AllegroGraph is now the exclusive database
- ✅ Production data loaded: 4,000 Capital IQ events (2007-2009 Lehman crisis)
- ✅ 59,090 RDF triples with full CSV traceability
- ✅ 22 major financial entities (Morgan Stanley, Lehman Brothers, etc.)
- ✅ SPARQL query interface operational
- ✅ Evolution methods tested and compatible

**Implementation Complete:**
- ✅ Infrastructure working (cloud-hosted AllegroGraph)
- ✅ Real production data loaded (4,000 events vs 20 synthetic)
- ✅ Evolution methods implemented (6 algorithms)
- ✅ Query system complete (SPARQL-based)
- ✅ Visualizations working (8 types)
- ✅ REST API running (20+ endpoints)
- ✅ CSV traceability for data lineage

**Ready for:**
- Research analysis and publication (real Capital IQ data)
- Evolution link computation on 4,000 events
- SPARQL-based risk analysis
- Frontend development
- Team collaboration (shared cloud database)

---

Last Updated: 2025-11-15
Version: 2.0.0 (AllegroGraph)
Status: Production Ready
Database: AllegroGraph @ qa-agraph.nelumbium.ai
