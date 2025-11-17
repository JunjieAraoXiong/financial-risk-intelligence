# Lehman Brothers Case Study

Complete guide for implementing the Lehman Brothers financial crisis case study in FE-EKG.

---

# Lehman Brothers Case Study - Complete Pipeline

## Overview

This document describes the complete pipeline for processing Capital IQ data through FE-EKG and converting it to RDF triples for AllegroGraph.

---

## Pipeline Architecture

```
Capital IQ Raw Data (.xlsx/.csv)
         ↓
    Process & Filter
    (process_capital_iq.py)
         ↓
    FE-EKG JSON Format
    (lehman_case_study.json)
         ↓
    Load into Neo4j + Evolution Analysis
    (load_lehman.py)
         ↓
    Property Graph (Neo4j)
    - 12 entities
    - 7 events
    - 4 risks
    - 21 evolution links
         ↓
    Convert to RDF Triples
    (convert_lehman_to_rdf.py)
         ↓
    RDF Triple Store
    - 278 triples in Turtle/RDF-XML/N-Triples
         ↓
    Upload to AllegroGraph (HTTPS)
    (optional: --upload flag)
```

---

## Step-by-Step Workflow

### Step 1: Download Capital IQ Data

**Your Task:**
1. Access Capital IQ via university library
2. Download financial crisis data (2007-2009)
3. Aim for 500-2,000 events covering:
   - Lehman Brothers
   - Bear Stearns
   - AIG
   - Other major financial institutions
4. Save to: `data/capital_iq_raw/financial_crisis_2007_2009.xlsx`

**See:** `data/CAPITAL_IQ_DOWNLOAD_GUIDE.md` for detailed instructions

### Step 2: Process Capital IQ Data

**Command:**
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --filter lehman \
    --output data/capital_iq_processed/lehman_case_study.json
```

**What it does:**
- Loads Excel/CSV file from Capital IQ
- Normalizes column names (handles various Capital IQ export formats)
- Filters for Lehman-related events:
  - Lehman Brothers
  - Bear Stearns (precursor)
  - AIG (systemic contagion)
  - Related institutions
- Filters date range: 2007-2009
- Converts to FE-EKG JSON format
- Infers entity types (bank, investment_bank, regulator, etc.)
- Normalizes event types (bankruptcy, merger_acquisition, etc.)

**Output:**
- `data/capital_iq_processed/lehman_case_study.json`
- Structured JSON with `events[]` and `entities[]`

### Step 3: Load into Neo4j with Evolution Analysis

**Command:**
```bash
./venv/bin/python ingestion/load_lehman.py
```

**What it does:**
1. Clears existing Neo4j data
2. Loads entities (12 entities: banks, regulators, markets)
3. Loads events (7 key events from Jan-Sep 2008)
4. Links entities to events
5. Runs 6 evolution analysis methods:
   - Temporal Correlation (TCDI)
   - Entity Overlap
   - Semantic Similarity
   - Topic Relevance
   - Event Type Causality
   - Emotional Consistency
6. Creates 21 evolution links (score ≥ 0.2)
7. Creates risk nodes for critical events
8. Links events to risks

**Result:**
```
Database statistics:
  - Entities: 12
  - Events: 7
  - Risks: 4
  - Evolution links: 21
  - Entity-Event links: 16
  - Event-Risk links: 4
```

### Step 4: Convert to RDF Triples

**Command:**
```bash
./venv/bin/python scripts/convert_lehman_to_rdf.py
```

**What it does:**
1. Connects to Neo4j
2. Fetches all nodes and relationships
3. Converts to RDF using FE-EKG ontology:
   - `http://feekg.org/ontology#` (classes and properties)
   - `http://feekg.org/lehman/` (instance URIs)
4. Creates 278 RDF triples
5. Saves in 3 formats:
   - Turtle (.ttl) - human-readable
   - RDF/XML (.xml) - legacy systems
   - N-Triples (.nt) - line-by-line processing

**Output Files:**
```
results/lehman_graph.ttl    (11 KB)
results/lehman_graph.xml    (25 KB)
results/lehman_graph.nt     (30 KB)
```

