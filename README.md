# FE-EKG: Financial Event Evolution Knowledge Graph

Implementation of the FEEKG paper: "Risk identification and management through knowledge Association: A financial event evolution knowledge graph approach"

**Tech Stack:** AllegroGraph (RDF) + Flask API + Next.js 15 | **Deploy:** Railway + Vercel | **Data:** 4,000 real Capital IQ events

**🌐 Frontend Repository:** https://github.com/JunjieAraoXiong/feekg-frontend

## 📚 Documentation

**Essential Guides:**
- **[📖 Documentation Index](docs/INDEX.md)** - Complete documentation catalog
- **[🔧 Developer Guide](CLAUDE.md)** - Technical guide for contributors
- **[🚀 Deployment](DEPLOYMENT.md)** - Railway + Vercel deployment guide
- **[🏗️ Architecture](ARCHITECTURE.md)** - System design and three-layer model

## 📊 Database: AllegroGraph (Production)

**Current Setup:**
- **Database:** AllegroGraph 8.4.0 (cloud-hosted)
- **Data:** 4,000 real financial events from Capital IQ (2007-2009 Lehman Brothers crisis)
- **Repository:** `mycatalog/FEEKG` @ qa-agraph.nelumbium.ai
- **Entities:** 22 major financial institutions (Morgan Stanley, Lehman Brothers, etc.)
- **Query Language:** SPARQL

> ⚠️ **Note:** Neo4j has been retired in favor of AllegroGraph. See [docs/ALLEGROGRAPH_SETUP.md](docs/ALLEGROGRAPH_SETUP.md) for details.

## 🚀 How to View Everything

### Option 1: Interactive HTML Visualizations

```bash
# Open interactive visualizations in browser
open results/optimized_knowledge_graph.html  # Main interactive graph
open results/timeline_view.html              # Timeline with 4,000 events
open results/dashboard.html                  # Statistics dashboard
```

**Available visualizations** (in `results/` folder):
- `optimized_knowledge_graph.html` (127KB) - Interactive network graph with zoom/pan/filter
- `timeline_view.html` (174KB) - Hierarchical timeline of 4,000 Lehman crisis events
- `dashboard.html` - Entity/Event/Risk statistics dashboard
- `interactive_kg_lehman_200.html` - Medium-scale graph (200 events)
- `clean_knowledge_graph.html` - Simplified graph view
- And 2 more...

See [docs/VISUALIZATIONS.md](docs/VISUALIZATIONS.md) for complete visualization documentation.

### Option 2: Next.js Frontend (Production Web App)

**Repository:** https://github.com/JunjieAraoXiong/feekg-frontend

A modern React-based frontend built with Next.js 15, featuring:
- 🎨 Interactive knowledge graph visualization (Cytoscape.js)
- 📊 Real-time data fetching with React Query
- 🎯 State management with Zustand
- 🎨 Tailwind CSS styling
- 📱 Responsive design

**Deploy to Vercel:**
```bash
# Frontend is ready for one-click Vercel deployment
# See "Deployment" section below for full instructions
```

### Option 3: Interactive API Demo (Web Browser)

```bash
# 1. Start the API server
./venv/bin/python api/app.py

# 2. Open the demo page in your browser
# Mac: open api/demo.html
# Or navigate to: file:///Users/hansonxiong/Desktop/DDP/feekg/api/demo.html
```

The demo page provides:
- ✅ Interactive buttons to test all API endpoints
- ✅ Live visualization generation
- ✅ Database statistics
- ✅ Query results display

### Option 4: AllegroGraph SPARQL Queries

```bash
# Check repository status
./venv/bin/python scripts/utils/check_feekg_mycatalog.py
```

See [docs/ALLEGROGRAPH_SETUP.md](docs/ALLEGROGRAPH_SETUP.md) for SPARQL query examples.

### Option 5: Run Query Demos (Terminal)

```bash
# Interactive demonstrations
./venv/bin/python scripts/demos/demo_feekg_capabilities.py

# This shows:
# - AllegroGraph connection test
# - Database statistics (4,000 events, 22 entities)
# - SPARQL query examples
# - Data quality metrics
```

