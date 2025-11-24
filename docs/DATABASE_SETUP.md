# Database Setup Guide

Complete guide to AllegroGraph RDF database setup and SPARQL usage.

---

## Quick Start

### Connection Details

```python
from franz.openrdf.connect import ag_connect

conn = ag_connect(
    'FEEKG',
    user='sadmin',
    host='https://qa-agraph.nelumbium.ai:443',
    password='your_password'
)
print(f"Connected! Triples: {conn.size()}")
conn.close()
```

### Environment Variables

```bash
# .env
AG_URL=https://qa-agraph.nelumbium.ai:443/
AG_USER=sadmin
AG_PASS=<password>
AG_CATALOG=mycatalog
AG_REPO=FEEKG
```

### Test Connection

```bash
./venv/bin/python scripts/check_feekg_mycatalog.py
```

---

## AllegroGraph Setup

### Requirements

```bash
./venv/bin/pip install agraph-python pycurl
```

### Key Configuration

- **Use HTTPS port 443** (firewall-friendly)
- **Use `ag_connect`** (not AllegroGraphServer)
- **Include explicit `:443`** in host URL

### Current Database Stats

- **Repository**: FEEKG
- **Triples**: 429,019
- **Events**: 5,105
- **Entities**: 22
- **Evolution Links**: 31,173

---

## SPARQL Usage

### Basic Queries

```sparql
# Get all events
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?label ?date ?type
WHERE {
    ?event a feekg:Event .
    ?event feekg:label ?label .
    ?event feekg:date ?date .
    ?event feekg:eventType ?type .
}
ORDER BY ?date
LIMIT 100
```

```sparql
# Get entities
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?entity ?label ?type
WHERE {
    ?entity a feekg:Entity .
    ?entity feekg:label ?label .
    ?entity feekg:entityType ?type .
}
```

```sparql
# Get evolution links
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?from ?to ?score
WHERE {
    ?from feekg:evolvesTo ?to .
    ?from feekg:evolutionScore ?score .
}
ORDER BY DESC(?score)
LIMIT 50
```

### Python Integration

```python
import requests
from requests.auth import HTTPBasicAuth

url = 'https://qa-agraph.nelumbium.ai/catalogs/mycatalog/repositories/FEEKG'
auth = HTTPBasicAuth('sadmin', 'password')

query = '''
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?label WHERE {
    ?event a feekg:Event .
    ?event feekg:label ?label .
} LIMIT 10
'''

response = requests.post(url,
    data={'query': query},
    headers={'Accept': 'application/sparql-results+json'},
    auth=auth
)
results = response.json()['results']['bindings']
```

### Using RDFBackend

```python
from shared.config.rdf_backend import RDFBackend

backend = RDFBackend()
backend.connect()

# Get stats
stats = backend.get_stats()
print(f"Total triples: {stats['total_triples']}")

# Query
results = backend.query_sparql('''
    SELECT * WHERE { ?s ?p ?o } LIMIT 5
''')

backend.close()
```

---

## RDF Triple Format

### Event Triple

```turtle
@prefix feekg: <http://feekg.org/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

feekg:evt_3410876 rdf:type feekg:Event .
feekg:evt_3410876 feekg:label "Lehman Brothers bankruptcy" .
feekg:evt_3410876 feekg:date "2008-09-15"^^xsd:date .
feekg:evt_3410876 feekg:eventType "bankruptcy" .
feekg:evt_3410876 feekg:hasActor feekg:entity_lehman .
```

### Evolution Link Triple

```turtle
feekg:evt_001 feekg:evolvesTo feekg:evt_002 .
feekg:evt_001 feekg:evolutionScore "0.85"^^xsd:float .
feekg:evt_001 feekg:temporalScore "0.82"^^xsd:float .
feekg:evt_001 feekg:semanticScore "0.53"^^xsd:float .
```

### CSV Traceability

```turtle
feekg:evt_001 feekg:csvRowNumber "15234"^^xsd:integer .
feekg:evt_001 feekg:csvFilename "capital_iq_download.csv" .
feekg:evt_001 feekg:capitalIqId "3410876" .
```

---

## Alternative Databases

### Apache Jena Fuseki (Local)

```bash
# Install
./scripts/setup_fuseki.sh

# Use
from config.fuseki_backend import FusekiBackend
fuseki = FusekiBackend()
fuseki.upload_turtle_file('results/feekg_graph.ttl')

# Web UI: http://localhost:3030
```

### RDFLib (In-Memory)

```python
from rdflib import Graph

g = Graph()
g.parse('results/feekg_graph.ttl', format='turtle')

results = g.query("""
    SELECT ?event ?type WHERE {
        ?event a feekg:Event .
        ?event feekg:eventType ?type .
    }
""")
```

---

## Troubleshooting

### Connection Timeout
- Ensure using HTTPS with explicit port 443
- Check: `host='https://qa-agraph.nelumbium.ai:443'`

### Permission Denied (401)
- Request admin to grant write access
- Use existing writable repository
- Use Fuseki or RDFLib alternatives

### Import Error: pycurl
```bash
./venv/bin/pip install pycurl
```

---

## Database Comparison

| Feature | AllegroGraph | Fuseki | RDFLib |
|---------|--------------|--------|--------|
| **Type** | Cloud | Local | In-Memory |
| **SPARQL** | Full | Full | Full |
| **Scale** | Enterprise | Medium | Small |
| **Cost** | Commercial | Free | Free |
| **Setup** | Medium | Easy | None |

---

**Last Updated:** November 2024
**Primary Database:** AllegroGraph @ qa-agraph.nelumbium.ai