**Example Triples:**
```turtle
@prefix feekg: <http://feekg.org/ontology#> .
@prefix lehman: <http://feekg.org/lehman/> .

# Entity
lehman:ent_009 a feekg:Entity ;
    feekg:entityId "ent_009" ;
    feekg:name "Lehman Brothers" ;
    feekg:entityType "investment_bank" ;
    feekg:involves lehman:evt_004 .

# Event
lehman:evt_004 a feekg:Event ;
    feekg:eventId "evt_004" ;
    feekg:date "2008-09-15" ;
    feekg:eventType "bankruptcy" ;
    feekg:headline "Lehman Brothers files for bankruptcy" ;
    feekg:description "Lehman Brothers Holdings Inc filed for Chapter 11..." ;
    feekg:triggers lehman:risk_evt_004 .

# Evolution Link
lehman:evt_003_to_evt_004 a feekg:EvolutionLink ;
    feekg:fromEvent lehman:evt_003 ;
    feekg:toEvent lehman:evt_004 ;
    feekg:score 0.85 ;
    feekg:temporalScore 0.92 ;
    feekg:entityScore 0.88 ;
    feekg:causalityScore 0.95 .

# Risk
lehman:risk_evt_004 a feekg:Risk ;
    feekg:riskId "risk_evt_004" ;
    feekg:riskType "credit_risk" ;
    feekg:severity "critical" ;
    feekg:likelihood 0.95 .
```

### Step 5: Upload to AllegroGraph (Optional)

**Command:**
```bash
./venv/bin/python scripts/convert_lehman_to_rdf.py --upload
```

**What it does:**
- Uses HTTPS REST API (bypasses port 10035 blocking)
- Connects to `https://qa-agraph.nelumbium.ai/`
- Creates repository `feekg_dev` if needed
- Clears existing data
- Uploads 278 triples
- Verifies upload success

**AllegroGraph Backend:**
- Uses `config/allegrograph_https_backend.py`
- HTTPS port 443 (not blocked by firewall)
- REST API for all operations
- Full SPARQL query support

---

## Current Status: Working Pipeline with Template Data

✅ **Completed and tested:**

1. **Capital IQ Processing Pipeline**
   - `ingestion/process_capital_iq.py` - Tested with template CSV
   - Successfully processes 7 events, 12 entities

2. **Neo4j Loading with Evolution**
   - `ingestion/load_lehman.py` - Fully tested
   - Creates complete knowledge graph
   - Runs all 6 evolution methods
   - Creates 21 evolution links
   - Generates risk nodes automatically

3. **RDF Conversion**
   - `scripts/convert_lehman_to_rdf.py` - Fully tested
   - Generates 278 triples
   - Outputs 3 RDF formats
   - Ready for AllegroGraph upload

4. **Supporting Infrastructure**
   - AllegroGraph HTTPS backend (workaround for port blocking)
   - Comprehensive documentation
   - Template data for testing

---

## Next Steps

### Immediate (Waiting on User):

1. **Download Capital IQ bulk data**
   - See: `data/CAPITAL_IQ_DOWNLOAD_GUIDE.md`
   - Target: 500-2,000 events from financial crisis
   - Save to: `data/capital_iq_raw/financial_crisis_2007_2009.xlsx`

2. **Process real data**
   - Run same pipeline with real Capital IQ data
   - Should extract 30-50 Lehman-related events (vs. 7 template events)
   - More comprehensive evolution analysis

### For Presentation:

3. **Create 3 Visuals** (mentioned by user for collaboration with Jayana):
   - Visual 1: News headline → structured triple (flowchart)
   - Visual 2: Event evolution sequence (timeline with causality scores)
   - Visual 3: Risk propagation network (three-layer diagram)

4. **Create GitHub Branch**
   - Branch: `feature/rdf-allegrograph`
   - Focus: RDF triple output instead of Neo4j LPG
   - Include all Lehman pipeline work

5. **SPARQL Query Examples**
   - Create `scripts/query_lehman_sparql.py`
   - Example queries for evolution chains
   - Risk propagation queries
   - Timeline queries

---

## File Structure