## Project Structure

### Backend (This Repository)

```
feekg/
├── .env                    # AllegroGraph credentials (NOT committed)
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── README.md              # This file
│
├── config/                # Configuration and secrets
│   ├── __init__.py
│   └── secrets.py        # Secure credential loading
│
├── api/                  # Flask REST API
│   ├── app.py           # Main API server (20+ endpoints)
│   ├── demo.html        # Interactive demo page
│   └── README.md        # API documentation
│
├── scripts/              # Utility scripts
│   ├── demos/           # Demonstration scripts
│   └── utils/           # Utility functions
│
├── ontology/             # RDF schema definitions
├── data/                 # Sample data and inputs
│   ├── capital_iq_raw/  # Raw Capital IQ data
│   └── capital_iq_processed/  # Processed JSON
├── ingestion/            # Data loading scripts
├── evolution/            # Event evolution algorithms (6 methods)
├── query/                # SPARQL queries and NL interface
├── viz/                  # Visualization scripts
├── results/              # Output files (graphs, plots, HTML)
└── logs/                 # Log files and test results
```

### Frontend (Separate Repository)

**Repository:** https://github.com/JunjieAraoXiong/feekg-frontend

```
feekg-frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/              # API client and utilities
│   ├── hooks/            # Custom React hooks
│   └── stores/           # Zustand state management
├── public/               # Static assets
├── package.json          # Dependencies
├── next.config.js        # Next.js configuration
├── tailwind.config.ts    # Tailwind CSS setup
└── tsconfig.json         # TypeScript configuration
```

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

The `.env` file should already exist with your AllegroGraph credentials:

```bash
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_REPO=feekg_dev
```

**⚠️ NEVER commit the .env file to Git!**

### 3. Test Connection

```bash
python scripts/check_connection.py
```

Expected output:
```
✅ Connected successfully!
   Repository: feekg_dev
   Current size: X triples
   Latency: XX ms
```

## Three-Layer Architecture

FE-EKG implements a three-layer knowledge graph:

1. **Entity Layer** (Bottom): Companies, institutions, and their relationships
2. **Event Layer** (Middle): Financial events and their evolution chains
3. **Risk Layer** (Top): Risk types, transitions, and probabilities

```
Risk Layer:     [LiquidityRisk] ──0.7──> [CreditRisk]
                       ↑
Event Layer:    [DebtDefault] ──evolves──> [CreditDowngrade]
                       ↑                           ↑
Entity Layer:   [Evergrande] ─────────────> [Minsheng Bank]
```

## 🚀 Deployment

### Full-Stack Deployment Guide

The FE-EKG system consists of two components that can be deployed separately:

#### 1. Backend (Flask API) → Railway/Render

**Recommended: Railway** (Easy Python deployment with PostgreSQL support)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Deploy from backend directory
railway init
railway up

# Set environment variables in Railway dashboard:
# - AG_URL
# - AG_USER
# - AG_PASS
# - AG_CATALOG
# - AG_REPO
```

**Alternative: Render**
1. Connect your GitHub repository
2. Create new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn api.app:app`
5. Add environment variables (same as above)

**Alternative: Fly.io**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

#### 2. Frontend (Next.js) → Vercel

**Repository:** https://github.com/JunjieAraoXiong/feekg-frontend

The frontend is **perfectly optimized for Vercel** deployment:

```bash
# Method 1: One-Click Deploy (Recommended)
# 1. Visit https://vercel.com/new
# 2. Import: https://github.com/JunjieAraoXiong/feekg-frontend
# 3. Set environment variables:
#    NEXT_PUBLIC_API_URL=https://your-backend.railway.app
#    NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
#    NEXT_PUBLIC_MAX_NODES=1000
# 4. Click Deploy!

# Method 2: Vercel CLI
npm i -g vercel
git clone https://github.com/JunjieAraoXiong/feekg-frontend.git
cd feekg-frontend
vercel --prod
```

**Environment Variables for Vercel:**
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

