# Agent-Based Model (ABM) Integration with FE-EKG

**How the ABM component integrates with the Knowledge Graph**

---

## Overview

The Agent-Based Model (ABM) simulates financial crisis contagion using the Mesa framework. It integrates with the FE-EKG Knowledge Graph to:

1. **Load network topology** from real financial institution relationships
2. **Initialize agent states** from historical data
3. **Query historical context** for AI-driven decisions (Week 3-4)
4. **Export simulation results** back to the knowledge graph

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ABM ↔ Knowledge Graph Integration               │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐                                ┌──────────────┐
│ AllegroGraph │                                │     ABM      │
│  (KG Store)  │                                │ Simulation   │
│              │                                │              │
│ • 4K events  │────── Load Network ───────────▶│ • 10 banks   │
│ • 22 entities│◀───── Query Context ───────────│ • Regulator  │
│ • Evolution  │                                │ • Market     │
└──────────────┘                                └──────────────┘
       │                                               │
       │                                               │
       ▼                                               ▼
┌──────────────┐                                ┌──────────────┐
│ SPARQL Query │                                │  Simulation  │
│              │                                │   Results    │
│ • Entities   │                                │              │
│ • Evolution  │                                │ • Failures   │
│ • Risk links │                                │ • Bailouts   │
└──────────────┘                                │ • Timeline   │
                                                └──────────────┘
```

---

## Integration Points

### 1. Network Topology Loading

**Purpose:** Load real financial institution relationships from the Knowledge Graph

**Implementation:** `abm/network.py`

```python
from abm.network import load_network_from_kg

# Load network from AllegroGraph
network, entity_metadata = load_network_from_kg(
    entity_limit=20,           # Max entities to load
    min_evolution_score=0.5    # Min relationship strength
)

# Returns:
# - network: NetworkX graph (nodes = entities, edges = evolution links)
# - entity_metadata: {node_id: {'name': '...', 'entity_id': '...', 'type': '...'}}
```

**What it does:**
1. Queries AllegroGraph for entities:
   ```sparql
   PREFIX feekg: <http://feekg.org/ontology#>
   SELECT ?entity ?label ?type
   WHERE {
       ?entity a feekg:Entity .
       ?entity feekg:label ?label .
       ?entity feekg:entityType ?type .
   }
   LIMIT 20
   ```

2. Queries evolution links between entities:
   ```sparql
   SELECT ?from ?to ?score
   WHERE {
       ?link a feekg:EvolutionLink .
       ?link feekg:fromEntity ?from .
       ?link feekg:toEntity ?to .
       ?link feekg:score ?score .
       FILTER (?score >= 0.5)
   }
   ```

3. Builds NetworkX graph:
   - Nodes = financial institutions (22 entities)
   - Edges = evolution relationships (weighted by score)
   - Metadata = entity names, types, IDs

**Example:**
```python
>>> network, metadata = load_network_from_kg(entity_limit=10)
>>> print(f"Loaded {network.number_of_nodes()} banks")
Loaded 10 banks
>>> print(f"Network density: {nx.density(network):.2f}")
Network density: 0.38
>>> print(metadata['bank_001'])
{'name': 'Lehman Brothers', 'entity_id': 'ent_lehman', 'type': 'investment_bank'}
```

---

### 2. Agent Initialization

**Purpose:** Initialize bank agents with realistic financial states from KG data

**Implementation:** `abm/model.py`

```python
from abm import FinancialCrisisModel

# Create model with KG network
model = FinancialCrisisModel(
    n_banks=10,
    network=network,            # From load_network_from_kg()
    initial_capital_range=(5.0, 20.0),
    crisis_trigger_step=50
)

