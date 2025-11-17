# What You Can Do With FEEKG Triples

## Current Database Status

- **Total Triples**: 74,012
- **Events**: 4,398 (2007-2009 financial crisis)
- **Entities**: 18 (banks, investment firms, regulators)
- **Date Range**: 2007-01-01 to 2009-12-31
- **CSV Traceability**: 100% (every event traceable to source)
- **Classification Quality**: 0% unknown, 87.1% avg confidence

---

## 1. RAG-Powered Chatbot with Source Verification

### What You Can Ask

**Natural Language Questions:**
- "What legal issues did Morgan Stanley face in 2009?"
- "Show me all credit downgrades during the Lehman crisis"
- "Which companies had management changes in 2008?"
- "What were the biggest restructuring events?"
- "Find events related to Goldman Sachs and Bear Stearns"

### How It Works

```
User Question
    ↓
OpenAI Embeddings (text-embedding-3-small)
    ↓
Vector Search in AllegroGraph
    ↓
Retrieve Relevant Events + CSV Source Metadata
    ↓
GPT-4 Generates Answer with Citations
    ↓
Show: Answer + CSV Row Numbers + Confidence Scores
```

### Example Response

```
Q: "What legal issues did Morgan Stanley face in 2009?"

A: Morgan Stanley faced several legal challenges in 2009:

1. Virgin Islands Pension Fund Lawsuit (Aug 21, 2009)
   - Type: Lawsuit for defrauding
   - CSV Source: Row 68940, Capital IQ ID 83730941
   - Confidence: 95% (pattern_match)
   - [View in CSV]

2. Securities Class Action Settlement (Mar 15, 2009)
   - Type: Legal settlement
   - CSV Source: Row 67892, Capital IQ ID 82156743
   - Confidence: 95% (pattern_match)
   - [View in CSV]

Sources: capital_iq_download.csv
```

**Cost**: ~$0.0005 per query (very cheap!)

---

## 2. Complex Financial Analysis Queries

### Query 1: Event Timeline Analysis

**Find all events by type over time:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?date ?type (COUNT(?event) as ?count)
WHERE {
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
}
GROUP BY ?date ?type
ORDER BY ?date
```

**Use Case**: Create timeline visualizations showing event clusters

---

### Query 2: High-Risk Event Detection

**Find high-severity events with source verification:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?date ?severity ?row ?confidence
WHERE {
    ?event feekg:severity "high" .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:severity ?severity .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:classificationConfidence ?confidence .
}
ORDER BY ?date
```

**Use Case**: Risk monitoring, audit trail for high-impact events

---

### Query 3: Entity Relationship Network

**Find all companies involved in legal issues:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?company ?event ?label ?date
WHERE {
    ?event feekg:eventType "legal_issue" .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:involves ?entity .
    ?entity rdfs:label ?company .
}
ORDER BY ?date
```

**Use Case**: Network analysis, identify interconnected entities

---

### Query 4: Classification Quality Audit

**Check classification accuracy by method:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?method
       (COUNT(?event) as ?count)
       (AVG(?confidence) as ?avgConfidence)
WHERE {
    ?event feekg:classificationMethod ?method .
    ?event feekg:classificationConfidence ?confidence .
}
GROUP BY ?method
ORDER BY DESC(?count)
```

**Results:**
- `pattern_match`: ~2,000 events, 95% confidence
- `capital_iq_mapping`: ~2,398 events, 75-85% confidence

**Use Case**: Quality assurance, identify events needing review

---

## 3. Source Traceability & Audit Trail

### Query 5: Verify Specific Event Source

**Trace event back to original CSV:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?row ?capitalIqId ?originalType ?mappedType ?confidence
WHERE {
    ?event feekg:eventId "evt_83730941" .
    ?event rdfs:label ?label .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:capitalIqId ?capitalIqId .
    ?event feekg:originalEventType ?originalType .
    ?event feekg:eventType ?mappedType .
    ?event feekg:classificationConfidence ?confidence .
}
```

**Result:**
```
label: "Virgin Islands Pension Fund Sues Morgan Stanley..."
row: 68940
capitalIqId: 83730941
originalType: "Lawsuits & Legal Issues"
mappedType: "legal_issue"
confidence: 0.95
```

**Use Case**: Verify chatbot answers, audit data quality

---

### Query 6: Find All Events from Specific CSV Rows

**Query events by CSV row range:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?row ?type
WHERE {
    ?event feekg:csvRowNumber ?row .
    ?event rdfs:label ?label .
    ?event feekg:eventType ?type .
    FILTER(?row >= 68900 && ?row <= 68950)
}
ORDER BY ?row
```

**Use Case**: Debug CSV import, spot-check data quality