#### 3. CORS Configuration

After deploying both backend and frontend, update CORS in `api/app.py`:

```python
# Update CORS origins to include your Vercel domain
CORS(app, origins=[
    "http://localhost:3000",  # Local development
    "https://your-app.vercel.app",  # Production frontend
])
```

Then redeploy the backend.

#### 4. Deployment Checklist

- [ ] Deploy Flask backend to Railway/Render/Fly.io
- [ ] Get backend URL (e.g., `https://feekg-api.up.railway.app`)
- [ ] Deploy Next.js frontend to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` environment variable in Vercel
- [ ] Update CORS configuration in backend
- [ ] Redeploy backend with updated CORS
- [ ] Test frontend connects to backend successfully

**Expected Result:**
- Backend API: `https://your-backend.railway.app/health` → `{"status": "healthy"}`
- Frontend: `https://your-app.vercel.app` → Interactive knowledge graph

## Development Status

**Backend (This Repository):**
- [x] **AllegroGraph Migration**: Migrated from Neo4j to AllegroGraph (cloud-hosted RDF triplestore) ✅
- [x] **Capital IQ Data**: Loaded 4,000 real financial events from 2007-2009 Lehman Brothers crisis ✅
- [x] **CSV Traceability**: Full data lineage with row numbers and Capital IQ IDs ✅
- [x] **Event Evolution**: 6 evolution algorithms (temporal, entity, semantic, topic, causal, emotional) ✅
- [x] **SPARQL Queries**: Query system with Python API ✅
- [x] **Interactive Visualizations**: 7 HTML visualizations with vis.js (network graphs, timeline, dashboard) ✅
- [x] **REST API**: 20+ endpoints for data access and visualization generation ✅
- [x] **Railway Deployment**: Production-ready deployment configuration ✅

**Frontend (Separate Repository):**
- [x] **Next.js 15**: Modern React framework with App Router ✅
- [x] **Cytoscape.js**: Interactive knowledge graph visualization ✅
- [x] **React Query**: Efficient server state management ✅
- [x] **Zustand**: UI state management ✅
- [x] **Vercel Ready**: One-click deployment configuration ✅

**Future Enhancements:**
- [ ] **Evolution Links Computation**: Apply 6 methods to 4,000 events
- [ ] **Advanced Analytics Dashboard**: Risk forecasting and network analysis
- [ ] **Real-time Updates**: WebSocket integration for live data
- [ ] **Mobile App**: React Native version

## Usage Guide

### Connecting to AllegroGraph

```bash
# Test connection
./venv/bin/python scripts/utils/check_feekg_mycatalog.py

# Expected output:
# ✅ Connected to AllegroGraph
# 📊 Total triples: 59,090
# 📅 Events: 4,000
# 👥 Entities: 22
```

### Running Demos

```bash
# Interactive capabilities demo
./venv/bin/python scripts/demos/demo_feekg_capabilities.py

# View visualizations
open results/optimized_knowledge_graph.html
open results/timeline_view.html
open results/dashboard.html
```

### Starting the REST API

```bash
# Start the API server
./venv/bin/python api/app.py

# Or use Python directly
python api/app.py
```

The API will be available at **http://localhost:5000**

Test it:
```bash
# Health check
curl http://localhost:5000/health

# Get all entities
curl http://localhost:5000/api/entities

# Get evolution links
curl "http://localhost:5000/api/evolution/links?min_score=0.5"

# Get graph data for frontend visualization
curl http://localhost:5000/api/graph/data
```

See [api/README.md](api/README.md) for complete API documentation.
```

### Using SPARQL Queries

```python
import requests
from requests.auth import HTTPBasicAuth

url = 'https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG'
auth = HTTPBasicAuth('sadmin', '279H-Dt<>,YU')

# Query entities
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

for r in results:
    print(f"{r['label']['value']} ({r['type']['value']})")
```

See [docs/ALLEGROGRAPH_SETUP.md](docs/ALLEGROGRAPH_SETUP.md) for more SPARQL examples.

## 📋 Quick Reference

### All Important Commands

```bash
# =============================================================================
# INTERACTIVE VISUALIZATIONS
# =============================================================================

