# Financial Crisis AI System - Architecture

**Last Updated:** 2025-11-16
**Version:** 2.0 (Post-restructuring)

---

## Executive Summary

This project has evolved from a single-paper implementation (FE-EKG) into a **multi-component AI system** for financial crisis analysis. It combines Knowledge Graphs, Agent-Based Modeling, and Small Language Models to predict and simulate financial contagion.

**What we're building:**
```
Historical KG → RAG Retrieval → SLM Reasoning → ABM Agents → Crisis Simulation
    ↓              ↓                ↓               ↓               ↓
5,105 events   Semantic search   AI decisions    Mesa 3.x      Contagion dynamics
```

---

## System Components

### 🏗️ Component 1: FE-EKG Core (Knowledge Graph)

**Status:** ✅ **COMPLETE** (Stages 1-6)
**Based on:** Liu et al. (2024) "Risk identification through knowledge association"
**Location:** Root directories + `docs/`

#### What It Does
- 3-layer knowledge graph (Risk → Event → Entity)
- 6 evolution algorithms (temporal, semantic, causal, etc.)
- AllegroGraph backend (5,105 events, 31,173 evolution links, 429K triples)
- SPARQL query interface
- Visualization tools (matplotlib, NetworkX)

#### Key Files
```
feekg/
├── data/
│   ├── evergrande_crisis.json        # Original case study
│   ├── capital_iq_processed/         # Lehman case study
│   └── lehman_events.csv             # 5,105 financial events
├── ingestion/
│   ├── load_evergrande.py
│   ├── load_lehman.py
│   └── process_capital_iq.py
├── evolution/
│   ├── methods.py                     # 6 evolution algorithms
│   └── run_evolution.py
├── query/
│   ├── risk_queries.cypher
│   └── risk_analyzer.py               # 80+ query templates
├── viz/
│   └── graph_viz.py
└── config/
    ├── graph_backend.py               # AllegroGraph connector
    └── rdf_backend.py
```

#### Publications
- **Primary:** Liu et al. (2024) - Original FE-EKG paper
- **Our extension:** Lehman Brothers case study (5,105 events vs original 20)

---

### 🤖 Component 2: Agent-Based Model (ABM)

**Status:** ✅ **FOUNDATION COMPLETE** (Week 1-2)
**Framework:** Mesa 3.3.1
**Location:** `abm/`

#### What It Does
- Simulates financial crisis contagion through agent interactions
- 3 agent types: BankAgent, RegulatorAgent, MarketAgent
- Network-based shock propagation
- Decision-making framework (rule-based, ready for SLM)
- Data collection and metrics export

#### Key Files
```
abm/
├── __init__.py
├── agents.py                          # 3 agent classes (500 lines)
│   ├── BankAgent                      # Banks with leverage, liquidity, risk
│   ├── RegulatorAgent                 # Fed with bailout fund, interest rate
│   └── MarketAgent                    # VIX, TED spread, sentiment
├── model.py                           # FinancialCrisisModel (300 lines)
├── network.py                         # Load topology from KG
├── metrics.py                         # Data collection & analysis
└── test_simulation.py                 # 10-bank test simulation

results/
├── abm_simulation_results.json
├── abm_network.json
└── abm_crisis_timeline.png            # 4-panel visualization
```

#### How Agents Work Now (Rule-Based)
```python
# BankAgent.decide_action()
if liquidity_ratio < 0.15:
    return 'SEEK_LIQUIDITY'  # Request Fed help
elif risk_score > 0.7:
    return 'DEFENSIVE'       # Reduce exposure
elif risk_score > 0.4:
    return 'MAINTAIN'        # Status quo
else:
    return 'AGGRESSIVE'      # Expand lending
```

#### Next: Week 3 - SLM Integration
Replace rules with AI reasoning:
```python
# Future: BankAgent.decide_action() with SLM
context = self.query_kg_for_historical_analogies()
decision = slm.reason(current_state, historical_context)
return decision  # AI-driven, knowledge-grounded
```

#### Publications Potential
- **Paper 2:** "Knowledge-Grounded Agent-Based Modeling of Financial Contagion"
- **Novel contribution:** First ABM using KG + SLM for agent decisions
- **Timeline:** Q1-Q2 2026 (after SLM integration)

