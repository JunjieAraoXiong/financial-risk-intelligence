# Getting Started with FE-EKG

**Fast track to exploring the Financial Event Evolution Knowledge Graph**

---

## 5-Minute Quick Start

### Option 1: View Interactive Visualizations (No Setup Required)

The fastest way to explore FE-EKG is through the interactive HTML visualizations:

```bash
# Open the main interactive knowledge graph
open results/optimized_knowledge_graph.html

# View the timeline of 4,000 Lehman crisis events
open results/timeline_view.html

# Explore the dashboard with statistics
open results/dashboard.html
```

**What you'll see:**
- Interactive network graphs with zoom/pan/filter
- 4,000 real financial events from the 2007-2009 crisis
- 22 major financial institutions
- Event evolution chains

**Features:**
- Click nodes to see details
- Zoom and pan to explore
- Filter by entity type or event type
- No installation required!

---

### Option 2: Browse All Documentation (Recommended)

Open the interactive documentation terminal:

```bash
open docs_hub.html
```

**Features:**
- Search across 50+ markdown files
- Organized categories (Getting Started, Deployment, API, etc.)
- Terminal-style interface
- In-browser markdown rendering

**Pro tip:** Press `Ctrl+K` to quick-search documentation!

---

### Option 3: Run the REST API

If you want to query the data programmatically:

```bash
# 1. Start the Flask API server
./venv/bin/python api/app.py

# 2. In another terminal, test it
curl http://localhost:5000/health
curl http://localhost:5000/api/info

# 3. Or open the interactive demo page
open api/demo.html
```

**Available at:** http://localhost:5000

---

## What is FE-EKG?

FE-EKG (Financial Event Evolution Knowledge Graph) is a complete implementation of a research paper for analyzing financial crisis contagion through knowledge graphs.

**Key Components:**
1. **Knowledge Graph** - 4,000 real events from Capital IQ (Lehman Brothers crisis)
2. **AllegroGraph Database** - Production RDF triplestore (59,090 triples)
3. **REST API** - Flask backend with 20+ endpoints
4. **Next.js Frontend** - Modern React-based web interface
5. **Agent-Based Model** - Simulate financial contagion with Mesa framework

**Research Paper:**
Liu et al. (2024) - "Risk identification and management through knowledge Association: A financial event evolution knowledge graph approach"

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     FE-EKG System                       │
└─────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Next.js    │──────│  Flask API   │──────│ AllegroGraph │
│   Frontend   │ HTTP │   Backend    │SPARQL│   Database   │
│  (Vercel)    │      │  (Railway)   │      │   (Cloud)    │
└──────────────┘      └──────────────┘      └──────────────┘
       │                     │                      │
       │                     │                      │
       ▼                     ▼                      ▼
  React Query         Evolution Methods      59,090 Triples
  Cytoscape.js        6 Algorithms          4,000 Events
  Zustand State       SPARQL Queries        22 Entities
```

---

## Next Steps by Use Case

### For Researchers
1. **View the data:** Open interactive visualizations
2. **Read the case study:** `docs/CASE_STUDY_LEHMAN.md`
3. **Understand methods:** `EVOLUTION_IMPLEMENTATION.md`
4. **Query the graph:** `ALLEGROGRAPH_MIGRATION.md` (SPARQL examples)

### For Developers
1. **Read the guide:** `CLAUDE.md` - Complete technical reference
2. **Setup local environment:** See "Development Setup" below
3. **Explore the API:** `api/README.md`
4. **Architecture details:** `FRONTEND_ARCHITECTURE.md`

### For Deployment
1. **Production deployment:** `DEPLOYMENT_GUIDE.md`
2. **Backend to Railway:** `RAILWAY_DEPLOYMENT.md`
3. **Frontend to Vercel:** `VERCEL_DEPLOYMENT.md`

### For Data Scientists
1. **Data quality report:** `DATA_QUALITY_REPORT.md`
2. **Data pipeline:** `docs/DATA_PIPELINE.md`
3. **Evolution algorithms:** `EVOLUTION_IMPLEMENTATION.md`
4. **SPARQL queries:** `QUICK_ANALYSIS_GUIDE.md`

---

## Development Setup (30 Minutes)

### Prerequisites
- Python 3.10+
- Virtual environment
- AllegroGraph credentials (provided in `.env`)

### Installation

```bash
# 1. Clone the repository (if needed)
cd /Users/hansonxiong/Desktop/DDP/feekg

# 2. Create virtual environment (if not exists)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify credentials exist
cat .env
# Should show:
# AG_URL=https://qa-agraph.nelumbium.ai/
# AG_USER=sadmin
# AG_PASS=...
# AG_CATALOG=mycatalog
# AG_REPO=FEEKG

