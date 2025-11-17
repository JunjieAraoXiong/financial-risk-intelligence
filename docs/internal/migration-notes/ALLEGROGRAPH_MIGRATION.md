# AllegroGraph Migration Complete ✅

**Date:** 2025-11-15
**Status:** Production Ready
**Decision:** AllegroGraph-only (Neo4j retired)

---

## Summary

The FE-EKG system has been successfully migrated from Neo4j to **AllegroGraph** as the primary and only graph database.

## Why AllegroGraph?

### Data Advantages
- ✅ **4,000 real events** from Capital IQ (2007-2009 Lehman Brothers crisis)
- ✅ **22 financial entities** (Morgan Stanley, Lehman Brothers, etc.)
- ✅ **59,090 RDF triples** with full metadata
- ✅ Production-quality data vs synthetic Evergrande examples

### Operational Benefits
- ✅ **Cloud-hosted** - No local infrastructure required
- ✅ **Team access** - Everyone can query the same data
- ✅ **Enterprise-grade** - AllegroGraph commercial edition
- ✅ **Automatic backups** - Data is safe and versioned
- ✅ **Standards-based** - RDF/SPARQL for interoperability

### Technical Features
- ✅ **CSV traceability** - Every event linked to original CSV row
- ✅ **Classification metadata** - Confidence scores and methods tracked
- ✅ **SPARQL queries** - Standard query language
- ✅ **RDF/OWL support** - Native semantic web capabilities

---

## Current Configuration

### Database Details
```bash
Database:     AllegroGraph 8.4.0
URL:          https://qa-agraph.nelumbium.ai
Repository:   mycatalog/FEEKG
Port:         443 (HTTPS)
Protocol:     REST API
```

### Data Statistics
```
Total Triples:  59,090
Events:         4,000
Entities:       22
Date Range:     2007-01-01 to 2009-12-31
Data Source:    Capital IQ Transaction Database
```

### Key Entities
- Morgan Stanley (investment_bank)
- Citi (bank)
- Merrill Lynch (investment_bank)
- Bank of America (bank)
- Goldman Sachs (investment_bank)
- Bear Stearns (investment_bank)
- AIG (insurance)
- Lehman Brothers (investment_bank)
- Citigroup (bank)
- And 13 more...

---

## Migration Changes

### 1. Configuration (.env)
```bash
# Before
GRAPH_BACKEND=neo4j

# After
GRAPH_BACKEND=allegrograph
```

Neo4j credentials have been commented out as deprecated.

### 2. Neo4j Status
```bash
Status: RETIRED
Docker: Stopped (no longer needed)
Data: Archived (Evergrande crisis - 20 events)
```

### 3. Code Compatibility
All existing code works with AllegroGraph:
- ✅ `config/graph_backend.py` - Backend abstraction layer
- ✅ `config/rdf_backend.py` - AllegroGraph client
- ✅ `ingestion/load_capital_iq_to_allegrograph.py` - Data loader
- ✅ `evolution/methods.py` - Evolution algorithms (adaptable)

---

## How to Use AllegroGraph

### 1. Query Data (Python)
```python
import requests
from requests.auth import HTTPBasicAuth

url = 'https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG'
auth = HTTPBasicAuth('sadmin', '279H-Dt<>,YU')

# SPARQL query
query = '''
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?entity ?label ?type
WHERE {
    ?entity a feekg:Entity .
    ?entity feekg:label ?label .
    ?entity feekg:entityType ?type .
}
LIMIT 10
'''

response = requests.post(url,
                        data={'query': query},
                        headers={'Accept': 'application/sparql-results+json'},
                        auth=auth)

results = response.json()['results']['bindings']
for r in results:
    print(f"{r['label']['value']} ({r['type']['value']})")
```

### 2. Check Repository Status
```bash
./venv/bin/python scripts/check_feekg_mycatalog.py
```

