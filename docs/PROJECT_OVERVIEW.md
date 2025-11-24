# FE-EKG Project Overview

## About the Project

Implementation of the **FE-EKG (Financial Event Evolution Knowledge Graph)** system based on:
> "Risk identification and management through knowledge Association: A financial event evolution knowledge graph approach" (Liu et al., 2024)

**Purpose:** Build a three-layer knowledge graph for financial risk analysis using real Capital IQ data from the 2007-2009 Lehman Brothers crisis.

---

## Architecture

```
┌─────────────────────────────────────┐
│   RISK LAYER (Why?)                 │
│   [LiquidityRisk] → [CreditRisk]    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   EVENT LAYER (What?)               │
│   [Bankruptcy] → [CreditDowngrade]  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   ENTITY LAYER (Who?)               │
│   [Lehman Brothers] ↔ [AIG]         │
└─────────────────────────────────────┘
```

---

## Technology Stack

- **Database:** AllegroGraph 8.4.0 (cloud-hosted RDF triplestore)
- **Backend:** Python 3.10+, Flask REST API
- **AI:** NVIDIA NIM embeddings, Local SLM (Llama-3.2-1B)
- **Graph:** NetworkX, RDFLib
- **Visualization:** Matplotlib, Cytoscape.js
- **Data:** Capital IQ Lehman Brothers crisis (2007-2009) - 5,105 events

---

## Current Status

### Overall Progress: 60%

```
[████████████████░░░░░░░░░░░░] 60% Complete

✅ Knowledge Graph (100%)
✅ ABM Foundation (100%)
⏳ RAG System (80%)
⏳ SLM Integration (50%)
```

### Component Status

| Component | Status | Key Deliverables |
|-----------|--------|------------------|
| **FE-EKG KG** | ✅ Complete | 5,105 events, 31,173 evolution links, 429K triples |
| **ABM** | ✅ Foundation | 3 agent classes, crisis simulator, metrics |
| **RAG** | ⏳ In Progress | ChromaDB (442K chunks), reranker, query generator |
| **SLM** | ⏳ In Progress | Llama-3.2-1B integration with ABM |

### What's Working

- Query financial events by type, date, entity
- Compute evolution links (6 algorithms)
- Visualize 3-layer graph
- REST API at localhost:5000
- ABM crisis simulation
- RAG retrieval from historical documents

---

## Research Context

### Research Question
**How does access to historical financial intelligence (via RAG) improve risk-aware decision-making compared to uninformed SLM agents in a financial ABM?**

### Hypotheses

1. **H1**: RAG-enabled agents make more contextually appropriate decisions across market regimes
2. **H2**: Information gap appears as measurable differences in decision consistency, timing, survival
3. **H3**: RAG retrieval quality correlates with agent decision quality

### Key Experiments

**Information Asymmetry Experiment:**
- **Group A (Insiders)**: RAG-enabled agents with historical context
- **Group B (Noise Traders)**: SLM-only agents (hallucination-prone)
- **Metric**: Survival rate, decision distribution, capital preservation

### Papers Planned

1. **Paper 1**: FE-EKG implementation (reference - Liu et al. 2024)
2. **Paper 2**: Knowledge-Grounded ABM (primary contribution)
3. **Paper 3**: SLM for Crisis Decision-Making (secondary)

---

## Quick Start

### Check AllegroGraph Connection
```bash
./venv/bin/python scripts/check_feekg_mycatalog.py
```

### Start the REST API
```bash
./venv/bin/python api/app.py
curl http://localhost:5000/health
```

### Run ABM Experiment
```bash
source .env && export PYTHONPATH=. && export TOKENIZERS_PARALLELISM=false
python run_experiment.py --liquidity-factor 0.20
```

### Test RAG Retrieval
```bash
python rag/test_retrieval.py
```

---

## Key Numbers

- **77,590** → **5,105** → **31,173** (Capital IQ events → filtered → evolution links)
- **429,019** RDF triples
- **442,963** RAG chunks (3,198 documents)
- **<100ms** query speed
- **6** evolution algorithms
- **22** financial institutions

---

## Directory Structure

```
feekg/
├── abm/           # Agent-Based Model (Mesa)
├── api/           # Flask REST API
├── docs/          # Documentation
├── feekg_core/    # KG core (evolution, ingestion, query, viz)
├── ontology/      # RDF/OWL schema
├── rag/           # RAG pipeline (ChromaDB, retriever)
├── results/       # Output files
├── scripts/       # Utility scripts
├── shared/        # Shared config (backends)
└── slm/           # Local SLM (Llama)
```

---

## Environment Setup

```bash
# .env file
GRAPH_BACKEND=allegrograph
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=<password>
AG_CATALOG=mycatalog
AG_REPO=FEEKG
OPENAI_API_KEY=<key>
```

---

## References

- **Paper**: Liu et al. (2024) "Risk identification and management through knowledge Association"
- **AllegroGraph**: https://franz.com/agraph/support/documentation/
- **Mesa ABM**: https://mesa.readthedocs.io/
- **LangChain**: https://python.langchain.com/

---

**Last Updated:** November 2024
**Version:** 2.0.0 (AllegroGraph + RAG)
**Status:** Active Development