# 5. Test connection
./venv/bin/python scripts/utils/check_feekg_mycatalog.py
```

**Expected output:**
```
✅ Connected to AllegroGraph
📊 Total triples: 59,090
📅 Events: 4,000
👥 Entities: 22
```

---

## Common Commands

### View Visualizations
```bash
# Interactive HTML visualizations
open results/optimized_knowledge_graph.html
open results/timeline_view.html
open results/dashboard.html
```

### Run API Server
```bash
# Start Flask backend
./venv/bin/python api/app.py

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/entities
curl http://localhost:5000/api/graph/data
```

### Query AllegroGraph
```bash
# Check repository status
./venv/bin/python scripts/utils/check_feekg_mycatalog.py

# Run capabilities demo
./venv/bin/python scripts/demos/demo_feekg_capabilities.py
```

### Run ABM Simulation
```bash
# Agent-Based Model simulation
./venv/bin/python abm/test_simulation.py

# Output: results/abm_simulation_results.json
```

---

## Key Files & Locations

| What | Where | Description |
|------|-------|-------------|
| **Interactive Docs** | `docs_hub.html` | Browse all documentation |
| **Main Guide** | `CLAUDE.md` | Complete technical reference |
| **API Docs** | `api/README.md` | REST API documentation |
| **Deployment** | `DEPLOYMENT_GUIDE.md` | Production deployment |
| **Case Study** | `docs/CASE_STUDY_LEHMAN.md` | Lehman Brothers analysis |
| **Frontend Repo** | [GitHub](https://github.com/JunjieAraoXiong/feekg-frontend) | Next.js frontend |
| **Data Quality** | `DATA_QUALITY_REPORT.md` | 4,000 events analysis |
| **Visualizations** | `results/*.html` | Interactive graphs |

---

## Frequently Asked Questions

### How do I view the knowledge graph?
Open `results/optimized_knowledge_graph.html` in your browser. No setup required!

### Where is the database?
AllegroGraph is cloud-hosted at `qa-agraph.nelumbium.ai`. Credentials are in `.env`.

### How do I query the data?
Three ways:
1. **REST API** - `curl http://localhost:5000/api/entities`
2. **SPARQL** - See `ALLEGROGRAPH_MIGRATION.md`
3. **Interactive visualizations** - Click and explore HTML files

### What happened to Neo4j?
Neo4j was retired. We now use AllegroGraph exclusively (production RDF triplestore).

### How do I deploy this?
See `DEPLOYMENT_GUIDE.md` for complete instructions (Railway + Vercel).

### Where's the frontend?
Separate repository: https://github.com/JunjieAraoXiong/feekg-frontend

### How do I run the ABM simulation?
```bash
./venv/bin/python abm/test_simulation.py
```

### Where's the real data from?
Capital IQ - 4,000 events from the 2007-2009 Lehman Brothers financial crisis.

---

## Project Status

**Current Version:** 2.1.0
**Last Updated:** 2025-11-16

**Completed:**
- ✅ AllegroGraph migration (production ready)
- ✅ 4,000 real Capital IQ events loaded
- ✅ 6 evolution algorithms implemented
- ✅ REST API with 20+ endpoints
- ✅ Interactive HTML visualizations
- ✅ Next.js frontend (separate repo)
- ✅ Agent-Based Model (Mesa framework)
- ✅ Railway deployment ready

**In Progress:**
- 🔄 Evolution link computation on 4,000 events
- 🔄 Advanced analytics dashboard

---

## Get Help

- **Documentation Hub:** Open `docs_hub.html` and search
- **Technical Guide:** Read `CLAUDE.md`
- **API Reference:** See `api/README.md`
- **Issues:** Check existing documentation first

---

## Quick Reference Card

```bash
# ===== INTERACTIVE EXPLORATION =====
open results/optimized_knowledge_graph.html  # Main graph
open results/timeline_view.html              # Timeline
open docs_hub.html                           # All docs

# ===== API SERVER =====
./venv/bin/python api/app.py                 # Start server
curl http://localhost:5000/health            # Test

# ===== DATABASE =====
./venv/bin/python scripts/utils/check_feekg_mycatalog.py  # Status

# ===== SIMULATION =====
./venv/bin/python abm/test_simulation.py     # Run ABM

# ===== DOCUMENTATION =====
open docs_hub.html                           # Search all docs
cat CLAUDE.md                                # Technical guide
cat DEPLOYMENT_GUIDE.md                      # Deploy to prod
```

---

**Ready to dive in?** Start with the interactive visualizations, then explore the documentation hub!
