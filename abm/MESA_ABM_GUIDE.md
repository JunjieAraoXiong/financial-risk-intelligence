# Mesa ABM Framework Guide

This document explains how the Mesa Agent-Based Modeling framework works and how it's used in the FE-EKG financial crisis simulation.

## What is Mesa?

**Mesa** is a Python framework for building Agent-Based Models (ABMs). ABMs simulate complex systems by modeling individual agents that interact with each other and their environment.

**Key features**:
- Pure Python (no external dependencies like NetLogo)
- Built-in data collection and visualization
- Modular design (Model, Agents, Schedulers)

## Core Concepts

### 1. Model (`mesa.Model`)

The **Model** is the container for the entire simulation. It holds:
- All agents
- Global state (environment variables)
- The simulation clock (steps)

```python
from mesa import Model

class FinancialCrisisModel(Model):
    def __init__(self, n_banks=10):
        super().__init__()
        self.num_agents = n_banks
        # Create agents here

    def step(self):
        # Advance simulation by one time unit
        self.agents.shuffle().do("step")
```

### 2. Agent (`mesa.Agent`)

**Agents** are the individual actors in the simulation. Each agent:
- Has a unique ID (auto-assigned)
- Belongs to a model
- Has state variables (capital, liquidity, etc.)
- Has a `step()` method defining behavior

```python
from mesa import Agent

class BankAgent(Agent):
    def __init__(self, model, entity_data):
        super().__init__(model)  # Registers with model.agents
        self.capital = entity_data['capital']
        self.liquidity = entity_data['liquidity']

    def step(self):
        # Agent behavior each time step
        action = self.decide_action()
        self.execute_action(action)
```

### 3. Agent Collection (`model.agents`)

In Mesa 3.x, agents are automatically added to `model.agents` when instantiated. You can:

```python
# Iterate over all agents
for agent in self.model.agents:
    print(agent.unique_id)

# Shuffle and execute (random activation)
self.agents.shuffle().do("step")

# Filter agents
alive_banks = [a for a in self.agents if not a.failed]
```

### 4. Time Advancement

The simulation advances in discrete **steps**. Each call to `model.step()`:
1. Updates global state (market conditions)
2. Activates agents (calls their `step()` methods)
3. Collects data

**Activation patterns**:
- **Sequential**: Agents act in fixed order
- **Random**: Agents act in random order (prevents order bias)
- **Simultaneous**: All agents observe, then all act

## How It Works in This Project

### Model: `FinancialCrisisModel`

Location: `abm/model.py`

**Initialization** (`__init__`):
1. Creates 10 bank agents
2. Assigns groups: Banks 0-4 (RAG-enabled) vs Banks 5-9 (no RAG)
3. Initializes SLM (Llama-3.2-1B-Instruct)

**Each step** (`step`):
1. Increments week counter
2. Sets market conditions (volatility, liquidity factor)
3. Triggers Lehman shock at week 9 (September 2008)
4. Queries RAG for market context
5. Activates all agents in random order

```python
def step(self):
    self.steps += 1

    # Set market conditions
    if self.steps >= 9:  # Lehman shock
        market_volatility = 0.80
        liquidity_factor = 0.30
    else:
        market_volatility = 0.10
        liquidity_factor = 1.0

    # Query RAG
    chunks = get_context_multi_query(...)

    # Store context for agents
    self.market_context = {
        "volatility": market_volatility,
        "liquidity": liquidity_factor,
        "news": news_context
    }

    # Activate agents
    self.agents.shuffle().do("step")
```

### Agent: `BankAgent`

Location: `abm/agents.py`

**State variables**:
- `capital`: Available capital (starts at 100B)
- `liquidity`: Liquidity ratio (starts at 0.20)
- `risk_score`: Risk metric (0.0-1.0)
- `failed`: Whether bank has failed
- `use_rag`: Whether agent uses RAG (Group A vs B)

**Each step** (`step`):
1. Check if failed (skip if so)
2. Get context (RAG or placeholder)
3. Decide action via SLM
4. Execute action (DEFENSIVE or MAINTAIN)
5. Check failure condition

