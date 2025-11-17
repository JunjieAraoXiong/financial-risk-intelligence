# SLM Knowledge Graph Agent-Based Model - MVP Roadmap

**Document Version:** 1.0
**Last Updated:** 2025-11-16
**Project Goal:** Build an SLM-powered Knowledge Graph Agent-Based Model for financial crisis simulation
**Current Status:** 35-40% Complete (Foundation Layer Ready)

---

## Table of Contents

1. [Vision Overview](#vision-overview)
2. [Current Status Assessment](#current-status-assessment)
3. [Critical Gaps Analysis](#critical-gaps-analysis)
4. [Technology Stack Decisions](#technology-stack-decisions)
5. [8-Week Implementation Roadmap](#8-week-implementation-roadmap)
6. [Agent Architecture Design](#agent-architecture-design)
7. [SLM Integration Strategy](#slm-integration-strategy)
8. [RAG Enhancement Plan](#rag-enhancement-plan)
9. [Success Metrics](#success-metrics)
10. [Risk Mitigation](#risk-mitigation)

---

## Vision Overview

### End Goal: SLM Knowledge Graph Agent-Based Model

**What This Means:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Your Vision (MVP)                        │
│                                                             │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐         │
│  │   SLM    │ ───▶ │ Agents   │ ───▶ │ Knowledge│         │
│  │ (Local)  │      │ (Mesa)   │      │  Graph   │         │
│  │  1-3B    │      │ 100-1K   │      │ 429K     │         │
│  │ params   │      │ entities │      │ triples  │         │
│  └──────────┘      └──────────┘      └──────────┘         │
│       ↓                  ↓                  ↓              │
│    Decision          Behavior          Historical         │
│     Making           Execution           Context          │
└─────────────────────────────────────────────────────────────┘
```

**System Capabilities:**
1. **Simulate** financial crisis scenarios using agent-based modeling
2. **Reason** about agent actions using small language models
3. **Learn** from historical knowledge graph (2007-2009 crisis)
4. **Predict** systemic risk propagation and contagion dynamics
5. **Test** "what-if" counterfactual scenarios
6. **Visualize** real-time multi-agent interactions

---

## Current Status Assessment

### ✅ What's Production-Ready (Foundation: 100%)

#### Knowledge Graph Infrastructure
```
Status: ✅ COMPLETE
Quality: Production-Ready
Database: AllegroGraph 8.4.0 (Cloud)
```

**Metrics:**
- **5,105 events** (Capital IQ, 2007-2009 financial crisis)
- **22 entities** (deduplicated: AIG, JPMorgan, Bank of America, etc.)
- **31,173 evolution links** (6 algorithms, threshold=0.5)
- **429,019 RDF triples** (8.6% of 5M license limit)
- **87% classification confidence**
- **100% CSV traceability** (full data lineage)

**Evolution Methods Implemented:**
1. ✅ Temporal correlation (TCDI formula)
2. ✅ Entity overlap (Jaccard similarity)
3. ✅ Semantic similarity (embeddings)
4. ✅ Topic relevance (event categories)
5. ✅ Event type causality (domain rules)
6. ✅ Emotional consistency (sentiment)

**Backend Capabilities:**
- ✅ SPARQL queries (<100ms)
- ✅ Flask REST API (20+ endpoints)
- ✅ Parallel processing (8 cores, 4-5x speedup)
- ✅ Retry logic + checkpointing (95% reliability)
- ✅ Query optimization (40x faster than naive)

---

### ⚠️ What's Partially Complete

#### LLM Infrastructure (10%)
```
Status: ⚠️ PARTIAL
Have: NVIDIA NIM API (Llama-3.1-8B-Instruct)
Missing: Local SLM for agent decision-making
Gap: Using 8B LLM (not SLM), cloud API (not local)
```

**Current:**
- NVIDIA NIM API configured ✅
- Embeddings: `nvidia/llama-3.2-nv-embedqa-1b-v2` (2048 dims) ✅
- API Key: `nvapi-G0nH...` ✅
- Cost: $0.0002 per query

**Problem:**
- **NOT an SLM** (8B parameters is too large)
- **Cloud API** = expensive for ABM (1,000 agents × $0.0002 = $0.20 per step)
- **Latency** = 200-500ms (too slow for real-time ABM)

---

### ❌ What's Missing (Critical Gaps)

#### 1. Agent-Based Model (0%) ⚠️ **HIGHEST PRIORITY**
```
Status: ❌ NOT STARTED
Impact: 🔴 CRITICAL - This is 50% of your vision
Effort: 3-4 weeks (minimal), 8-12 weeks (full)
```

**Missing Components:**
- Mesa ABM framework (not installed)
- Agent classes (BankAgent, RegulatorAgent, etc.)
- Simulation model (FinancialCrisisModel)
- Network topology (from KG evolution links)
- Step functions (agent behavior rules)
- Shock propagation mechanics
- Scheduler (synchronous vs asynchronous)

**Impact on Vision:**
Without ABM, you have a **static knowledge graph**, not a **dynamic simulation**.

---

#### 2. Local SLM (0%) ⚠️ **CRITICAL**
```
Status: ❌ NOT STARTED
Impact: 🔴 CRITICAL - This is 25% of your vision
Effort: 1-2 weeks
```

**Missing Components:**
- Local SLM model download (Llama-3.2-1B or 3B)
- Inference engine (transformers + torch)
- Agent integration (decision-making pipeline)
- Prompt templates for financial reasoning
- Context window management (8K tokens)

**Why Local SLM Needed:**
- **Scalability:** Run 1,000+ agents simultaneously
- **Cost:** $0 (vs $0.0002 × 1K agents = $0.20/step)
- **Latency:** 50-200ms (vs 200-500ms API)
- **Control:** Fine-tune on financial domain
- **True SLM:** 1-3B parameters (vs 8B LLM)

---

#### 3. RAG Pipeline (10%)
```
Status: ⚠️ PARTIAL
Have: SPARQL queries, embeddings API
Missing: FAISS vector DB, hybrid retrieval
Effort: 1 week
```

**Current:**
- AllegroGraph SPARQL ✅
- NVIDIA embeddings API ✅
- Event descriptions ready ✅

**Missing:**
- FAISS vector database ❌
- Hybrid retrieval (SPARQL + vector) ❌
- Context expansion via evolution links ❌
- Integration with SLM for agent reasoning ❌

---

#### 4. Frontend Visualization (0%)
```
Status: ❌ NOT STARTED
Impact: 🟡 MEDIUM - Not critical for MVP, but needed for demo
Effort: 2-3 weeks
```

**Current:**
- Flask API works ✅
- Static PNG visualizations ✅

**Missing:**
- Next.js frontend ❌
- Cytoscape.js graph visualization ❌
- Real-time ABM simulation viewer ❌
- Timeline controls ❌
- Agent state monitoring dashboard ❌

---

## Critical Gaps Analysis

### Gap 1: Agent-Based Modeling (Mesa)

**Problem:** No ABM framework = no dynamic simulation

**Why Critical:**
- Your vision is "Agent-Based Model", but you have **zero agents**
- Knowledge graph is static (historical data only)
- No way to simulate "what-if" scenarios
- No contagion/propagation dynamics

**Solution:**
```bash
pip install mesa
```

**Minimal Implementation (3 weeks):**
```python
# abm/agents.py
from mesa import Agent

class BankAgent(Agent):
    """
    Bank agent with capital, liquidity, risk metrics
    Makes decisions via SLM based on KG context
    """
    def __init__(self, unique_id, model, entity_data):
        super().__init__(unique_id, model)
        self.name = entity_data['name']
        self.capital = entity_data['capital']
        self.liquidity = entity_data['liquidity']
        self.risk_score = 0.0
        self.failed = False

    def step(self):
        # 1. Query KG for historical context
        context = self.get_kg_context()

        # 2. SLM decides action
        action = self.decide_action(context)

        # 3. Execute action
        if action == 'defensive':
            self.reduce_exposure()
        elif action == 'aggressive':
            self.expand_lending()

        # 4. Check failure condition
        if self.liquidity < 0.1 * self.capital:
            self.fail()

    def fail(self):
        self.failed = True
        # Propagate shock to counterparties
        for neighbor in self.model.get_neighbors(self.unique_id):
            neighbor.absorb_shock(strength=0.2)

    def decide_action(self, context):
        # SLM-powered decision making
        prompt = f"""
        You are {self.name}, a financial institution.

        Current state:
        - Capital: ${self.capital}B
        - Liquidity: {self.liquidity}
        - Risk score: {self.risk_score}

        Historical context:
        {context}

        Should you take defensive or aggressive action?
        Answer: defensive/aggressive
        """
        return self.model.slm.generate(prompt)
```

---

### Gap 2: Local SLM Integration

**Problem:** Using 8B LLM API (not local SLM)

**Why Critical:**
- **Cost:** $0.20 per simulation step with 1,000 agents
- **Latency:** 200-500ms too slow for real-time ABM
- **Scalability:** Can't run parallel agents
- **Not SLM:** 8B parameters ≠ "Small" Language Model

**Solution: Llama-3.2-1B Local**

**Model Specs:**
```
Model: meta-llama/Llama-3.2-1B-Instruct
Parameters: 1 billion (TRUE SLM)
Memory: ~2GB RAM
Inference: 50-200ms per query (CPU/GPU)
Cost: $0 (local)
Quality: Good for financial reasoning
```

**Implementation:**
```python
# llm/local_slm.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LocalSLM:
    def __init__(self, model_name="meta-llama/Llama-3.2-1B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def generate(self, prompt, max_tokens=100):
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
```

**Why 1B vs 3B:**
- **1B:** Faster (50-100ms), smaller (2GB), good enough for simple decisions
- **3B:** Better reasoning (100-200ms), larger (6GB), better for complex scenarios

**Recommendation:** Start with **1B**, upgrade to **3B** if needed.

---

### Gap 3: RAG for Agent Intelligence

**Problem:** Agents can't retrieve relevant historical context from KG

**Why Critical:**
- Agents need to **learn from history** (2008 crisis patterns)
- Simple SPARQL queries miss semantic similarity
- Vector search needed for "find similar events"

**Solution: Hybrid RAG (SPARQL + FAISS)**

**Architecture:**
```
Agent Question
    ↓
Intent Classification (SLM)
    ↓
    ├─ Structured Query? → SPARQL (AllegroGraph)
    │   "What entities are connected to Lehman?"
    │
    └─ Semantic Query? → Vector Search (FAISS)
        "Find events similar to liquidity crisis"
    ↓
Context Expansion (Evolution Links)
    ↓
SLM Answer Generation
    ↓
Agent Decision
```

**Implementation (1 week):**
```python
# rag/retrieval.py
class HybridRetriever:
    def __init__(self):
        self.faiss_index = self.build_faiss_index()
        self.graph = AllegroGraphRDFLoader()
        self.slm = LocalSLM()

    def build_faiss_index(self):
        # Embed all 5,105 events
        from llm.nemotron_client import NemotronClient
        client = NemotronClient()

        events = self.load_events()
        embeddings = client.generate_embeddings(
            [e['description'] for e in events],
            model='nvidia/llama-3.2-nv-embedqa-1b-v2'
        )

        # Build FAISS index
        import faiss
        import numpy as np

        embedding_matrix = np.array(embeddings).astype('float32')
        index = faiss.IndexFlatIP(2048)  # 2048 dimensions
        index.add(embedding_matrix)

        faiss.write_index(index, 'data/event_embeddings.faiss')
        return index

    def retrieve(self, query, top_k=10):
        # 1. Classify intent
        intent = self.classify_intent(query)

        results = []

        # 2. Structured query → SPARQL
        if intent == 'structured':
            sparql_results = self.query_graph(query)
            results.extend(sparql_results)

        # 3. Semantic query → FAISS
        elif intent == 'semantic':
            query_emb = self.embed_query(query)
            distances, indices = self.faiss_index.search(
                np.array([query_emb]).astype('float32'),
                k=top_k
            )
            vector_results = [self.events[i] for i in indices[0]]
            results.extend(vector_results)

        # 4. Expand with evolution links
        results = self.expand_with_graph(results)

        return results
```

**Cost:** FREE (NVIDIA NIM free tier: 1,000 queries/day)

---

## Technology Stack Decisions

### Final Stack for SLM ABM

| Component | Technology | Status | Rationale |
|-----------|-----------|--------|-----------|
| **Knowledge Graph** | AllegroGraph 8.4.0 | ✅ Production | SPARQL, RDF reasoning, 5M triple license |
| **Agent Framework** | Mesa 2.0+ | ❌ TODO | Python ABM library, easy integration |
| **Local SLM** | Llama-3.2-1B-Instruct | ❌ TODO | True SLM, free, fast (50-200ms) |
| **Embeddings** | nvidia/llama-3.2-nv-embedqa-1b-v2 | ✅ Ready | Free API, 2048 dims, 53.1% FiQA |
| **Vector DB** | FAISS (local) | ❌ TODO | Free, fast (<50ms), 40MB storage |
| **Graph Analytics** | NetworkX 3.0+ | ✅ Ready | 500+ algorithms, GPU-ready |
| **API** | Flask 3.0+ | ✅ Production | 20+ endpoints, CORS enabled |
| **Frontend** | Next.js 14 + Cytoscape.js | ❌ TODO | React, graph viz, real-time |

---

## 8-Week Implementation Roadmap

### Week 1-2: Mesa ABM Foundation (CRITICAL)

**Goal:** Build basic agent-based model with 3 agent types

**Tasks:**
- [ ] Install Mesa: `pip install mesa`
- [ ] Download Llama-3.2-1B: 2GB download
- [ ] Create agent classes: `BankAgent`, `RegulatorAgent`, `MarketAgent`
- [ ] Implement `FinancialCrisisModel` class
- [ ] Define network topology from KG evolution links
- [ ] Implement basic step() functions
- [ ] Test with 10 agents (smoke test)

**Deliverable:** ABM that can simulate 10 banks over 100 time steps

**Code Structure:**
```
abm/
├── __init__.py
├── agents.py          # BankAgent, RegulatorAgent, MarketAgent
├── model.py           # FinancialCrisisModel
├── network.py         # Load network from KG
├── scheduler.py       # RandomActivation or SimultaneousActivation
└── metrics.py         # DataCollector for statistics
```

**Example Test:**
```python
# Run minimal simulation
from abm.model import FinancialCrisisModel

model = FinancialCrisisModel(
    n_banks=10,
    n_regulators=1,
    network_file='data/kg_network.json'
)

for step in range(100):
    model.step()

    # Check for systemic failure
    failed_banks = [a for a in model.schedule.agents if a.failed]
    print(f"Step {step}: {len(failed_banks)} banks failed")
```

---

### Week 3: Local SLM Integration

**Goal:** Agents use Llama-3.2-1B for decision-making

**Tasks:**
- [ ] Set up transformers + torch
- [ ] Download Llama-3.2-1B-Instruct (~2GB)
- [ ] Create `LocalSLM` wrapper class
- [ ] Design prompt templates for financial reasoning
- [ ] Integrate SLM into `BankAgent.decide_action()`
- [ ] Test inference speed (target: <200ms)
- [ ] Optimize: batch inference for multiple agents

**Deliverable:** Agents make SLM-powered decisions

**Prompt Template:**
```python
DECISION_PROMPT = """
You are {bank_name}, a financial institution in {year}.

Current State:
- Capital: ${capital:.1f}B
- Liquidity Ratio: {liquidity:.2%}
- Risk Score: {risk_score:.2f}
- Network Position: {centrality:.2f}

Recent Events:
{recent_events}

Similar Historical Events:
{similar_events}

Market Conditions:
- VIX: {vix}
- TED Spread: {ted_spread}
- Unemployment: {unemployment}%

Question: Should you take defensive action (reduce exposure) or maintain current strategy?

Consider:
1. Your liquidity position
2. Recent market events
3. Historical patterns
4. Counterparty risks

Answer with one word: DEFENSIVE or MAINTAIN
Reasoning (1 sentence):
"""
```

**Performance Target:**
- Inference: <200ms per agent
- Batch size: 10 agents simultaneously
- Total: 100 agents in 2 seconds

---

### Week 4: KG Integration & RAG

**Goal:** Agents query KG via RAG for historical context

**Tasks:**
- [ ] Build FAISS index from 5,105 events (~30 min)
- [ ] Implement `HybridRetriever` class
- [ ] Create agent memory (store past decisions)
- [ ] Integrate RAG into agent step() function
- [ ] Test retrieval quality (precision@10)
- [ ] Optimize: cache frequent queries

**Deliverable:** Agents retrieve relevant historical events

**Agent Query Flow:**
```python
class BankAgent(Agent):
    def step(self):
        # 1. Observe current state
        state = self.get_current_state()

        # 2. Query KG for similar historical scenarios
        query = f"Find events similar to: {state['description']}"
        context = self.model.rag.retrieve(query, top_k=5)

        # 3. SLM decides action based on context
        action = self.decide_action(state, context)

        # 4. Execute action
        self.execute_action(action)

        # 5. Update memory
        self.memory.append({
            'step': self.model.schedule.steps,
            'state': state,
            'context': context,
            'action': action
        })
```

---

### Week 5: Simulation Logic & Shock Propagation

**Goal:** Implement realistic financial contagion dynamics

**Tasks:**
- [ ] Define shock types (liquidity, solvency, market)
- [ ] Implement contagion rules (counterparty exposure)
- [ ] Add network effects (fire sales, bank runs)
- [ ] Create event triggers from KG timeline
- [ ] Test with 2008 crisis scenario
- [ ] Calibrate parameters (failure threshold, shock strength)

**Deliverable:** Realistic crisis simulation

**Contagion Mechanics:**
```python
class BankAgent(Agent):
    def absorb_shock(self, strength, source_agent):
        """
        Absorb shock from failed counterparty

        Args:
            strength: Shock magnitude (0-1)
            source_agent: Failed bank
        """
        # Direct exposure loss
        exposure = self.get_exposure(source_agent)
        capital_loss = exposure * strength

        self.capital -= capital_loss

        # Liquidity impact
        liquidity_shock = capital_loss * 0.5  # 50% liquidity drain
        self.liquidity -= liquidity_shock

        # Mark-to-market losses
        if self.model.crisis_intensity > 0.7:
            mtm_loss = self.assets * 0.1  # 10% asset depreciation
            self.capital -= mtm_loss

        # Check failure
        if self.capital < 0 or self.liquidity < self.min_liquidity:
            self.fail()

    def fail(self):
        self.failed = True
        self.model.failed_banks.append(self)

        # Propagate to all counterparties
        for neighbor in self.model.network.neighbors(self.unique_id):
            neighbor_agent = self.model.schedule._agents[neighbor]
            neighbor_agent.absorb_shock(
                strength=0.3,  # 30% exposure loss
                source_agent=self
            )
```

---

### Week 6: Scenario Testing & Calibration

**Goal:** Validate model against 2008 crisis timeline

**Tasks:**
- [ ] Load 2008 crisis timeline from KG
- [ ] Run simulation with historical event triggers
- [ ] Compare results to actual outcomes
- [ ] Calibrate parameters (network, thresholds, shocks)
- [ ] Test counterfactuals ("what if Fed acted earlier?")
- [ ] Document parameter sensitivity

**Deliverable:** Calibrated model matching 2008 crisis

**Validation Metrics:**
```python
# Compare simulation to reality
def validate_against_history():
    # Run simulation
    model = FinancialCrisisModel(
        start_date='2007-01-01',
        end_date='2009-12-31',
        historical_mode=True
    )

    for event in kg.get_events(start='2007-01-01', end='2009-12-31'):
        model.trigger_event(event)
        model.step()

    # Compare outcomes
    actual_failures = [
        'Lehman Brothers',
        'Bear Stearns',
        'Washington Mutual',
        'Wachovia'
    ]

    simulated_failures = [a.name for a in model.failed_banks]

    # Metrics
    precision = len(set(actual_failures) & set(simulated_failures)) / len(simulated_failures)
    recall = len(set(actual_failures) & set(simulated_failures)) / len(actual_failures)

    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
```

---

### Week 7-8: Frontend Visualization

**Goal:** Build web UI for real-time ABM visualization

**Tasks:**
- [ ] Set up Next.js 14 project
- [ ] Install Cytoscape.js for graph viz
- [ ] Create API endpoints for ABM state
- [ ] Build timeline controls
- [ ] Add agent state dashboard
- [ ] Implement real-time updates (WebSocket)
- [ ] Deploy to localhost:3000

**Deliverable:** Interactive ABM dashboard

**Frontend Components:**
```
feekg-frontend/
├── app/
│   ├── page.tsx              # Main dashboard
│   ├── simulation/
│   │   └── page.tsx          # ABM viewer
│   └── api/
│       └── simulation/
│           ├── start/route.ts
│           ├── step/route.ts
│           └── state/route.ts
├── components/
│   ├── GraphVisualization.tsx   # Cytoscape.js
│   ├── TimelineControl.tsx      # Play/pause/step
│   ├── AgentDashboard.tsx       # Agent states
│   └── MetricsPanel.tsx         # Statistics
└── lib/
    └── api.ts                   # API client
```

**Graph Visualization:**
```tsx
// components/GraphVisualization.tsx
import Cytoscape from 'cytoscape';

export default function GraphVisualization({ agents, network }) {
  useEffect(() => {
    const cy = Cytoscape({
      container: document.getElementById('cy'),
      elements: {
        nodes: agents.map(a => ({
          data: {
            id: a.id,
            label: a.name,
            color: a.failed ? 'red' : 'green',
            size: a.capital
          }
        })),
        edges: network.map(e => ({
          data: {
            source: e.source,
            target: e.target,
            weight: e.exposure
          }
        }))
      },
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)'
          }
        }
      ]
    });
  }, [agents, network]);

  return <div id="cy" style={{ width: '100%', height: '600px' }} />;
}
```

---

## Agent Architecture Design

### Agent Types

#### 1. BankAgent
```python
class BankAgent(Agent):
    """
    Commercial/investment bank agent

    Attributes:
        - capital: Tier 1 capital ($B)
        - liquidity: Liquid assets ($B)
        - assets: Total assets ($B)
        - liabilities: Total liabilities ($B)
        - counterparties: Set[BankAgent]
        - risk_score: Systemic risk metric (0-1)
        - failed: Boolean failure state

    Behaviors:
        - Assess risk (query KG + SLM)
        - Adjust exposure (defensive/aggressive)
        - Propagate shocks (contagion)
        - Seek liquidity (interbank lending)
    """
```

#### 2. RegulatorAgent
```python
class RegulatorAgent(Agent):
    """
    Federal Reserve / Treasury agent

    Attributes:
        - intervention_threshold: Crisis trigger level
        - available_funds: Bailout capacity ($B)
        - interest_rate: Policy rate (%)

    Behaviors:
        - Monitor systemic risk
        - Provide emergency liquidity
        - Adjust interest rates
        - Coordinate bailouts
    """
```

#### 3. MarketAgent
```python
class MarketAgent(Agent):
    """
    Aggregate market sentiment agent

    Attributes:
        - vix: Volatility index
        - ted_spread: Credit stress indicator
        - sentiment: Market confidence (-1 to 1)

    Behaviors:
        - Update market conditions
        - Trigger panic (bank runs)
        - Amplify shocks (fire sales)
    """
```

### Agent Decision Framework

**SLM Prompt Structure:**
```
ROLE: You are {agent_name}, a {agent_type}.

CURRENT STATE:
{agent_state}

HISTORICAL CONTEXT (from KG):
{retrieved_events}

NETWORK POSITION:
- Direct counterparties: {counterparties}
- Centrality: {centrality}
- Exposure: ${total_exposure}B

MARKET CONDITIONS:
- VIX: {vix}
- TED Spread: {ted_spread}
- Failed banks: {n_failed}

QUESTION: What action should you take?
OPTIONS:
1. DEFENSIVE (reduce lending, increase reserves)
2. MAINTAIN (continue current strategy)
3. AGGRESSIVE (expand lending, take risks)
4. SEEK_LIQUIDITY (request Fed assistance)

CONSTRAINTS:
- Capital ratio must stay above {min_capital_ratio}
- Liquidity coverage ratio must be ≥ 100%

ANSWER (one word): [option]
REASONING (1 sentence): [explain]
```

---

## SLM Integration Strategy

### Model Selection

| Model | Parameters | Memory | Speed | Quality | Cost | Recommendation |
|-------|-----------|--------|-------|---------|------|----------------|
| **Llama-3.2-1B** | 1B | 2GB | 50-100ms | Good | $0 | ✅ **START HERE** |
| Llama-3.2-3B | 3B | 6GB | 100-200ms | Better | $0 | Upgrade later |
| Llama-3.1-8B (API) | 8B | N/A | 200-500ms | Best | $0.0002 | Too slow/expensive |

**Decision:** Use **Llama-3.2-1B** for MVP, fine-tune later.

### Fine-Tuning Strategy (Optional, Week 9+)

**Dataset:**
- 5,105 event descriptions from KG
- Agent decision labels (defensive/maintain/aggressive)
- Historical outcomes (bank failures, crisis severity)

**Method:**
- LoRA (Low-Rank Adaptation) - efficient fine-tuning
- Training data: 4,000 examples
- Validation: 1,000 examples
- Epochs: 3-5
- Time: 2-4 hours on GPU

**Expected Improvement:**
- Base model: 60-70% decision accuracy
- Fine-tuned: 75-85% accuracy
- Domain-specific reasoning improves

---

## RAG Enhancement Plan

### Phase 1: Vector Database (Week 4)

**Build FAISS Index:**
```python
# rag/build_index.py
from llm.nemotron_client import NemotronClient
import faiss
import numpy as np
import json

# Load 5,105 events
with open('data/capital_iq_processed/lehman_v4_deduped.json') as f:
    data = json.load(f)
    events = data['events']

# Generate embeddings
client = NemotronClient()
print(f"Embedding {len(events)} events...")

embeddings = client.generate_embeddings(
    [e['description'] for e in events],
    model='nvidia/llama-3.2-nv-embedqa-1b-v2'
)

# Build FAISS index
embedding_matrix = np.array(embeddings).astype('float32')
index = faiss.IndexFlatIP(2048)  # Inner product similarity
index.add(embedding_matrix)

# Save
faiss.write_index(index, 'data/event_embeddings.faiss')
with open('data/event_ids.json', 'w') as f:
    json.dump([e['eventId'] for e in events], f)

print(f"✅ Indexed {len(events)} events")
print(f"   Storage: ~40MB")
```

**Cost:** FREE (within NVIDIA NIM free tier: 1,000 queries/day)
**Time:** ~20 seconds
**Quality:** 53.1% FiQA score (financial Q&A benchmark)

---

### Phase 2: Hybrid Retrieval (Week 4)

**Architecture:**
```
Agent Query
    ↓
┌───────────────────────────┐
│  Intent Classification    │  (SLM: 50ms)
└───────────────────────────┘
    ↓           ↓
  SPARQL     Vector
  (100ms)    (10ms)
    ↓           ↓
┌───────────────────────────┐
│   Context Expansion       │  (Evolution links: 50ms)
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│   Rank & Filter           │  (Top-K: 10ms)
└───────────────────────────┘
    ↓
Return top 10 events
```

**Total Latency:** ~220ms (acceptable for ABM)

---

## Success Metrics

### Technical Metrics

**Knowledge Graph:**
- ✅ 5,105 events loaded
- ✅ 31,173 evolution links
- ✅ <100ms SPARQL queries

**ABM:**
- [ ] 100+ agents running simultaneously
- [ ] 1,000+ time steps per simulation
- [ ] <2 seconds per step (100 agents)
- [ ] 90%+ uptime

**SLM:**
- [ ] <200ms inference time
- [ ] 70%+ decision accuracy
- [ ] Batch processing: 10 agents/second

**RAG:**
- [ ] <50ms vector search
- [ ] 60%+ retrieval precision@10
- [ ] 80%+ context relevance

---

### Validation Metrics

**Historical Accuracy:**
- [ ] Predict Lehman failure: ✅ or ❌
- [ ] Predict Bear Stearns failure: ✅ or ❌
- [ ] Timing error: <30 days
- [ ] Severity correlation: >0.7

**Counterfactual Testing:**
- [ ] "Fed intervenes 1 week earlier" → fewer failures
- [ ] "Lehman has 20% more capital" → no systemic collapse
- [ ] "No Bear Stearns bailout" → faster contagion

---

## Risk Mitigation

### Risk 1: SLM Quality Too Low

**Risk:** 1B model too small, poor decisions

**Mitigation:**
1. Start with 1B, upgrade to 3B if needed
2. Fine-tune on financial domain
3. Fallback: Use rule-based logic + SLM validation
4. Last resort: Use NVIDIA API for critical decisions

---

### Risk 2: ABM Too Complex

**Risk:** 8-week timeline too ambitious

**Mitigation:**
1. Start with minimal ABM (3 agent types)
2. Use simple rules before SLM integration
3. Defer advanced features (fire sales, bank runs)
4. Focus on core: shock propagation + contagion

---

### Risk 3: Computational Performance

**Risk:** 1,000 agents × SLM = too slow

**Mitigation:**
1. Batch inference: Process 10 agents simultaneously
2. GPU acceleration: 5-10x faster
3. Hybrid approach: SLM for critical decisions only
4. Rule-based for routine decisions

---

## Next Steps

### Immediate (This Week)

**Day 1-2:**
```bash
# Install Mesa
pip install mesa

# Download Llama-3.2-1B
pip install transformers torch
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('meta-llama/Llama-3.2-1B-Instruct')"
```

**Day 3-5:**
- Create `abm/agents.py` with `BankAgent` class
- Create `abm/model.py` with `FinancialCrisisModel`
- Test with 10 agents, 100 steps

**Day 6-7:**
- Integrate KG network topology
- Add shock propagation
- Validate basic contagion

---

### Month 1: Core ABM + SLM (Weeks 1-4)

**Week 1-2:** Mesa ABM foundation
**Week 3:** Local SLM integration
**Week 4:** RAG for agent intelligence

**Deliverable:** 100-agent simulation with SLM decision-making

---

### Month 2: Calibration + Frontend (Weeks 5-8)

**Week 5:** Shock propagation mechanics
**Week 6:** 2008 crisis validation
**Week 7-8:** Next.js frontend

**Deliverable:** Full MVP with interactive visualization

---

## Conclusion

### Current Reality
You have a **world-class knowledge graph foundation** (100% complete), but you're **missing the core differentiator** of your vision:

- ❌ **Agent-Based Model** (0%)
- ❌ **Small Language Model** (0%)

### Path Forward
- **8 weeks** to complete MVP
- **3-4 weeks** for minimal viable ABM
- **Critical:** Start Mesa ABM + Local SLM **immediately**

### Bottom Line
You have the **data** (5,105 events, 429K triples). Now you need the **simulation engine** (Mesa) and **intelligence layer** (SLM).

**Recommended Action:** Start building ABM **this week**.

---

**Document Owner:** Project Team
**Next Review:** 2025-12-01
**Priority:** 🔴 CRITICAL PATH - ABM is blocking MVP completion

---

*End of Roadmap*