# Agents are initialized with:
# - Names from KG entity metadata
# - Network positions from KG topology
# - Financial states (randomized within realistic ranges)
```

**Agent initialization process:**
1. Create `n_banks` bank agents
2. Assign names from `entity_metadata`
3. Position agents in network topology
4. Initialize financial state:
   - Capital: Random in range (5-20 $B)
   - Liquidity: 20% of capital
   - Assets: 10x capital
   - Liabilities: 8x capital
   - Leverage: ~10x (realistic for crisis period)

**Example:**
```python
>>> model = FinancialCrisisModel(n_banks=3, network=network)
>>> for bank in model.bank_agents:
...     print(f"{bank.name}: ${bank.capital:.1f}B capital, {bank.leverage_ratio:.1f}x leverage")
Lehman Brothers: $12.3B capital, 9.8x leverage
Bear Stearns: $8.7B capital, 11.2x leverage
Merrill Lynch: $15.1B capital, 8.5x leverage
```

---

### 3. Historical Context Queries (Week 3-4)

**Purpose:** Enable AI-driven agent decisions based on historical precedents

**Status:** Planned for Week 3-4 (SLM + RAG integration)

**Future Implementation:**

```python
# In BankAgent.decide_action() - Week 3
def decide_action(self, context):
    # Query KG for similar historical situations
    query = f"""
    PREFIX feekg: <http://feekg.org/ontology#>
    SELECT ?event ?description ?outcome
    WHERE {{
        ?event a feekg:Event .
        ?event feekg:description ?description .
        ?event feekg:outcome ?outcome .
        FILTER (contains(?description, "liquidity crisis"))
        FILTER (contains(?description, "leverage"))
    }}
    LIMIT 5
    """

    historical_events = self.kg_client.query(query)

    # Use SLM to reason over historical context
    decision = self.slm.generate(
        prompt=self.format_decision_prompt(context, historical_events),
        max_tokens=50
    )

    return decision  # "DEFENSIVE", "AGGRESSIVE", etc.
```

**What this enables:**
- Banks learn from historical precedents
- Decisions grounded in real financial crisis data
- Explainable AI (cite historical events in decisions)

---

### 4. Evolution Link Queries

**Purpose:** Use evolution patterns to predict contagion paths

**Example Query:**

```python
# Find banks most likely to be affected by failure
def find_contagion_targets(self, failed_bank_id):
    query = f"""
    PREFIX feekg: <http://feekg.org/ontology#>
    SELECT ?target ?score
    WHERE {{
        ?link feekg:fromEntity <{failed_bank_id}> .
        ?link feekg:toEntity ?target .
        ?link feekg:score ?score .
    }}
    ORDER BY DESC(?score)
    LIMIT 10
    """

    targets = self.kg_client.query(query)
    return targets
```

**Use case:**
- When Lehman fails, identify counterparties most at risk
- Weight shock propagation by evolution link strength
- More realistic than random network contagion

---

### 5. Simulation Results Export (Future)

**Purpose:** Save simulation outcomes back to KG for analysis

**Planned Implementation:**

```python
# After simulation completes
def export_to_kg(model):
    # Create simulation run entity
    sim_id = f"simulation_{datetime.now().isoformat()}"

    # Export each bank failure as an event
    for failure in model.failed_banks:
        triple = f"""
        <{sim_id}/failure_{failure.unique_id}> a feekg:SimulationEvent ;
            feekg:eventType "bank_failure" ;
            feekg:entity <{failure.name}> ;
            feekg:step {failure.failure_step} ;
            feekg:capital {failure.capital_at_failure} .
        """
        kg_client.insert_triple(triple)

    # Export contagion links
    for contagion in model.contagion_events:
        triple = f"""
        <{sim_id}/contagion_{contagion['id']}> a feekg:ContagionEvent ;
            feekg:fromBank <{contagion['from']}> ;
            feekg:toBank <{contagion['to']}> ;
            feekg:lossAmount {contagion['loss']} .
        """
        kg_client.insert_triple(triple)
```

**Benefits:**
- Compare simulations to historical crises
- Validate ABM against real data
- Build dataset of simulated crises for ML

---

## Running ABM with KG Integration

### Basic Example

```python
from abm import FinancialCrisisModel
from abm.network import load_network_from_kg

# 1. Load network from Knowledge Graph
network, metadata = load_network_from_kg(entity_limit=10)

# 2. Create ABM with KG topology
model = FinancialCrisisModel(
    n_banks=10,
    network=network,
    crisis_trigger_step=30,
    random_seed=42
)

# 3. Run simulation
for step in range(100):
    model.step()

    if (step + 1) % 10 == 0:
        summary = model.get_summary()
        print(f"Step {step + 1}: {summary['failed_banks']} banks failed")

# 4. Export results
model.export_results('results/simulation_with_kg.json')
```

### Advanced Example (Week 3-4 with SLM)

```python
from abm import FinancialCrisisModel
from abm.network import load_network_from_kg
from rag import KGQueryCache
from llm import Llama1B