---

## 4. Event Pattern & Risk Analysis

### Query 7: Event Co-occurrence Analysis

**Find events involving multiple entities:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?date (COUNT(DISTINCT ?entity) as ?entityCount)
WHERE {
    ?event feekg:involves ?entity .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
}
GROUP BY ?event ?label ?date
HAVING (COUNT(DISTINCT ?entity) >= 2)
ORDER BY DESC(?entityCount)
```

**Use Case**: Identify systemic events affecting multiple entities

---

### Query 8: Time-Based Event Clustering

**Find event spikes by month:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>

SELECT (SUBSTR(?date, 1, 7) as ?month)
       (COUNT(?event) as ?eventCount)
WHERE {
    ?event feekg:date ?date .
}
GROUP BY (SUBSTR(?date, 1, 7))
ORDER BY ?month
```

**Result Example:**
```
2007-01: 245 events
2008-09: 892 events (Lehman bankruptcy!)
2009-03: 634 events
```

**Use Case**: Crisis timeline visualization, event hotspot detection

---

## 5. Entity-Centric Analysis

### Query 9: Company Event Profile

**Get all events for a specific company:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?type ?date ?severity
WHERE {
    {
        ?event feekg:actor "Morgan Stanley" .
    } UNION {
        ?event feekg:involves ?entity .
        ?entity rdfs:label "Morgan Stanley" .
    }
    ?event rdfs:label ?label .
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
    OPTIONAL { ?event feekg:severity ?severity . }
}
ORDER BY ?date
```

**Use Case**: Company risk profile, due diligence

---

### Query 10: Entity Network Connections

**Find entities connected through events:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?entity1 ?entity2 ?event ?label
WHERE {
    ?event feekg:involves ?ent1 .
    ?event feekg:involves ?ent2 .
    ?event rdfs:label ?label .
    ?ent1 rdfs:label ?entity1 .
    ?ent2 rdfs:label ?entity2 .
    FILTER(?entity1 < ?entity2)
}
```

**Use Case**: Network graph visualization, contagion analysis

---

## 6. Data Quality & Validation

### Query 11: High-Confidence Classifications Only

**Filter by classification quality:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?type ?confidence ?method
WHERE {
    ?event feekg:classificationConfidence ?confidence .
    ?event rdfs:label ?label .
    ?event feekg:eventType ?type .
    ?event feekg:classificationMethod ?method .
    FILTER(?confidence >= 0.9)
}
ORDER BY DESC(?confidence)
LIMIT 100
```

**Use Case**: High-quality dataset for training, analysis

---

### Query 12: Original Type Mapping Analysis

**Compare original vs mapped types:**

```sparql
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?originalType ?mappedType (COUNT(?event) as ?count)
WHERE {
    ?event feekg:originalEventType ?originalType .
    ?event feekg:eventType ?mappedType .
}
GROUP BY ?originalType ?mappedType
ORDER BY DESC(?count)
```

**Use Case**: Validate type mappings, improve classification

---

## 7. Visualization Possibilities

### Graph Visualizations

**1. Entity Relationship Network**
- Nodes: Companies, banks, regulators
- Edges: Co-occurrence in events
- Color: Entity type
- Size: Event count

**2. Event Timeline**
- X-axis: Time (2007-2009)
- Y-axis: Event type
- Color: Severity
- Click: View CSV source

**3. Risk Heatmap**
- Rows: Companies
- Columns: Months
- Color: Event count/severity
- Hover: Event details + CSV row

**4. Classification Confidence Dashboard**
- Pie chart: Events by method
- Bar chart: Confidence distribution
- Table: Low-confidence events needing review

---

## 8. Integration with LLM Playground

### Setup AllegroGraph NLQ (Natural Language Queries)

```bash
# 1. Create vector database in AllegroGraph WebView
# 2. Navigate to: Natural Language (NL) to SPARQL
# 3. Click: CREATE NLQ VDB & SHACL SHAPES
# 4. Enter OpenAI API key
# 5. Wait ~2 minutes for vectorization
```

**Cost**: ~$0.20 one-time (vectorize 74K triples)

### Then Ask Natural Language Questions

```
Q: "Which banks had the most legal issues during 2008?"

