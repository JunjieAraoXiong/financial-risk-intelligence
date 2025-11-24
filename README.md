# Financial Risk Intelligence

Comparing structured (Knowledge Graph) vs unstructured (RAG) approaches to financial risk intelligence in multi-agent crisis simulations.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Research Question

**How does information structure affect crisis decision-making?**

We compare two approaches to financial risk intelligence in an agent-based model:

| Approach | Method | Strengths |
|----------|--------|-----------|
| **FE-EKG (Structured)** | Explicit causal chains, SPARQL queries, rule-based risk propagation | High precision, traceability |
| **RAG (Unstructured)** | Semantic similarity over documents, LLM-based interpretation | Flexibility, coverage |

## Key Contribution

We study how information quality affects both **individual agent decisions** and **system-level stability** by comparing:
- **Group A (Insiders):** RAG-enabled agents with historical financial context
- **Group B (Noise Traders):** Uninformed SLM agents prone to hallucination

## Hypotheses

- **H1:** RAG-enabled agents make more contextually appropriate decisions across market regimes
- **H2:** Information asymmetry manifests as differences in decision consistency, risk timing, and survival
- **H3:** RAG retrieval quality correlates with agent decision quality

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ABM Simulation                        │
│  ┌─────────────┐              ┌─────────────┐           │
│  │  Group A    │              │  Group B    │           │
│  │  (RAG)      │              │  (No RAG)   │           │
│  └──────┬──────┘              └──────┬──────┘           │
│         │                            │                   │
│         ▼                            ▼                   │
│  ┌─────────────┐              ┌─────────────┐           │
│  │ Historical  │              │ SLM Only    │           │
│  │ Context     │              │ (Halluci-   │           │
│  │ (442K docs) │              │  nation)    │           │
│  └─────────────┘              └─────────────┘           │
└─────────────────────────────────────────────────────────┘

Knowledge Graph (FE-EKG)          RAG Pipeline
┌─────────────────────┐     ┌─────────────────────┐
│ Risk Layer          │     │ ChromaDB            │
│ [Liquidity]→[Credit]│     │ 442K chunks         │
│        ↑            │     │ BGE embeddings      │
│ Event Layer         │     │ Reranker            │
│ [Default]→[Downgrade│     │                     │
│        ↑            │     │ Sources:            │
│ Entity Layer        │     │ - JPM Weekly        │
│ [Lehman]→[Morgan]   │     │ - BIS Reports       │
└─────────────────────┘     │ - FT Archive        │
                            │ - FCIC Report       │
                            └─────────────────────┘
```

## Tech Stack

- **Knowledge Graph:** AllegroGraph (RDF/SPARQL), 59K triples
- **RAG:** ChromaDB + BGE embeddings + Reranker
- **ABM:** Mesa framework
- **SLM:** Llama 3.2 1B Instruct
- **API:** Flask + CORS
- **Data:** 4,000 Capital IQ events (2007-2009 Lehman crisis)

## Quick Start

### 1. Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Create `.env`:

```bash
# AllegroGraph
AG_URL=https://your-instance.com/
AG_USER=your_user
AG_PASS=your_password
AG_CATALOG=mycatalog
AG_REPO=FEEKG
```

### 3. Run Experiment

```bash
source .env && export PYTHONPATH=. && export TOKENIZERS_PARALLELISM=false
python run_experiment.py --liquidity-factor 0.15
```

### 4. Run API

```bash
python api/app.py
# Available at http://localhost:5000
```

## Project Structure

```
├── abm/              # Agent-based model (Mesa)
│   ├── agents.py     # BankAgent with use_rag flag
│   └── model.py      # CrisisModel simulation
├── rag/              # RAG pipeline
│   ├── retriever.py  # ChromaDB retrieval
│   ├── reranker.py   # BGE reranker
│   └── evaluation.py # RAG metrics
├── slm/              # Small language model
│   └── llama_client.py
├── evolution/        # 6 event evolution algorithms
├── query/            # SPARQL queries
├── api/              # Flask REST API
├── config/           # Configuration
└── data/             # Capital IQ data
```

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Simulation length | 52 weeks |
| Banks | 10 (5 RAG, 5 non-RAG) |
| Initial capital | 100B each |
| Shock week | Week 5 (testing) |
| Pre-shock volatility | 10% |
| Post-shock volatility | 80% |

### Parameter Sweep

| Run | Liquidity Factor | Stress Level |
|-----|------------------|--------------|
| 1 | 0.30 | Mild |
| 2 | 0.20 | Moderate |
| 3 | 0.15 | Significant |
| 4 | 0.10 | Severe |

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| Survival Rate | % of each group alive at end |
| Decision Distribution | DEFENSIVE vs MAINTAIN counts |
| Capital Preservation | Final capital comparison |
| Response Quality | Source citations vs hallucinations |

## RAG Dataset

| Source | Files | Coverage |
|--------|-------|----------|
| JPM Weekly (2002-2009) | 366 | Credit, liquidity, market risks |
| BIS Annual (1931-2024) | 94 | Systemic risk, banking stability |
| BIS Quarterly (1997-2024) | 114 | Cross-border risks, derivatives |
| FT Archive | 2,626 | Event-driven risks, sentiment |
| FCIC Report | 1 | Comprehensive crisis analysis |

**Total:** 3,207 files, 442K chunks

## Knowledge Graph (FE-EKG)

Based on Liu et al. (2024) "Risk identification and management through knowledge Association"

**Three-layer structure:**
- **Entity Layer:** 22 financial institutions
- **Event Layer:** 4,000 events with 6 evolution algorithms
- **Risk Layer:** Risk types and transitions

**Evolution Methods:**
1. Temporal Correlation (TCDI formula)
2. Entity Overlap (Jaccard similarity)
3. Semantic Similarity
4. Topic Relevance
5. Event Type Causality
6. Emotional Consistency

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/entities` | All entities (22) |
| `GET /api/events` | All events (4,000) |
| `GET /api/evolution/links` | Evolution relationships |
| `GET /api/graph/data` | Graph visualization data |

## Future Phases

- **Phase 3:** Inter-bank contagion mechanism
- **Phase 4:** GraphRAG / KG-GNN hybrid
- **Phase 5:** Comparative evaluation (KG vs RAG vs Hybrid)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Developer guide
- [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) - Project overview
- [rag/EVALUATION_PLAN.md](rag/EVALUATION_PLAN.md) - RAG evaluation plan

## Frontend

[feekg-frontend](https://github.com/JunjieAraoXiong/feekg-frontend) - Next.js visualization app

## References

- Liu et al. (2024) - FE-EKG paper
- [AllegroGraph](https://allegrograph.com/)
- [Mesa ABM](https://mesa.readthedocs.io/)
- [ChromaDB](https://www.trychroma.com/)

## License

MIT - Research and educational purposes.