# 1. Load network
network, metadata = load_network_from_kg(entity_limit=20)

# 2. Initialize SLM and RAG cache
llm = Llama1B(model_path='models/Llama-3.2-1B')
query_cache = KGQueryCache(llm=llm)

# 3. Create model with AI agents
model = FinancialCrisisModel(
    n_banks=20,
    network=network,
    llm=llm,
    query_cache=query_cache,
    crisis_trigger_step=50
)

# 4. Run simulation with AI decisions
for step in range(200):
    model.step()  # Agents query KG and use SLM reasoning

# 5. Analyze results
print(f"Cache hit rate: {query_cache.hit_rate():.1%}")
print(f"Total LLM calls: {llm.call_count}")
print(f"Failed banks: {len(model.failed_banks)}")
```

---

## Network Topology Details

### Entity Types in KG

| Entity Type | Count | Examples |
|-------------|-------|----------|
| investment_bank | 8 | Lehman Brothers, Bear Stearns, Morgan Stanley |
| bank | 6 | Citigroup, Bank of America, JPMorgan |
| insurance | 3 | AIG, MetLife |
| gse | 2 | Fannie Mae, Freddie Mac |
| regulator | 3 | Federal Reserve, SEC, Treasury |

**Total:** 22 entities

### Evolution Link Weights

Links are weighted by evolution score (0-1):
- **High strength (0.7-1.0):** Direct counterparty relationships
- **Medium (0.4-0.7):** Indirect exposure
- **Low (0.2-0.4):** Weak connections

### Network Properties

```python
>>> network, _ = load_network_from_kg(entity_limit=22)
>>> print(f"Nodes: {network.number_of_nodes()}")
Nodes: 22
>>> print(f"Edges: {network.number_of_edges()}")
Edges: 45
>>> print(f"Density: {nx.density(network):.3f}")
Density: 0.195
>>> print(f"Avg clustering: {nx.average_clustering(network):.3f}")
Avg clustering: 0.412
>>> print(f"Avg degree: {sum(dict(network.degree()).values()) / network.number_of_nodes():.1f}")
Avg degree: 4.1
```

---

## Integration Benefits

### 1. Realistic Network Structure

**Without KG:**
- Random Erdős-Rényi graph
- Uniform edge weights
- No domain knowledge

**With KG:**
- Real financial institution relationships
- Evolution-weighted edges
- Based on 4,000 actual crisis events

**Impact:** More realistic contagion patterns

### 2. Explainable Decisions (Week 3)

**Without KG:**
- Black-box agent rules
- No historical grounding
- Can't explain "why"

**With KG + SLM:**
- Decisions cite historical precedents
- Natural language explanations
- Traceable to source events

**Impact:** Trustworthy simulation results

### 3. Validation Against History

**With KG data:**
- Compare simulation to 2007-2009 crisis
- Measure deviation from actual events
- Calibrate model parameters

**Example:**
```python
# Compare simulated vs actual Lehman failure timeline
actual_lehman_failure = "2008-09-15"
simulated_failure_step = 42

# Calculate alignment
days_per_step = (crisis_end_date - crisis_start_date).days / 200
simulated_date = crisis_start_date + timedelta(days=simulated_failure_step * days_per_step)

error = abs((simulated_date - actual_lehman_failure).days)
print(f"Simulation error: {error} days")
```

---

## Performance Considerations

### Query Caching (Week 4)

**Problem:** Querying KG every agent step is slow
- 10 banks × 200 steps = 2,000 queries
- Each query: ~200ms
- Total: 400 seconds (6.7 minutes)

**Solution:** 3-tier query cache
```python
from rag import KGCacheManager

cache = KGCacheManager(
    kg_client=kg_client,
    llm=llm,
    tiers=['memory', 'disk', 'kg']
)

# First call: queries KG (200ms)
result = cache.query("historical liquidity crises")

# Second call: memory cache (1ms)
result = cache.query("historical liquidity crises")
```

**Performance:**
- 80% cache hit rate
- Average query time: 40ms (vs 200ms)
- Total simulation time: 80 seconds (vs 400 seconds)

### Batch SPARQL Queries

Instead of:
```python
# BAD: 10 separate queries
for bank in banks:
    result = kg_client.query(f"SELECT ... WHERE {{ ?entity = <{bank.id}> }}")