→ AllegroGraph converts to SPARQL automatically
→ Runs query on FEEKG
→ Returns results with CSV sources
```

**Examples:**
- "Timeline of Morgan Stanley events in 2009"
- "All restructuring events with high severity"
- "Companies involved in credit downgrades"
- "Events classified with low confidence" (for QA review)

---

## 9. Python API Integration

### Example: Query Events with Source Metadata

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv()

base_url = os.getenv('AG_URL').rstrip('/')
catalog = os.getenv('AG_CATALOG')
repo = os.getenv('AG_REPO')
auth = (os.getenv('AG_USER'), os.getenv('AG_PASS'))

repo_url = f"{base_url}/catalogs/{catalog}/repositories/{repo}"

# Query: Get all legal issues with CSV sources
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?date ?row ?confidence
WHERE {
    ?event feekg:eventType "legal_issue" .
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:csvRowNumber ?row .
    ?event feekg:classificationConfidence ?confidence .
}
ORDER BY ?date
LIMIT 20
"""

response = requests.get(
    repo_url,
    params={'query': query},
    headers={'Accept': 'application/sparql-results+json'},
    auth=auth
)

results = response.json()

# Process results
for binding in results['results']['bindings']:
    print(f"Event: {binding['label']['value'][:60]}")
    print(f"  Date: {binding['date']['value']}")
    print(f"  CSV Row: {binding['row']['value']}")
    print(f"  Confidence: {binding['confidence']['value']}")
    print()
```

---

## 10. Advanced Use Cases

### A. Risk Propagation Simulation

```sparql
# Find events that could trigger cascading risks
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?event1 ?event2 ?sharedEntity ?timeDiff
WHERE {
    ?event1 feekg:involves ?sharedEntity .
    ?event2 feekg:involves ?sharedEntity .
    ?event1 feekg:date ?date1 .
    ?event2 feekg:date ?date2 .
    FILTER(?event1 != ?event2 && ?date2 > ?date1)
    BIND((?date2 - ?date1) as ?timeDiff)
}
ORDER BY ?timeDiff
```

**Use Case**: Contagion modeling, systemic risk analysis

---

### B. Event Classification Training Data

```sparql
# Export high-confidence events for ML training
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?type ?confidence ?method
WHERE {
    ?event rdfs:label ?label .
    ?event feekg:eventType ?type .
    ?event feekg:classificationConfidence ?confidence .
    ?event feekg:classificationMethod ?method .
    FILTER(?confidence >= 0.9)
}
```

**Use Case**: Create labeled dataset for NLP model training

---

### C. Audit Trail for Compliance

```sparql
# Generate audit report with full provenance
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?date ?type
       ?csvRow ?capitalIqId ?originalType ?confidence
WHERE {
    ?event rdfs:label ?label .
    ?event feekg:date ?date .
    ?event feekg:eventType ?type .
    ?event feekg:csvRowNumber ?csvRow .
    ?event feekg:capitalIqId ?capitalIqId .
    ?event feekg:originalEventType ?originalType .
    ?event feekg:classificationConfidence ?confidence .
    FILTER(?date >= "2008-09-01" && ?date <= "2008-09-30")
}
ORDER BY ?date
```

**Use Case**: Regulatory compliance, data lineage documentation

---

## Summary: What's Now Possible

| Capability | Status | Notes |
|-----------|--------|-------|
| Natural Language Q&A | ✅ Ready | $0.20 setup + $0.0005/query |
| SPARQL Queries | ✅ Ready | Unlimited, free |
| CSV Source Tracing | ✅ Ready | 100% traceability |
| Graph Visualization | ⚠️ Need frontend | Data ready |
| Risk Analysis | ✅ Ready | Complex queries possible |
| Audit Trails | ✅ Ready | Full provenance |
| ML Training Data | ✅ Ready | Export via SPARQL |
| Time Series Analysis | ✅ Ready | 2007-2009 coverage |

---

## Next Steps

### Immediate (< 1 day):
1. ✅ Set up AllegroGraph NLQ for natural language queries
2. ✅ Test chatbot with sample questions
3. ✅ Create basic query templates

### Short-term (1-3 days):
1. Build chatbot UI with CSV source viewer
2. Add graph visualizations (D3.js or Cytoscape.js)
3. Create dashboard showing:
   - Event timeline
   - Entity network
   - Classification quality metrics

### Medium-term (1 week):
1. Add more crisis periods (2000 dot-com, 2020 COVID)
2. Implement event evolution tracking
3. Add risk scoring algorithms
4. Build interactive demo for publication

---

## Cost Estimates

| Feature | One-time | Per Query |
|---------|----------|-----------|
| Vectorization | $0.20 | - |
| RAG Query | - | $0.0005 |
| SPARQL Query | Free | Free |
| Storage (74K triples) | $0 | $0 |

**Total for 1,000 queries**: ~$0.70 (incredibly cheap!)

---

## Access Points

**AllegroGraph WebView:**
https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG

**SPARQL Endpoint:**
https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG

**Current Data:**
- 74,012 triples
- 4,398 events
- 18 entities
- 100% CSV traceability
- 0% unknown events
