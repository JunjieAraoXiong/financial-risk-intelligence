# FEEKG Quick Analysis Guide

## What You Have in AllegroGraph

### Three-Layer Structure:
- **Layer 1 (Entities)**: 66 entities (banks, companies, people)
- **Layer 2 (Events)**: 9,852 financial events (2007-2009 crisis)
- **Layer 3 (Risks)**: 50 risk instances + 12 risk types

### Connections:
- ✅ Entity ↔ Event: `feekg:involves` (many connections)
- ✅ Event → Risk: `feekg:increasesRiskOf` (50 connections)
- ✅ Risk → RiskType: `feekg:hasRiskType` (50 connections)
- ❌ Event → Event (evolution): 0 (optional, can add later)
- ❌ Risk → Entity: 0 (needs to be created)

### Total: **86,583 RDF triples**

---

## Quick Analysis Commands

### 1. Statistics Overview
```bash
./venv/bin/python scripts/efficient_analyzer.py stats
```

### 2. Find All Entities
```bash
./venv/bin/python scripts/efficient_analyzer.py entities
```

### 3. Get Events for an Entity (e.g., "Lehman")
```bash
./venv/bin/python scripts/efficient_analyzer.py entity-events --entity "Lehman"
```

### 4. Get Events by Date Range
```bash
./venv/bin/python scripts/efficient_analyzer.py events-by-date \
    --start "2008-09-01" \
    --end "2008-09-30"
```

### 5. Get High-Severity Events
```bash
./venv/bin/python scripts/efficient_analyzer.py high-severity
```

### 6. Get Crisis Timeline
```bash
./venv/bin/python scripts/efficient_analyzer.py crisis-events \
    --start "2008-01-01" \
    --end "2008-12-31"
```

### 7. Get Events by Type
```bash
./venv/bin/python scripts/efficient_analyzer.py events-by-type --type "bankruptcy"
```

### 8. Export to JSON
```bash
./venv/bin/python scripts/efficient_analyzer.py crisis-events \
    --export crisis_2008.json
```

---

## Direct SPARQL Queries

### Via Python:
```python
from scripts.efficient_analyzer import FEEKGAnalyzer

analyzer = FEEKGAnalyzer()

# Get entities
entities = analyzer.get_all_entities()

# Get timeline for an entity
timeline = analyzer.get_event_timeline("Lehman")

# Custom query
results = analyzer.query("""
    PREFIX feekg: <http://feekg.org/ontology#>
    SELECT ?event ?date ?label
    WHERE {
        ?event a feekg:Event .
        ?event feekg:severity "critical" .
        ?event feekg:date ?date .
        ?event rdfs:label ?label .
    }
    ORDER BY ?date
""")

analyzer.display_results(results)
```

### Via AllegroGraph Web Interface:
1. Go to: https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG
2. Click "Query"
3. Paste SPARQL and execute

---

## Example SPARQL Queries

### Get All Risk Types
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?riskType ?label ?description
WHERE {
    ?riskType a feekg:RiskType .
    ?riskType rdfs:label ?label .
    OPTIONAL { ?riskType rdfs:comment ?description . }
}
```

### Get Events that Triggered Risks
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?eventLabel ?risk ?riskType ?severity
WHERE {
    ?event feekg:increasesRiskOf ?risk .
    ?event rdfs:label ?eventLabel .
    ?risk feekg:hasRiskType ?riskType .
    ?risk feekg:hasSeverity ?severity .
}
ORDER BY ?severity
```

### Get Entity Event Timeline
```sparql
PREFIX feekg: <http://feekg.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?date ?eventType ?severity ?label
WHERE {
    ?entity rdfs:label "Lehman Brothers" .
    ?event feekg:involves ?entity .
    ?event feekg:date ?date .
    ?event feekg:eventType ?eventType .
    ?event rdfs:label ?label .
    OPTIONAL { ?event feekg:severity ?severity . }
}
ORDER BY ?date
```

### Count Events by Risk Type
```sparql
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?riskType (COUNT(?event) as ?eventCount)
WHERE {
    ?event feekg:increasesRiskOf ?risk .
    ?risk feekg:hasRiskType ?riskType .
}
GROUP BY ?riskType
ORDER BY DESC(?eventCount)
```

---

## Data Structure

### Namespaces:
- `feekg:` = http://feekg.org/ontology#
- `rdfs:` = http://www.w3.org/2000/01/rdf-schema#
- `xsd:` = http://www.w3.org/2001/XMLSchema#

### Key Classes:
- `feekg:Entity` - Companies, banks, people
- `feekg:Event` - Financial events
- `feekg:Risk` - Risk instances
- `feekg:RiskType` - Risk categories

### Key Properties:
- `feekg:involves` - Event → Entity
- `feekg:increasesRiskOf` - Event → Risk
- `feekg:hasRiskType` - Risk → RiskType
- `feekg:hasSeverity` - Risk severity level
- `feekg:eventType` - Type of event
- `feekg:date` - Event date

---

## Next Steps

### Complete the Graph:
1. **Add more risks** (currently only 50 out of 1,464 high-severity events):
   ```bash
   # Modify scripts/complete_three_layer_graph.py to fix Turtle syntax
   # Then run again to add more risks
   ```

2. **Add Risk→Entity connections**:
   ```bash
   # Connect risks to the entities they affect
   ```

3. **Add evolution links** (Event → Event):
   ```bash
   # Add selective evolution links for related events
   ```

### Analysis:
1. **Time series analysis**: Event frequency over time
2. **Risk propagation**: How risks spread across entities
3. **Crisis detection**: Identify crisis periods
4. **Entity impact**: Which entities are most affected

### Visualization:
1. Timeline charts
2. Network graphs (Entity-Event-Risk)
3. Heat maps (event density over time)
4. Risk distribution charts

---

## Efficient Analysis Tips

### 1. Use Filters to Reduce Results:
- Filter by date range for temporal analysis
- Filter by severity for critical events only
- Filter by entity for focused analysis

### 2. Use Batch Queries:
- Query multiple entities in one SPARQL query
- Use UNION for combining results

### 3. Export and Process Externally:
- Export to JSON for Python/Pandas analysis
- Export to CSV for Excel/visualization tools

### 4. Index Common Patterns:
- AllegroGraph automatically indexes frequently queried patterns
- Repeated queries will get faster over time

---

## Connection Details

### Repository Info:
- **URL**: https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG
- **Catalog**: mycatalog
- **Repository**: FEEKG
- **Triple Count**: 86,583

### Access:
- Via Python scripts (recommended)
- Via AllegroGraph web interface
- Via direct HTTP API calls

---

## Troubleshooting

### Query Timeout:
- Add LIMIT clause to queries
- Filter results before counting

### No Results:
- Check namespace prefixes
- Verify entity/event names (case-sensitive)
- Check date format (YYYY-MM-DD)

### Performance:
- Use selective queries
- Add filters early in WHERE clause
- Limit result size

---

Last Updated: 2025-11-15