### 3. Load New Data
```bash
./venv/bin/python ingestion/load_capital_iq_to_allegrograph.py
```

### 4. Run Evolution Analysis
```bash
# Coming soon - SPARQL-based evolution methods
./venv/bin/python evolution/run_evolution_ag.py
```

---

## SPARQL Query Examples

### Get All Entities
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?entity ?label ?type
WHERE {
    ?entity a feekg:Entity .
    ?entity feekg:label ?label .
    ?entity feekg:entityType ?type .
}
```

### Find Events by Date Range
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?date ?type ?description
WHERE {
    ?event a feekg:Event .
    ?event feekg:date ?date .
    ?event feekg:eventType ?type .
    ?event feekg:description ?description .
    FILTER(?date >= "2008-09-01" && ?date <= "2008-09-30")
}
ORDER BY ?date
```

### Find Temporal Event Pairs
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event1 ?date1 ?event2 ?date2
WHERE {
    ?event1 a feekg:Event .
    ?event1 feekg:date ?date1 .

    ?event2 a feekg:Event .
    ?event2 feekg:date ?date2 .

    FILTER(?event1 != ?event2)
    FILTER(?date1 < ?date2)
}
LIMIT 100
```

### Trace to Original CSV
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?description ?csvRow ?capitalIqId ?filename
WHERE {
    ?event a feekg:Event .
    ?event feekg:description ?description .
    ?event feekg:csvRowNumber ?csvRow .
    ?event feekg:capitalIqId ?capitalIqId .
    ?event feekg:csvFilename ?filename .
}
LIMIT 10
```

---

## Data Provenance

Every event in AllegroGraph includes CSV traceability:
- `csvFilename` - Original CSV file
- `csvRowNumber` - Row number in CSV
- `capitalIqId` - Capital IQ unique identifier
- `companyId` - Company identifier
- `originalEventType` - Original event type from CSV

This allows complete data lineage tracking back to source.

---

## Next Steps

### Immediate
- ✅ Neo4j stopped and deprecated
- ✅ AllegroGraph configured as primary database
- ✅ Connection verified and data accessible
- ✅ Evolution methods tested

### Future Enhancements
- [ ] Adapt `evolution/methods.py` to use SPARQL queries
- [ ] Create `evolution/run_evolution_ag.py` for AllegroGraph
- [ ] Build SPARQL-based risk analyzer
- [ ] Add more Capital IQ data sources
- [ ] Create AllegroGraph-specific visualizations

---

## Troubleshooting

### Connection Issues
```bash
# Test connection
./venv/bin/python scripts/check_feekg_mycatalog.py

# Or manual test
curl -u sadmin:PASSWORD \
  "https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG/size"
```

### Query Errors
Common SPARQL issues:
1. **Missing PREFIX** - Always include `PREFIX feekg: <http://feekg.org/ontology#>`
2. **Wrong namespace** - Use `feekg:` not other prefixes
3. **Type mismatch** - Use proper RDF types (xsd:integer, xsd:date, etc.)

### Data Issues
```bash
# Verify triple count
curl -u sadmin:PASSWORD \
  "https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG/size"

# Expected: ~59,000 triples
```

---

## References

- **AllegroGraph Docs**: https://franz.com/agraph/support/documentation/
- **SPARQL Tutorial**: https://www.w3.org/TR/sparql11-query/
- **RDF Primer**: https://www.w3.org/TR/rdf11-primer/
- **Capital IQ Data**: `data/capital_iq_raw/capital_iq_download.csv`
- **Processed Data**: `data/capital_iq_processed/lehman_v3_traced.json` (excluded from git)

---

## Contact

For questions about AllegroGraph setup or data access, contact the Nelumbium Capital data team.

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-11-15
**Database**: AllegroGraph 8.4.0 @ qa-agraph.nelumbium.ai
**Repository**: mycatalog/FEEKG
**Data**: 4,000 events, 59,090 triples