```python
def step(self):
    if self.failed:
        return

    # 1. Get context
    if self.use_rag and volatility >= 0.15:
        context = get_agent_context(...)
    else:
        context = "No specific news."

    # 2. Decide via SLM
    action = self.decide_action(context)

    # 3. Execute
    self.execute_action(action)

    # 4. Check failure
    effective_liquidity = self.liquidity * liquidity_factor
    if effective_liquidity < 0.05 or self.capital < 0:
        self.fail()
```

## Simulation Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Model Initialization                 │
│  - Create 10 BankAgents (5 RAG, 5 non-RAG)             │
│  - Initialize SLM                                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              For each week (52 total):                  │
│                                                         │
│  1. Model.step()                                        │
│     ├─ Update week counter                              │
│     ├─ Set market conditions                            │
│     │   └─ Week >= 9: Lehman shock (80% vol, low liq)  │
│     ├─ Query RAG (multi-query + HyDE)                   │
│     └─ Store market_context                             │
│                                                         │
│  2. Activate agents (random order)                      │
│     For each BankAgent:                                 │
│     ├─ Skip if failed                                   │
│     ├─ Get context (RAG or placeholder)                 │
│     ├─ SLM decides: DEFENSIVE or MAINTAIN               │
│     ├─ Execute action                                   │
│     │   ├─ DEFENSIVE: +5% liquidity, -1B capital       │
│     │   └─ MAINTAIN: no change                          │
│     └─ Check failure (liq < 5% or capital < 0)          │
│                                                         │
│  3. Collect data                                        │
│     └─ Record agent states for analysis                 │
└─────────────────────────────────────────────────────────┘
```

## Key Mesa 3.x Changes

This project uses Mesa 3.x which has breaking changes from 2.x:

| Feature | Mesa 2.x | Mesa 3.x |
|---------|----------|----------|
| Agent registration | `self.schedule.add(agent)` | Automatic via `super().__init__(model)` |
| Agent collection | `self.schedule.agents` | `self.agents` |
| Activation | `self.schedule.step()` | `self.agents.shuffle().do("step")` |
| Scheduler import | `from mesa.time import RandomActivation` | Not needed |

## Running the Simulation

```bash
cd /Users/hansonxiong/Desktop/DDP/feekg

# Set environment
source .env
export PYTHONPATH=.
export TOKENIZERS_PARALLELISM=false

# Run with default parameters
python run_experiment.py

# Run with custom liquidity factor
python run_experiment.py --liquidity-factor 0.15
```

## Extending the Model

### Add a New Agent Type

```python
class RegulatorAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.intervention_threshold = 0.10

    def step(self):
        # Check system health
        failed_count = sum(1 for a in self.model.agents
                          if hasattr(a, 'failed') and a.failed)

        if failed_count > 2:
            self.intervene()
```

### Add Data Collection

```python
from mesa.datacollection import DataCollector

class FinancialCrisisModel(Model):
    def __init__(self):
        super().__init__()

        self.datacollector = DataCollector(
            model_reporters={
                "Total Capital": lambda m: sum(a.capital for a in m.agents),
                "Failed Banks": lambda m: sum(1 for a in m.agents if a.failed)
            },
            agent_reporters={
                "Capital": "capital",
                "Liquidity": "liquidity"
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle().do("step")
```

### Add Inter-Agent Interactions (Contagion)

```python
def step(self):
    # ... existing code ...

    # Check counterparty exposure
    for other in self.model.agents:
        if other != self and other.failed:
            # Lose 10% of exposure to failed bank
            self.capital -= self.exposure_to(other) * 0.10
```

## Comparison to Other ABM Frameworks

| Framework | Language | Strengths | Weaknesses |
|-----------|----------|-----------|------------|
| **Mesa** | Python | Easy integration with ML/data science, pure Python | Slower than compiled languages |
| NetLogo | NetLogo | Great visualization, educational | Limited ML integration |
| MASON | Java | High performance | Verbose, less ML-friendly |
| Repast | Java/Python | Scalable, HPC support | Steeper learning curve |

## Resources

- **Mesa Documentation**: https://mesa.readthedocs.io/
- **Mesa GitHub**: https://github.com/projectmesa/mesa
- **Mesa Examples**: https://github.com/projectmesa/mesa-examples
- **ABM Tutorial**: https://mesa.readthedocs.io/en/stable/tutorials/intro_tutorial.html

---

Last Updated: 2025-11-22