---

### 🧠 Component 3: Small Language Model (SLM)

**Status:** ⏳ **PLANNED** (Week 3-4)
**Model:** Llama-3.2-1B-Instruct
**Location:** `slm/` (to be created)

#### What It Will Do
- Replace rule-based agent decisions with AI reasoning
- Query knowledge graph for historical context (via RAG)
- Generate natural language explanations for decisions
- Run locally (no API costs, <200ms inference)

#### Planned Architecture
```
slm/
├── llama_client.py                    # Local Llama-3.2-1B wrapper
├── prompts/
│   ├── bank_decision.txt              # Decision-making prompt
│   ├── regulator_intervention.txt
│   └── risk_assessment.txt
├── evaluation/
│   ├── compare_slm_vs_rules.py        # Ablation study
│   └── metrics.py
└── fine_tuning/                       # Future: Fine-tune on finance
    └── prepare_dataset.py
```

#### Example Usage (Week 3)
```python
from slm.llama_client import LocalSLM

slm = LocalSLM(model_path='models/llama-3.2-1b-instruct')

# Agent queries KG
historical_context = rag.retrieve(
    "Similar situations: high leverage, failing banks, VIX=60"
)

# SLM reasons
prompt = f"""
You are JPMorgan Chase with:
- Capital: $150B
- Liquidity ratio: 15%
- Market VIX: 60 (panic)
- Failed banks: Lehman, Bear Stearns

Historical precedent from 2008:
{historical_context}

What action should you take?
1. DEFENSIVE - Reduce exposure
2. MAINTAIN - Status quo
3. AGGRESSIVE - Expand lending
4. SEEK_LIQUIDITY - Request Fed help

Decision:"""

decision = slm.generate(prompt, max_tokens=50)
```

#### Publications Potential
- **Paper 3:** "Small Language Models for Financial Crisis Decisions"
- **Novel contribution:** 1B param SLM vs 8B+ LLM, knowledge grounding
- **Timeline:** Q2 2026

---

### 🔍 Component 4: RAG (Retrieval-Augmented Generation)

**Status:** ⏳ **PLANNED** (Week 4)
**Vector DB:** FAISS (local)
**Location:** `rag/` (to be created)

#### What It Will Do
- Store event embeddings in FAISS index
- Hybrid retrieval: Semantic (embeddings) + Temporal (dates) + Graph (SPARQL)
- Provide context to SLM for decision-making
- Incremental updates when new events added

#### Planned Architecture
```
rag/
├── faiss_manager.py                   # FAISS index manager
├── embeddings/
│   ├── generate_embeddings.py         # Embed events (NVIDIA NIM)
│   └── event_embeddings.faiss         # ~40MB for 5,105 events
├── retrievers/
│   ├── hybrid_retriever.py            # Semantic + Temporal + Graph
│   ├── semantic_search.py             # FAISS similarity
│   └── temporal_filter.py             # Date range filtering
└── cache/
    └── query_cache.py                 # 3-tier caching for ABM
```

#### How It Works
```
Agent Query: "What happened after Lehman bankruptcy?"
    ↓
1. FAISS Semantic Search
   → Find events similar to "Lehman bankruptcy"
   → Top 100 candidates (by embedding similarity)
    ↓
2. Temporal Filter
   → Only events AFTER 2008-09-15
   → Reduces to 50 candidates
    ↓
3. Graph Traversal
   → Follow evolution links from Lehman event
   → Get causal chain: Lehman → AIG → Market crash
    ↓
4. Rank & Return
   → Top 5 most relevant events
   → Pass to SLM as context
```

#### Performance Goals
- Query latency: <50ms (with caching)
- Incremental updates: <5 seconds for 100 new events
- Cache hit rate: 80%+

---

### 🔄 Component 5: Dynamic KG (Future Work)

**Status:** 📝 **VISION DOCUMENT CREATED** (Week 8+)
**Document:** `DYNAMIC_KG_VISION.md`
**Location:** `dynamic_kg/` (to be created)

