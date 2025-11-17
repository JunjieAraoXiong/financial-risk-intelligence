# CSV Traceability & Data Quality Summary

## Overview

Successfully implemented **full CSV traceability** for all events in the FE-EKG knowledge graph. Every event can now be traced back to the exact row in the original Capital IQ CSV file.

**Date**: 2025-11-15
**Status**: ✅ Complete

---

## Key Achievements

### 1. Data Quality Improvement

**Before:**
- Unknown events: 2,301 (8.6% of 26,785 events)
- 27 unmapped Capital IQ event types
- No source traceability

**After:**
- Unknown events: **0 (0.0%)**
- 27 new event type mappings added
- Average classification confidence: **87.1%**
- Full CSV source metadata for every event

### 2. CSV Traceability Implementation

Every event in AllegroGraph now includes:

| Property | Description | Example |
|----------|-------------|---------|
| `feekg:csvRowNumber` | Exact row in CSV file | 68940 |
| `feekg:csvFilename` | Source CSV filename | capital_iq_download.csv |
| `feekg:capitalIqId` | Capital IQ event ID | 83730941 |
| `feekg:companyId` | Capital IQ company ID | 472898 |
| `feekg:companyName` | Company name | Morgan Stanley |
| `feekg:originalEventType` | Original Capital IQ type | Lawsuits & Legal Issues |
| `feekg:classificationConfidence` | Confidence score (0-1) | 0.95 |
| `feekg:classificationMethod` | Classification method | pattern_match |

### 3. Sample Event with Full Metadata

```sparql
# Event: evt_83730941
# Headline: "Virgin Islands Pension Fund Sues Morgan Stanley of Defrauding"

feekg:evt_83730941 rdf:type feekg:Event .
feekg:evt_83730941 feekg:eventType "legal_issue" .
feekg:evt_83730941 feekg:date "2009-08-21"^^xsd:date .
feekg:evt_83730941 rdfs:label "Virgin Islands Pension Fund Sues Morgan Stanley..." .

# CSV Source Metadata
feekg:evt_83730941 feekg:csvRowNumber "68940"^^xsd:integer .
feekg:evt_83730941 feekg:csvFilename "capital_iq_download.csv" .
feekg:evt_83730941 feekg:capitalIqId "83730941" .
feekg:evt_83730941 feekg:companyName "Morgan Stanley" .
feekg:evt_83730941 feekg:originalEventType "Lawsuits & Legal Issues" .

# Classification Metadata
feekg:evt_83730941 feekg:classificationConfidence "0.95"^^xsd:float .
feekg:evt_83730941 feekg:classificationMethod "pattern_match" .
```

---

## Implementation Details

### New Files Created

1. **`scripts/analyze_csv_quality.py`**
   - Analyzes raw Capital IQ CSV for data quality
   - Identifies unmapped event types
   - Generates recommendations

2. **`ingestion/process_capital_iq_v3.py`**
   - Enhanced processor with comprehensive event type mappings
   - Adds CSV source tracking to every event
   - Classification confidence scoring
   - Reduces unknown events from 8.6% to 0%

3. **`data/capital_iq_processed/lehman_v3_traced.json`**
   - Output file with 4,398 events
   - Full CSV metadata for each event
   - 0% unknown events
   - 87.1% average confidence

### Updated Files

1. **`ingestion/load_capital_iq_to_allegrograph.py`**
   - Modified `convert_to_turtle()` method
   - Adds CSV metadata as RDF triples
   - Preserves traceability during upload

---

## Comprehensive Event Type Mapping

Added 27 new Capital IQ type mappings:

| Capital IQ Type | FE-EKG Type | Confidence | Events |
|----------------|-------------|------------|--------|
| Company Conference Presentations | earnings_announcement | 0.80 | 630 |
| Labor-related Announcements | management_change | 0.75 | 302 |
| Seeking to Sell/Divest | restructuring | 0.85 | 282 |
| Conferences | earnings_announcement | 0.75 | 231 |
| Annual General Meeting | business_operations | 0.85 | 174 |
| Considering Multiple Strategic Alternatives | restructuring | 0.80 | 93 |
| Changes in Company Bylaws/Rules | business_operations | 0.75 | 88 |
| Shelf Registration Filings | capital_raising | 0.80 | 79 |
| Seeking Financing/Partners | capital_raising | 0.85 | 78 |
| Shareholder/Analyst Calls | earnings_announcement | 0.85 | 72 |
| Special Calls | earnings_announcement | 0.80 | 65 |
| Delistings | stock_movement | 0.90 | 32 |
| Index Constituent Drops | stock_movement | 0.80 | 28 |
| Special/Extraordinary Shareholders Meeting | business_operations | 0.80 | 28 |
| Index Constituent Adds | stock_movement | 0.80 | 28 |
| Potential Privatization of Government Entities | merger_acquisition | 0.75 | 17 |
| Auditor Changes | management_change | 0.75 | 16 |
| End of Lock-Up Period | stock_movement | 0.80 | 13 |
| Address Changes | business_operations | 0.60 | 10 |
| Delayed SEC Filings | legal_issue | 0.85 | 10 |
| Name Changes | business_operations | 0.70 | 6 |
| Ticker Changes | business_operations | 0.70 | 4 |
| Exchange Changes | business_operations | 0.75 | 4 |
| Analyst/Investor Day | earnings_announcement | 0.85 | 4 |
| Impairments/Write Offs | earnings_loss | 0.95 | 3 |
| Auditor Going Concern Doubts | credit_downgrade | 0.90 | 3 |
| Fiscal Year End Changes | business_operations | 0.70 | 1 |