```
feekg/
├── data/
│   ├── capital_iq_raw/              # Raw Capital IQ downloads
│   │   └── financial_crisis_2007_2009.xlsx  ← User downloads here
│   ├── capital_iq_processed/        # Processed FE-EKG JSON
│   │   └── lehman_case_study.json   ← Output from process_capital_iq.py
│   ├── lehman_crisis_template.csv   # Template for testing
│   ├── CAPITAL_IQ_DOWNLOAD_GUIDE.md # Download instructions
│   └── README_WORKFLOW.md           # Workflow guide
│
├── ingestion/
│   ├── process_capital_iq.py        # Capital IQ → FE-EKG JSON
│   └── load_lehman.py               # JSON → Neo4j + Evolution
│
├── scripts/
│   └── convert_lehman_to_rdf.py     # Neo4j → RDF triples
│
├── config/
│   ├── graph_backend.py             # Neo4j backend
│   └── allegrograph_https_backend.py # AllegroGraph HTTPS API
│
├── evolution/
│   └── methods.py                   # 6 evolution analysis methods
│
└── results/
    ├── lehman_graph.ttl             # Turtle RDF
    ├── lehman_graph.xml             # RDF/XML
    └── lehman_graph.nt              # N-Triples
```

---

## Key Features

### 1. Flexible Data Processing
- Handles various Capital IQ export formats
- Automatic column name normalization
- Multiple filtering options:
  - By company name (partial match, case-insensitive)
  - By date range
  - By event type

### 2. Event Evolution Analysis
- 6 sophisticated methods from FE-EKG paper
- Composite scoring (weighted average)
- Threshold filtering (≥ 0.2)
- Stores component scores separately

### 3. RDF Triple Generation
- FE-EKG ontology compliant
- Preserves all evolution metadata
- Multiple serialization formats
- Ready for SPARQL querying

### 4. AllegroGraph Integration
- HTTPS REST API (bypasses firewall)
- Automatic repository management
- Bulk upload support
- SPARQL query interface

---

## Testing with Template Data

Current test results with `data/lehman_crisis_template.csv`:

**Input:**
- 7 events (Jan 2008 - Sep 2008)
- Key moments: Bear Stearns rescue, Lehman losses, bankruptcy, AIG bailout

**Output:**
- ✅ 12 entities extracted
- ✅ 7 events loaded
- ✅ 21 evolution links computed
- ✅ 4 risks generated
- ✅ 278 RDF triples created

**Evolution Link Example:**
```
evt_003 (BofA backs out) → evt_004 (Lehman bankruptcy)
  Score: 0.85
  - Temporal: 0.92 (5 days apart)
  - Entity: 0.88 (shared entities: Lehman)
  - Causality: 0.95 (failed acquisition → bankruptcy)
```

---

## Summary

**The complete Capital IQ → FE-EKG → RDF pipeline is ready and tested.**

All infrastructure is in place to:
1. Process bulk Capital IQ data
2. Extract Lehman Brothers case study
3. Run sophisticated evolution analysis
4. Convert to RDF triples
5. Upload to AllegroGraph

**Waiting on:** User to download real Capital IQ data (500-2,000 events).

Once data is ready, the entire pipeline runs with 3 commands:
1. Process: `./venv/bin/python ingestion/process_capital_iq.py --input [file] --filter lehman`
2. Load: `./venv/bin/python ingestion/load_lehman.py`
3. Convert: `./venv/bin/python scripts/convert_lehman_to_rdf.py --upload`

---

**Total Development Time for This Pipeline:** ~4 hours (including testing and documentation)

**Lines of Code Added:**
- `process_capital_iq.py`: ~350 lines
- `load_lehman.py`: ~320 lines
- `convert_lehman_to_rdf.py`: ~350 lines
- Documentation: ~1,000 lines
- **Total: ~2,020 lines**


---
## Quick Start

# Lehman Brothers Pipeline - Quick Start

## 3-Step Pipeline (After You Download Capital IQ Data)

### Step 1: Process Capital IQ Data
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/your_file.xlsx \
    --filter lehman