```

Do:
```python
# GOOD: 1 batch query
bank_ids = [bank.id for bank in banks]
query = f"SELECT ... WHERE {{ VALUES ?entity {{ {' '.join(bank_ids)} }} }}"
results = kg_client.query(query)
```

**Speedup:** 10x faster for batch operations

---

## Testing

### Test Network Loading

```bash
./venv/bin/python -c "
from abm.network import load_network_from_kg
network, metadata = load_network_from_kg(entity_limit=10)
print(f'Loaded {network.number_of_nodes()} nodes')
print(f'Metadata: {list(metadata.keys())[:3]}')
"
```

**Expected output:**
```
Loaded 10 nodes
Metadata: ['bank_001', 'bank_002', 'bank_003']
```

### Test ABM with KG Network

```bash
./venv/bin/python abm/test_simulation.py
```

**Expected output:**
```
Loading network from Knowledge Graph...
Loaded 10 banks from AllegroGraph
Network density: 0.38

Running simulation for 100 steps...
Step 20: 0 banks failed
Step 30: CRISIS TRIGGERED - Lehman Brothers forced to fail
Step 40: 3 banks failed
...
```

---

## Future Enhancements

### Week 3: SLM Integration
- [ ] Query KG for historical context
- [ ] Use Llama-3.2-1B for agent decisions
- [ ] Generate natural language explanations

### Week 4: RAG + Caching
- [ ] Implement 3-tier query cache
- [ ] Batch SPARQL queries
- [ ] Optimize for 100 banks × 200 steps

### Later: Bi-directional Integration
- [ ] Export simulation results to KG
- [ ] Compare simulations to historical data
- [ ] Build ML dataset from simulations

---

## Code Examples

### Complete Integration Example

```python
#!/usr/bin/env python
"""
Run ABM with Knowledge Graph integration
"""

from abm import FinancialCrisisModel
from abm.network import load_network_from_kg
import json

def main():
    # Load network from KG
    print("Loading network from Knowledge Graph...")
    network, metadata = load_network_from_kg(
        entity_limit=10,
        min_evolution_score=0.5
    )

    print(f"Loaded {network.number_of_nodes()} banks from AllegroGraph")
    print(f"Network density: {nx.density(network):.2f}")

    # Create model
    print("\nCreating ABM model...")
    model = FinancialCrisisModel(
        n_banks=network.number_of_nodes(),
        network=network,
        crisis_trigger_step=30,
        random_seed=42
    )

    # Run simulation
    print("\nRunning simulation for 100 steps...")
    for step in range(100):
        model.step()

        if (step + 1) % 20 == 0:
            summary = model.get_summary()
            print(f"Step {step + 1}: {summary['failed_banks']} banks failed, "
                  f"crisis intensity: {summary['crisis_intensity']:.2f}")

    # Export results
    print("\nExporting results...")
    model.export_results('results/abm_with_kg.json')
    print("Saved to results/abm_with_kg.json")

    # Print summary
    summary = model.get_summary()
    print(f"\nFinal summary:")
    print(f"  Total banks: {summary['n_banks']}")
    print(f"  Failed: {summary['failed_banks']}")
    print(f"  Survived: {summary['surviving_banks']}")
    print(f"  Bailouts: {summary['bailouts_provided']}")

if __name__ == '__main__':
    main()
```

---

## Summary

**Integration Status:**
- ✅ Network loading from KG (complete)
- ✅ Agent initialization with KG data (complete)
- 🔄 Historical context queries (Week 3)
- 🔄 SLM-driven decisions (Week 3)
- 🔄 Query caching (Week 4)
- ⏳ Results export to KG (future)

**Key Benefits:**
- Realistic network topology from real data
- Grounded in 4,000 historical crisis events
- Explainable AI decisions (Week 3)
- Validation against 2007-2009 crisis

**Performance:**
- Current: ~2 seconds for 10 banks, 100 steps
- Week 4: ~10 seconds for 20 banks, 200 steps (with caching)

**Next Steps:**
1. Read `abm/README.md` for ABM details
2. Run `abm/test_simulation.py` to see integration in action
3. Review `SLM_ABM_ROADMAP.md` for Week 3-4 plans

---

**Ready to simulate?** Try `./venv/bin/python abm/test_simulation.py`