#### What It Will Do
- Automated data ingestion (JSON, CSV, web scraping, PDFs)
- NLP entity/event extraction (spaCy + optional LLM)
- Smart deduplication ("JP Morgan" = "JPMorgan Chase")
- Incremental evolution link computation (26x speedup)
- FAISS index updates (non-blocking)
- Scheduled batch processing (daily at 2am)

#### Not Implementing Yet
This is **future enhancement** - focus on SLM integration first.

#### Publications Potential
- **Paper 4:** "Self-Updating Knowledge Graphs for Real-Time Risk"
- **Timeline:** 2026+ (if time permits)

---

## Data Flow Architecture

### Current System (Stages 1-6 Complete)
```
┌──────────────────────────────────────────────────────┐
│  DATA SOURCES                                        │
│  • Evergrande case study (20 events)                 │
│  • Lehman case study (5,105 events)                  │
│  • Capital IQ (processed JSON)                       │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  KNOWLEDGE GRAPH (AllegroGraph)                      │
│  • 5,105 events                                      │
│  • 22 entities                                       │
│  • 31,173 evolution links                            │
│  • 429,019 triples                                   │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  QUERY LAYER                                         │
│  • SPARQL queries (80+ templates)                    │
│  • RiskAnalyzer class                                │
│  • Visualization tools                               │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  AGENT-BASED MODEL (Mesa)                            │
│  • 10-bank simulation                                │
│  • Rule-based decisions                              │
│  • Network contagion                                 │
│  • Data export (JSON, PNG)                           │
└──────────────────────────────────────────────────────┘
```