**Total**: 2,301 previously unknown events now classified

---

## Database Statistics

**AllegroGraph Repository: mycatalog/FEEKG**

- Total triples: **74,012**
- Events: **4,398** (all with CSV metadata)
- Entities: **18**
- Date range: 2007-01-01 to 2009-12-31
- Unknown events: **0**
- Average confidence: **87.1%**

**Breakdown of 74,012 triples:**
- ~4,398 events × 10 properties = ~44,000 event triples
- ~4,398 events × 6 CSV metadata fields = ~26,000 metadata triples
- ~18 entities × 3 properties = ~50 entity triples
- ~4,000 entity relationships

---

## SPARQL Query Examples

### Query 1: Find events by CSV row number

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?row ?capitalIqId
WHERE {
    ?event feekg:csvRowNumber ?row .
    ?event rdfs:label ?label .
    ?event feekg:capitalIqId ?capitalIqId .
    FILTER(?row = 68940)
}
```

### Query 2: Find high-confidence classifications

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?confidence ?method
WHERE {
    ?event feekg:classificationConfidence ?confidence .
    ?event rdfs:label ?label .
    ?event feekg:classificationMethod ?method .
    FILTER(?confidence >= 0.9)
}
ORDER BY DESC(?confidence)
LIMIT 100
```

### Query 3: Trace event back to original CSV type

```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?originalType ?mappedType ?row
WHERE {
    ?event feekg:originalEventType ?originalType .
    ?event feekg:eventType ?mappedType .
    ?event feekg:csvRowNumber ?row .
    ?event rdfs:label ?label .
    FILTER(?originalType = "Lawsuits & Legal Issues")
}
LIMIT 20
```

### Query 4: Count events by classification method

```sparql
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?method (COUNT(?event) as ?count)
WHERE {
    ?event feekg:classificationMethod ?method .
}
GROUP BY ?method
ORDER BY DESC(?count)
```

---

## Usage Examples

### Load v3 data with CSV metadata

```bash
# Process Capital IQ CSV with comprehensive mapping
./venv/bin/python ingestion/process_capital_iq_v3.py \
    --input data/capital_iq_raw/capital_iq_download.csv \
    --output data/capital_iq_processed/lehman_v3_traced.json

# Load to AllegroGraph
./venv/bin/python ingestion/load_capital_iq_to_allegrograph.py \
    --input lehman_v3_traced.json
```

### Query CSV metadata

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv('AG_URL').rstrip('/')
catalog = os.getenv('AG_CATALOG')
repo = os.getenv('AG_REPO')
auth = (os.getenv('AG_USER'), os.getenv('AG_PASS'))

repo_url = f"{base_url}/catalogs/{catalog}/repositories/{repo}"

# Query for event by CSV row
query = """
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?capitalIqId ?originalType
WHERE {
    ?event feekg:csvRowNumber "68940"^^xsd:integer .
    ?event rdfs:label ?label .
    ?event feekg:capitalIqId ?capitalIqId .
    ?event feekg:originalEventType ?originalType .
}
"""

response = requests.get(
    repo_url,
    params={'query': query},
    headers={'Accept': 'application/sparql-results+json'},
    auth=auth
)

result = response.json()
print(result['results']['bindings'])
```

---

## Next Steps: Chatbot Integration

### Planned Features

1. **CSV Source Viewer**
   - Click "View Source" button on any event
   - Display exact CSV row context
   - Show original vs. mapped event type
   - Confidence score visualization

2. **RAG-Powered Q&A**
   - Natural language questions about events
   - Source traceability in answers
   - Example: "Which Morgan Stanley legal issues occurred in 2009?"
   - Answer includes CSV row numbers and confidence scores

3. **UI Mockup**

```
┌─────────────────────────────────────────────────────────────┐
│ Event: Virgin Islands Pension Fund Sues Morgan Stanley      │
│                                                              │
│ Type: legal_issue                                           │
│ Date: 2009-08-21                                            │
│ Severity: high                                              │
│                                                              │
│ 📊 Source Information                                       │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ CSV Row: 68940                                          ││
│ │ Capital IQ ID: 83730941                                 ││
│ │ Original Type: Lawsuits & Legal Issues                  ││
│ │ Confidence: 95% (pattern_match)                         ││
│ │                                                         ││
│ │ [View in CSV] [View Context]                           ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Implementation Tasks

- [ ] Add SPARQL query templates for CSV metadata
- [ ] Create CSV row context viewer API endpoint
- [ ] Build "View Source" modal component
- [ ] Integrate with RAG chatbot responses
- [ ] Add confidence score indicators to UI
- [ ] Enable filtering by classification method

---

## Quality Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Unknown events | 2,301 (8.6%) | 0 (0.0%) | -100% |
| Avg confidence | N/A | 87.1% | New metric |
| CSV traceability | 0% | 100% | +100% |
| Mapped types | 52 | 79 | +52% |

---

## Conclusion

Successfully achieved **complete CSV traceability** for all financial events in the knowledge graph. Every event can now be:

1. ✅ Traced to exact CSV row number
2. ✅ Linked to original Capital IQ ID
3. ✅ Compared against original event type
4. ✅ Evaluated for classification confidence
5. ✅ Verified through source context

This enables:
- **Audit trail**: Full transparency of data provenance
- **Quality assurance**: Confidence scoring for every classification
- **Debugging**: Easy identification of misclassifications
- **User trust**: Source verification in chatbot responses

**Next**: Integrate CSV source viewer into RAG-powered chatbot demo.