```

**Output:** `data/capital_iq_processed/lehman_case_study.json`

---

### Step 2: Load into Neo4j + Run Evolution
```bash
./venv/bin/python ingestion/load_lehman.py
```

**Creates:**
- Entities (financial institutions, regulators)
- Events (chronological timeline)
- Risks (credit, systemic, market)
- Evolution links (21+ connections with causality scores)

---

### Step 3: Convert to RDF Triples
```bash
./venv/bin/python scripts/convert_lehman_to_rdf.py
```

**Output:**
- `results/lehman_graph.ttl` (Turtle format)
- `results/lehman_graph.xml` (RDF/XML format)
- `results/lehman_graph.nt` (N-Triples format)

**Optional: Upload to AllegroGraph**
```bash
./venv/bin/python scripts/convert_lehman_to_rdf.py --upload
```

---

## Alternative Commands

### Process All Capital IQ Data (Not Just Lehman)
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --filter all \
    --output data/capital_iq_processed/all_events.json
```

### Process Specific Companies
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --companies "Lehman Brothers,Bear Stearns,AIG,Merrill Lynch"
```

### Custom Output File
```bash
./venv/bin/python ingestion/load_lehman.py \
    --input data/capital_iq_processed/custom_case_study.json
```

---

## What You Need to Download

**From Capital IQ (via university library):**

1. Time Period: 2007-01-01 to 2009-12-31
2. Industries: Financial Services, Banks, Investment Banking
3. Event Types: All
4. Target Size: 500-2,000 events
5. Save As: `data/capital_iq_raw/financial_crisis_2007_2009.xlsx`

**Detailed instructions:** See `data/CAPITAL_IQ_DOWNLOAD_GUIDE.md`

---

## Current Status with Template Data

**Input:** 7 events from Lehman crisis template

**Output:**
- ✅ 12 entities (Lehman Brothers, Bear Stearns, AIG, JPMorgan, etc.)
- ✅ 7 events (Jan 2008 - Sep 2008)
- ✅ 4 risks (credit, systemic, market)
- ✅ 21 evolution links (temporal, causal, semantic)
- ✅ 278 RDF triples

**Processing time:** < 10 seconds end-to-end

---

## Troubleshooting

### "File not found"
Make sure you saved Capital IQ data to:
```
data/capital_iq_raw/your_file.xlsx
```

### "Cannot connect to Neo4j"
Start Neo4j first:
```bash
./scripts/start_neo4j.sh
```

### "No events found for Lehman"
Check if Capital IQ data contains Lehman Brothers events:
- Search for "Lehman" or "Lehman Brothers"
- Verify date range includes 2008
- Try `--filter all` to see all events

### "Column names don't match"
The processor handles various Capital IQ formats automatically.
It normalizes:
- "Company Name" → "company"
- "Event Date" → "date"
- "Event Type" → "event_type"

---

## Generated Files Location

```
data/
├── capital_iq_processed/
│   └── lehman_case_study.json  ← FE-EKG format

results/
├── lehman_graph.ttl            ← Turtle RDF (human-readable)
├── lehman_graph.xml            ← RDF/XML
└── lehman_graph.nt             ← N-Triples
```

---

## RDF Triple Example

```turtle
@prefix feekg: <http://feekg.org/ontology#> .
@prefix lehman: <http://feekg.org/lehman/> .

# Lehman Brothers bankruptcy event
lehman:evt_004 a feekg:Event ;
    feekg:date "2008-09-15" ;
    feekg:eventType "bankruptcy" ;
    feekg:headline "Lehman Brothers files for bankruptcy" ;
    feekg:description "Lehman Brothers Holdings Inc filed for Chapter 11..." ;
    feekg:sentiment 0.0 ;
    feekg:triggers lehman:risk_evt_004 .

# Evolution: Failed acquisition → Bankruptcy
lehman:evt_003_to_evt_004 a feekg:EvolutionLink ;
    feekg:fromEvent lehman:evt_003 ;  # BofA backs out
    feekg:toEvent lehman:evt_004 ;    # Lehman bankruptcy
    feekg:score 0.85 ;
    feekg:temporalScore 0.92 ;
    feekg:causalityScore 0.95 .

# Triggered credit risk
lehman:risk_evt_004 a feekg:Risk ;
    feekg:riskType "credit_risk" ;
    feekg:severity "critical" ;
    feekg:likelihood 0.95 .
```

---

## Complete Documentation

- **Architecture:** `LEHMAN_CASE_STUDY_PIPELINE.md`
- **Workflow:** `data/README_WORKFLOW.md`
- **Download Guide:** `data/CAPITAL_IQ_DOWNLOAD_GUIDE.md`

---

**Ready to process your Capital IQ data!**