### Future System (Week 3-8)
```
┌──────────────────────────────────────────────────────┐
│  DATA SOURCES                                        │
│  • Existing KG data                                  │
│  • New uploads (JSON, CSV)                           │
│  • SEC filings (web scraping) - optional             │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  KNOWLEDGE GRAPH (AllegroGraph)                      │
│  • Existing 429K triples                             │
│  • + New data (incremental updates)                  │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  RAG SYSTEM                                          │
│  • FAISS embeddings                                  │
│  • Hybrid retrieval                                  │
│  • 3-tier caching                                    │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  SMALL LANGUAGE MODEL (Llama-3.2-1B)                 │
│  • Query KG via RAG                                  │
│  • Reason about historical context                   │
│  • Generate decisions                                │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  AGENT-BASED MODEL (Mesa)                            │
│  • BankAgents use SLM decisions                      │
│  • Emergent behavior from AI reasoning               │
│  • Validate against 2008 crisis                      │
└──────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Infrastructure
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Graph DB** | AllegroGraph | 8.0+ | RDF triple store |
| **Vector DB** | FAISS | Latest | Event embeddings |
| **Python** | 3.10+ | Required | All components |
| **Virtual Env** | venv | Built-in | Dependency isolation |

### Knowledge Graph (Component 1)
| Tool | Purpose |
|------|---------|
| RDFLib | RDF manipulation |
| NetworkX | Graph algorithms |
| pandas | Data processing |
| matplotlib | Visualization |

### Agent-Based Model (Component 2)
| Tool | Purpose |
|------|---------|
| Mesa | 3.3.1 - ABM framework |
| NumPy | Numerical computations |
| NetworkX | Network topology |

### SLM + RAG (Components 3-4)
| Tool | Purpose |
|------|---------|
| transformers | Llama model loading |
| FAISS | Vector similarity search |
| sentence-transformers | Embeddings (alternative) |
| NVIDIA NIM | Embeddings API (current) |

### Future (Component 5)
| Tool | Purpose |
|------|---------|
| spaCy | NLP entity extraction |
| BeautifulSoup | Web scraping |
| APScheduler | Batch processing |
| Celery | Async tasks (optional) |

---

## File Organization

### Current Structure (As-Is)
```
feekg/
├── abm/                               # NEW: Week 1-2
├── config/
├── data/
├── docs/
├── evolution/
├── ingestion/
├── ontology/
├── query/
├── results/
├── scripts/
├── viz/
├── requirements.txt
└── README.md
```

### Improved Structure (To-Be)
```
feekg/  (or rename to: financial-crisis-ai/)
│
├── docs/                              # All documentation
│   ├── papers/                        # Academic papers
│   │   ├── FEEKG_ORIGINAL.md
│   │   ├── ABM_PAPER_OUTLINE.md
│   │   └── SLM_PAPER_OUTLINE.md
│   ├── vision/                        # Vision documents
│   │   ├── DYNAMIC_KG_VISION.md
│   │   └── SLM_ABM_ROADMAP.md
│   ├── api/                           # API docs
│   └── tutorials/                     # How-to guides
│
├── feekg_core/                        # Component 1 (rename from root)
│   ├── ingestion/
│   ├── evolution/
│   ├── query/
│   ├── viz/
│   ├── README.md                      # "FE-EKG Core"
│   └── requirements.txt               # Core dependencies
│
├── abm/                               # Component 2 (already created)
│   ├── agents.py
│   ├── model.py
│   ├── network.py
│   ├── metrics.py
│   ├── tests/
│   ├── README.md                      # "ABM Component"
│   └── requirements.txt               # Mesa, NumPy
│
├── slm/                               # Component 3 (Week 3)
│   ├── llama_client.py
│   ├── prompts/
│   ├── evaluation/
│   ├── README.md                      # "SLM Integration"
│   └── requirements.txt               # transformers, torch
│
├── rag/                               # Component 4 (Week 4)
│   ├── faiss_manager.py
│   ├── embeddings/
│   ├── retrievers/
│   ├── README.md                      # "RAG System"
│   └── requirements.txt               # FAISS, sentence-transformers
│
├── shared/                            # Shared utilities
│   ├── config/                        # Moved from root
│   │   ├── graph_backend.py
│   │   └── rdf_backend.py
│   ├── utils/
│   └── constants.py
│
├── data/                              # All data
│   ├── raw/                           # Original data
│   ├── processed/                     # Processed data
│   ├── embeddings/                    # FAISS indices
│   └── uploads/                       # Dynamic KG uploads
│
├── results/                           # All outputs
│   ├── feekg/                         # KG visualizations
│   ├── abm/                           # Simulation results
│   └── experiments/                   # Research experiments
│
├── scripts/                           # Utility scripts
│   ├── verify_stage*.py
│   ├── demo_*.py
│   └── setup/
│
├── tests/                             # All tests
│   ├── test_feekg_core/
│   ├── test_abm/
│   └── test_integration/
│
├── ARCHITECTURE.md                    # This file
├── README.md                          # Main project README
├── CONTRIBUTING.md
├── LICENSE
└── requirements/
    ├── base.txt                       # Common dependencies
    ├── feekg.txt                      # FE-EKG core
    ├── abm.txt                        # ABM
    ├── slm.txt                        # SLM + RAG
    └── dev.txt                        # Development tools