# Open interactive HTML visualizations in browser
open results/optimized_knowledge_graph.html  # Main interactive graph
open results/timeline_view.html              # Timeline with 4,000 events
open results/dashboard.html                  # Statistics dashboard

# =============================================================================
# REST API
# =============================================================================

# Start API server → http://localhost:5000
./venv/bin/python api/app.py

# Test API endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/info
curl http://localhost:5000/api/entities

# Open interactive demo page (in browser)
# Navigate to: file:///Users/hansonxiong/Desktop/DDP/feekg/api/demo.html

# =============================================================================
# ALLEGROGRAPH QUERIES
# =============================================================================

# Check AllegroGraph repository status
./venv/bin/python scripts/utils/check_feekg_mycatalog.py

# Run interactive capabilities demo
./venv/bin/python scripts/demos/demo_feekg_capabilities.py

# =============================================================================
# DATA MANAGEMENT
# =============================================================================

# Load Capital IQ data to AllegroGraph
./venv/bin/python ingestion/load_capital_iq_to_allegrograph.py

# Recompute evolution links (SPARQL-based)
./venv/bin/python evolution/run_evolution_ag.py
```

### Important Files & Locations

| What | Where | Description |
|------|-------|-------------|
| **Production Frontend** | [GitHub Repo](https://github.com/JunjieAraoXiong/feekg-frontend) | Next.js 15 web app (Vercel-ready) |
| **Interactive Visualizations** | `results/*.html` | 7 interactive HTML visualizations |
| **API Demo** | `api/demo.html` | Interactive web interface |
| **API Docs** | `api/README.md` | Complete API documentation |
| **Developer Guide** | `CLAUDE.md` | Comprehensive project guide |
| **Deployment Guide** | `DEPLOYMENT.md` | Railway + Vercel instructions |
| **AllegroGraph Setup** | `docs/ALLEGROGRAPH_SETUP.md` | Setup guide and SPARQL examples |
| **Visualizations** | `docs/VISUALIZATIONS.md` | Visualization documentation |
| **Capital IQ Data** | `data/capital_iq_raw/` | Raw transaction data (2007-2009) |
| **Processed Data** | `data/capital_iq_processed/` | Classified Lehman events |
| **Documentation Index** | `docs/INDEX.md` | Complete docs catalog |

### Quick API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/info` | Database overview |
| `GET /api/entities` | All entities |
| `GET /api/events` | All events |
| `GET /api/evolution/links?min_score=0.5` | Evolution links |
| `GET /api/evolution/chains` | Causal chains |
| `GET /api/risks` | All risks |
| `GET /api/graph/data` | Graph data for D3.js |
| `GET /api/visualizations/three-layer` | Generate 3-layer viz |

See `api/README.md` for complete API documentation.

## Security Notes

- All credentials are stored in `.env` (excluded from Git)
- Passwords are masked in logs and error messages
- Use `config.secrets.get_masked_config()` for safe logging

## References

### Research & Data
- Paper: Liu et al. (2024) "Risk identification and management through knowledge Association"
- AllegroGraph: https://allegrograph.com/
- EventKG: https://eventkg.l3s.uni-hannover.de/
- Capital IQ: Professional financial data source

### Backend Technologies
- Flask: https://flask.palletsprojects.com/
- NetworkX: https://networkx.org/
- RDFLib: https://rdflib.readthedocs.io/
- SPARQL: https://www.w3.org/TR/sparql11-query/

### Frontend Technologies
- Next.js 15: https://nextjs.org/
- React Query (TanStack): https://tanstack.com/query/latest
- Zustand: https://zustand-demo.pmnd.rs/
- Cytoscape.js: https://js.cytoscape.org/
- Tailwind CSS: https://tailwindcss.com/

### Deployment Platforms
- Vercel (Frontend): https://vercel.com/
- Railway (Backend): https://railway.app/
- AllegroGraph Cloud: https://allegrograph.com/products/allegrograph/

## License

This project is for research and educational purposes.