```

---

## Development Workflow

### Current Status
```
✅ Stage 1-6: FE-EKG Core (COMPLETE)
✅ Week 1-2: ABM Foundation (COMPLETE)
⏳ Week 3: SLM Integration (NEXT)
⏳ Week 4: RAG System (NEXT)
📝 Week 5+: Experiments & Papers
```

### Active Branches (Recommended)
```
main                    # Stable, production-ready
├── dev                 # Active development
├── feature/slm         # Week 3 work
├── feature/rag         # Week 4 work
└── research/*          # Experimental branches
```

### Typical Development Cycle
```
1. Create feature branch
2. Implement component
3. Write tests
4. Update documentation
5. Merge to dev
6. Run integration tests
7. Merge to main
8. Tag release (v1.1, v1.2, etc.)
```

---

## Testing Strategy

### Unit Tests
```
tests/
├── test_feekg_core/
│   ├── test_evolution_methods.py
│   ├── test_risk_analyzer.py
│   └── test_graph_backend.py
├── test_abm/
│   ├── test_agents.py
│   ├── test_model.py
│   └── test_network.py
└── test_slm/
    ├── test_llama_client.py
    └── test_prompts.py
```

### Integration Tests
```
tests/integration/
├── test_kg_to_abm.py              # KG → ABM data flow
├── test_rag_to_slm.py             # RAG → SLM reasoning
└── test_end_to_end.py             # Full pipeline
```

### Run Tests
```bash
# All tests
pytest tests/

# Specific component
pytest tests/test_abm/

# With coverage
pytest --cov=abm tests/test_abm/
```

---

## Deployment Considerations

### Local Development (Current)
- Python venv
- Local AllegroGraph instance
- NVIDIA NIM API (free tier)
- Local FAISS index

### Future Production (If Needed)
```
Docker Compose:
├── allegrograph (graph DB)
├── app (Python API)
├── nginx (reverse proxy)
└── redis (caching)

Kubernetes (Scale):
├── Pods: API servers (auto-scale)
├── StatefulSet: AllegroGraph
├── Persistent Volumes: Data, embeddings
└── Ingress: Load balancer
```

---

## Academic Publication Roadmap

### Timeline
```
Q4 2025:
- ✅ FE-EKG core complete
- ✅ ABM foundation complete
- ⏳ SLM integration

Q1 2026:
- Complete SLM + RAG
- Run 2008 crisis replication experiments
- Draft Paper 2: "Knowledge-Grounded ABM"

Q2 2026:
- Ablation studies (SLM vs rules)
- Submit Paper 2 to conference
- Start Paper 3: "SLM for Finance"

Q3 2026:
- Revisions on Paper 2
- Complete SLM evaluation
- Draft Paper 3

Q4 2026:
- Submit Paper 3
- (Optional) Start dynamic KG work
```

### Target Venues
- **Conferences:** AAAI, IJCAI, NeurIPS (AI track)
- **Finance:** Journal of Financial Economics, Review of Financial Studies
- **Interdisciplinary:** Nature Computational Science, PNAS

---

## Key Decisions & Rationale

### Why Mesa (not custom ABM)?
- Well-maintained (active development)
- Python native (easy integration)
- Good documentation
- Used in academic research (citable)

### Why FAISS (not Pinecone/Weaviate)?
- **Local:** No API costs, no data privacy concerns
- **Fast:** <10ms search even with 100K vectors
- **Simple:** No infrastructure overhead
- **Scalable:** Can move to cloud later if needed

### Why Llama-3.2-1B (not GPT-4)?
- **Local inference:** No API costs
- **Fast:** <200ms per decision
- **Research:** Can study SLM vs LLM trade-offs
- **Control:** Full model access for fine-tuning

### Why AllegroGraph (not Neo4j)?
- **Original paper** used RDF/OWL ontology
- **SPARQL:** Powerful for temporal queries
- **Continuity:** Already implemented and working

---

## Future Enhancements (Not Committed)

### Possible Additions
1. **Frontend Dashboard** (React + D3.js)
2. **Real-time Streaming** (Kafka pipeline)
3. **Fine-tuned SLM** (on financial domain)
4. **Multi-agent Learning** (RL for optimal policies)
5. **Causal Discovery** (learn causal graph from data)

### Not Planning
- Cloud deployment (unless collaborators need it)
- Large-scale production system
- Commercial application

---

## References

### Primary Papers
1. Liu et al. (2024) - FE-EKG original paper
2. Mesa Documentation - https://mesa.readthedocs.io/
3. Llama 3.2 Technical Report - Meta AI

### Related Work
- Haldane & May (2011) - Systemic risk in banking networks
- Cont & Schaanning (2017) - Fire sales and contagion
- Lewis et al. (2024) - Retrieval-Augmented Generation

---

## Contact & Collaboration

**Maintainer:** [Your Name]
**Institution:** [Your University]
**Email:** [Your Email]

**Open to:**
- Academic collaborations
- Code contributions (see CONTRIBUTING.md)
- Research discussions

**Not open to:**
- Commercial licensing (at this time)
- Production support

---

## Changelog

### Version 2.0 (2025-11-16)
- ✅ Restructured project into components
- ✅ Created ARCHITECTURE.md
- ✅ Completed ABM foundation (Mesa 3.3.1)
- 📝 Planned SLM + RAG integration

### Version 1.0 (2025-11-10)
- ✅ FE-EKG core complete (Stages 1-6)
- ✅ 5,105 events loaded
- ✅ 31,173 evolution links computed
- ✅ REST API operational

---

**This is a living document. Update as the project evolves.**
