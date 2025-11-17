# RDF and Ontology Setup

Complete guide to RDF conversion, triple stores, and ontology management.

---

# Converting FE-EKG to RDF

You have **4 options** to use RDF with FE-EKG:

## Option 1: AllegroGraph RDF Backend (Recommended)

Use your existing AllegroGraph credentials to store data as RDF triples.

### Setup

Your `.env` already has AllegroGraph credentials:
```bash
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_REPO=feekg_dev
```

### Convert Your Data

```bash
# Interactive menu
./venv/bin/python scripts/convert_to_rdf.py

# Options:
# 1. Convert from Neo4j to RDF (migrate existing data)
# 2. Convert from JSON to RDF (fresh start)
# 3. Export to Turtle file (.ttl)
# 4. Test SPARQL queries
```

### Use RDF Backend in Code

```python
from config.rdf_backend import RDFBackend

# Connect
rdf = RDFBackend()
rdf.connect()

# Add event as RDF triple
event = {
    'eventId': 'evt_001',
    'type': 'debt_default',
    'date': '2021-12-01',
    'description': 'Evergrande defaulted on bonds'
}
rdf.create_event_triple(event)

# Query with SPARQL
query = """
PREFIX feekg: <http://feekg.org/ontology#>

SELECT ?event ?type ?date
WHERE {
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
    ?event feekg:date ?date .
}
ORDER BY ?date
"""
results = rdf.query_sparql(query)

# Export to file
rdf.export_to_turtle('results/feekg_graph.ttl')

rdf.close()
```

### RDF Triple Format

Your data becomes:

```turtle
@prefix feekg: <http://feekg.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Event
feekg:evt_001 rdf:type feekg:Event .
feekg:evt_001 feekg:eventType "debt_default" .
feekg:evt_001 feekg:date "2021-12-01"^^xsd:date .
feekg:evt_001 feekg:description "Evergrande defaulted on bonds" .

# Entity
feekg:ent_evergrande rdf:type feekg:Entity .
feekg:ent_evergrande feekg:name "China Evergrande Group" .
feekg:ent_evergrande feekg:entityType "company" .

# Evolution relationship (reified)
feekg:evt_001_to_evt_002 rdf:type feekg:EvolutionLink .
feekg:evt_001_to_evt_002 feekg:fromEvent feekg:evt_001 .
feekg:evt_001_to_evt_002 feekg:toEvent feekg:evt_002 .
feekg:evt_001_to_evt_002 feekg:score "0.85"^^xsd:float .
```

---

## Option 2: Neo4j + Neosemantics (n10s)

Keep using Neo4j but add RDF support with the `n10s` plugin.

### Install n10s Plugin

```bash
# 1. Download n10s plugin
# https://github.com/neo4j-labs/neosemantics/releases

# 2. Copy to Neo4j plugins folder
docker cp neosemantics-4.4.0.0.jar feekg-neo4j:/plugins/

# 3. Restart Neo4j
docker restart feekg-neo4j

# 4. Enable in Neo4j Browser
CALL n10s.graphconfig.init();
```

### Export Neo4j to RDF

```cypher
// Export entire graph to Turtle
CALL n10s.rdf.export.cypher(
  'MATCH (n) RETURN n',
  {format: 'Turtle'}
)
```

### Import RDF into Neo4j

```cypher
// Import from Turtle file
CALL n10s.rdf.import.fetch(
  'file:///path/to/feekg_graph.ttl',
  'Turtle'
)
```

**Pros**: Keep Neo4j, get RDF for free
**Cons**: Requires plugin installation, mapping config

---

## Option 3: RDFLib (Python Library)

Generate RDF triples using Python's `rdflib` library.

### Install

```bash
./venv/bin/pip install rdflib
```

### Example Code

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

# Create graph
g = Graph()
FEEKG = Namespace("http://feekg.org/ontology#")
g.bind("feekg", FEEKG)

# Add event
event_uri = FEEKG['evt_001']
g.add((event_uri, RDF.type, FEEKG.Event))
g.add((event_uri, FEEKG.eventType, Literal("debt_default")))
g.add((event_uri, FEEKG.date, Literal("2021-12-01", datatype=XSD.date)))

# Save to file
g.serialize(destination='results/feekg_graph.ttl', format='turtle')

# Query with SPARQL
query = """
SELECT ?event ?type
WHERE {
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
}
"""
results = g.query(query)
for row in results:
    print(f"{row.event} -> {row.type}")
```

**Pros**: Pure Python, no external database
**Cons**: In-memory only, no scalability

---

## Option 4: Dual Backend (Neo4j + AllegroGraph)

Run both Neo4j and AllegroGraph simultaneously.

### Architecture

```
FE-EKG
   ├── Neo4j (primary)        ← Fast queries, visualizations
   └── AllegroGraph (RDF)     ← SPARQL, semantic web integration
```

### Code Example

```python
from config.graph_backend import Neo4jBackend
from config.rdf_backend import RDFBackend

# Dual write
neo4j = Neo4jBackend()
rdf = RDFBackend()
rdf.connect()

def add_event(event):
    # Write to both backends
    neo4j.create_event(event)
    rdf.create_event_triple(event)

# Query from either backend
# Fast queries: Neo4j
results = neo4j.execute_query("MATCH (e:Event) RETURN e LIMIT 10")

# Semantic queries: AllegroGraph
results = rdf.query_sparql("SELECT ?event WHERE { ?event a feekg:Event }")
```

**Pros**: Best of both worlds
**Cons**: Data sync complexity

---

## Comparison Table

| Feature | AllegroGraph | Neo4j + n10s | RDFLib | Dual Backend |
|---------|--------------|--------------|--------|--------------|
| **RDF Native** | ✅ Yes | 🟡 Via plugin | ✅ Yes | ✅ Yes |
| **SPARQL** | ✅ Full support | ✅ Via n10s | ✅ Yes | ✅ Yes |
| **Scalability** | ✅ Enterprise | ✅ High | ❌ In-memory | ✅ High |
| **Setup Complexity** | 🟡 Medium | 🟡 Plugin install | ✅ Easy | 🔴 Complex |
| **Your Credentials** | ✅ Already have | ❌ Need setup | ✅ Built-in | 🟡 Both |
| **Cost** | 💰 Commercial | 💰 Enterprise | 🆓 Free | 💰💰 Both |

---

## Recommendation

**For your project, I recommend Option 1: AllegroGraph** because:

1. ✅ You already have credentials in `.env`
2. ✅ RDF-native (no conversion needed)
3. ✅ Full SPARQL support
4. ✅ I already built the backend (`config/rdf_backend.py`)
5. ✅ Easy migration with `scripts/convert_to_rdf.py`

**Quick Start**:

```bash
# 1. Convert your data
./venv/bin/python scripts/convert_to_rdf.py
# Choose option 2: Convert from JSON to RDF

# 2. Test SPARQL queries
./venv/bin/python scripts/convert_to_rdf.py
# Choose option 4: Test SPARQL queries

# 3. Export to Turtle
./venv/bin/python scripts/convert_to_rdf.py
# Choose option 3: Export to .ttl file
```

---

## Why RDF?

**RDF (Resource Description Framework)** is better than property graphs for:

### 1. Semantic Web Integration
```sparql
# RDF: Can federate with other knowledge graphs
SELECT ?event ?related
WHERE {
    ?event a feekg:Event .

    # Query external SPARQL endpoint
    SERVICE <http://dbpedia.org/sparql> {
        ?related dbo:company ?event .
    }
}
```

### 2. Schema Flexibility
```turtle
# RDF: Can add properties without schema migration
feekg:evt_001 feekg:newProperty "value" .  # Just add it!
```

### 3. Standards Compliance
- W3C standards (RDF, SPARQL, OWL)
- Interoperability with other systems
- Reuse existing ontologies (Dublin Core, FOAF, etc.)

### 4. Reasoning
```sparql
# OWL reasoning: Infer new facts
feekg:LiquidityRisk rdfs:subClassOf feekg:FinancialRisk .
# Reasoner automatically knows all liquidity risks are financial risks
```

---

## Files Created

```
feekg/
├── config/
│   └── rdf_backend.py           # AllegroGraph RDF backend
│
├── scripts/
│   └── convert_to_rdf.py        # Conversion tool
│
└── RDF_CONVERSION_GUIDE.md      # This file
```

---

## Next Steps

1. **Try the conversion**:
   ```bash
   ./venv/bin/python scripts/convert_to_rdf.py
   ```

2. **Learn SPARQL**:
   - Similar to SQL but for triples
   - W3C tutorial: https://www.w3.org/TR/sparql11-query/

3. **Integrate with API**:
   - Add SPARQL endpoint to `api/app.py`
   - Query RDF from web demo

4. **Explore semantic reasoning**:
   - Define ontology with OWL
   - Use reasoners to infer new knowledge

---

## Troubleshooting

**Problem**: AllegroGraph connection fails

```bash
# Check if AllegroGraph is accessible
curl https://qa-agraph.nelumbium.ai:10035

# Verify credentials in .env
cat .env | grep AG_
```

**Problem**: Port 10035 blocked

```bash
# AllegroGraph uses port 10035
# Check firewall/VPN settings
```

**Problem**: Want to use both Neo4j and RDF

```python
# Use dual backend approach
from config.graph_backend import Neo4jBackend
from config.rdf_backend import RDFBackend

# Both work simultaneously
```

---

**Status**: RDF backend ready to use! 🎉


---
## RDF Database Options

# RDF Database Options for FE-EKG

Complete guide to RDF triplestores beyond AllegroGraph.

## Quick Comparison Table

| Database | Type | Cost | Ease of Setup | SPARQL | Performance | Best For |
|----------|------|------|---------------|--------|-------------|----------|
| **Apache Jena Fuseki** | Server | 🆓 Free | ⭐⭐⭐⭐⭐ Easy | Full | Medium | **Development & Production** |
| **RDFLib** | Library | 🆓 Free | ⭐⭐⭐⭐⭐ Easy | Full | Low | **Small datasets, Prototyping** |
| **Virtuoso** | Server | 🆓 Free / 💰 Commercial | ⭐⭐⭐ Medium | Full | High | **Large-scale production** |
| **GraphDB** | Server | 🆓 Free / 💰 Commercial | ⭐⭐⭐⭐ Easy | Full | High | **Enterprise, Reasoning** |
| **Blazegraph** | Server | 🆓 Free | ⭐⭐⭐⭐ Easy | Full | High | **Graph analytics** |
| **Stardog** | Server | 💰 Commercial | ⭐⭐⭐ Medium | Full | High | **Enterprise, Security** |
| **Amazon Neptune** | Cloud | 💰 Pay-as-you-go | ⭐⭐⭐ Medium | Full | High | **AWS ecosystem** |
| **AllegroGraph** | Server | 💰 Commercial | ⭐⭐ Hard | Full | High | **Enterprise (if accessible)** |

---

## 1. Apache Jena Fuseki ⭐ **RECOMMENDED**

### Why Choose It?
- ✅ **Free and open source** (Apache License 2.0)
- ✅ **Easy to install** - Single download, runs anywhere with Java
- ✅ **Full SPARQL 1.1** support
- ✅ **Web UI** included for testing queries
- ✅ **Persistent storage** (TDB2 backend)
- ✅ **Active development** by Apache Foundation
- ✅ **Perfect for your project** - Great for research & production

### Installation

```bash
# Option 1: Using our script (automated)
chmod +x scripts/setup_fuseki.sh
./scripts/setup_fuseki.sh

# Option 2: Manual installation
# 1. Download from https://jena.apache.org/download/
# 2. Extract and run:
./fuseki-server --update --mem /feekg

# Option 3: Docker
docker run -p 3030:3030 stain/jena-fuseki
```

### Usage with FE-EKG

```python
from config.fuseki_backend import FusekiBackend

# Connect
fuseki = FusekiBackend(base_url='http://localhost:3030', dataset='feekg')

# Upload your RDF data
fuseki.upload_turtle_file('results/feekg_graph.ttl')

# Query
query = """
PREFIX feekg: <http://feekg.org/ontology#>
SELECT ?event ?type WHERE {
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
}
"""
results = fuseki.query_sparql(query)

# Get stats
stats = fuseki.get_stats()
print(f"Total triples: {stats['total_triples']}")
```

### Web UI

After starting Fuseki, open: **http://localhost:3030**

- Upload data via drag-and-drop
- Run SPARQL queries in browser
- Visualize results
- Monitor performance

### Pros & Cons

**Pros**:
- Free forever
- Easy to use
- Good documentation
- Standards-compliant
- Persistent storage

**Cons**:
- Requires Java
- Not as fast as commercial options for very large datasets
- Basic UI (no fancy visualizations)

---

## 2. RDFLib (Pure Python) 📚

### Why Choose It?
- ✅ **Pure Python** - No external dependencies
- ✅ **Already installed** in your project!
- ✅ **In-memory or file-based**
- ✅ **Perfect for prototyping**
- ✅ **Easy integration**

### Usage (Already Working!)

```python
from rdflib import Graph

# Load RDF file
g = Graph()
g.parse('results/feekg_graph.ttl', format='turtle')

# Query
query = """
SELECT ?event ?type WHERE {
    ?event a feekg:Event .
    ?event feekg:eventType ?type .
}
"""
results = g.query(query)
for row in results:
    print(row.event, row.type)

# Save to different format
g.serialize(destination='output.xml', format='xml')
```

### When to Use
- ✅ Small datasets (<100K triples)
- ✅ Prototyping
- ✅ One-time conversions
- ✅ Testing SPARQL queries
- ❌ NOT for: Large datasets, multi-user access, production

---

## 3. Virtuoso (OpenLink)

### Why Choose It?
- ✅ **Extremely fast** - Used by DBpedia
- ✅ **Scales to billions** of triples
- ✅ **Hybrid database** - RDF + SQL
- ✅ **Free open source** version available

### Installation

```bash
# Docker (easiest)
docker run -d \
  --name virtuoso \
  -p 8890:8890 \
  -p 1111:1111 \
  -e DBA_PASSWORD=dba \
  openlink/virtuoso-opensource-7

# Web UI: http://localhost:8890/conductor
# SPARQL endpoint: http://localhost:8890/sparql
```

### Usage

```python
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:8890/sparql")
sparql.setQuery("""
    PREFIX feekg: <http://feekg.org/ontology#>
    SELECT ?event ?type WHERE {
        ?event a feekg:Event .
        ?event feekg:eventType ?type .
    }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
```

### Pros & Cons

**Pros**:
- Extremely fast
- Handles huge datasets
- Active community

**Cons**:
- Harder to configure
- Commercial edition required for some features
- Steeper learning curve

---

## 4. GraphDB (Ontotext)

### Why Choose It?
- ✅ **OWL reasoning** built-in
- ✅ **Great UI** for exploration
- ✅ **Free edition** available
- ✅ **Good documentation**

### Installation

```bash
# Download from: https://www.ontotext.com/products/graphdb/download/
# Or use Docker:
docker run -p 7200:7200 \
  ontotext/graphdb:10.6.0 \
  --GDB_HEAP_SIZE=2g
```

### When to Use
- ✅ Need OWL reasoning (infer new facts)
- ✅ Want a nice UI
- ✅ Enterprise support needed
- ❌ Free version limited to 100M triples

---

## 5. Blazegraph (AWS/Wikimedia)

### Why Choose It?
- ✅ **Used by Wikidata**
- ✅ **GPU acceleration** support
- ✅ **High-performance** analytics
- ✅ **Free and open source**

### Installation

```bash
# Download .jar from: https://github.com/blazegraph/database
java -server -Xmx4g -jar blazegraph.jar

# Or Docker:
docker run -p 9999:9999 lyrasis/blazegraph:2.1.5
```

### SPARQL Endpoint
http://localhost:9999/blazegraph/sparql

### Pros & Cons

**Pros**:
- Very fast for analytics
- Good for graph algorithms
- Used in production at scale

**Cons**:
- Development slowed down (maintained but not active)
- Fewer updates than competitors

---

## 6. Cloud Options

### Amazon Neptune
- **Type**: Managed RDF + Property Graph
- **Cost**: ~$0.10/hour + storage
- **Best for**: AWS ecosystem integration
- **SPARQL**: Full support
- **Setup**: AWS Console

### Azure Cosmos DB (Gremlin API)
- **Type**: Managed graph database
- **RDF Support**: Via conversion
- **Cost**: Pay-as-you-go
- **Best for**: Azure ecosystem

### Neo4j with Neosemantics (n10s)
- You already have Neo4j!
- Add RDF support with plugin
- **Hybrid**: Property Graph + RDF

---

## Recommendation for FE-EKG

### Best Choice: **Apache Jena Fuseki**

**Why?**

1. ✅ **Free forever** - Apache license
2. ✅ **Easy setup** - Run our script, done in 2 minutes
3. ✅ **Perfect size** - Your 320 triples (or even 100K+) will run great
4. ✅ **Full SPARQL** - All features you need
5. ✅ **Persistent** - Data survives restarts
6. ✅ **Local** - No network issues like AllegroGraph
7. ✅ **Web UI** - Test queries in browser
8. ✅ **Python API** - I already built the integration!

### Quick Start with Fuseki

```bash
# 1. Install Java (if needed)
brew install openjdk@17

# 2. Run our setup script
chmod +x scripts/setup_fuseki.sh
./scripts/setup_fuseki.sh

# 3. In another terminal, upload your data
./venv/bin/python -c "
from config.fuseki_backend import FusekiBackend
fuseki = FusekiBackend()
fuseki.upload_turtle_file('results/feekg_graph.ttl')
print('Data uploaded!')
"

# 4. Open web UI
open http://localhost:3030
```

### Alternative: Keep RDFLib

If you don't want to run a server, **RDFLib is already working** perfectly for your needs:
- ✅ 320 triples loads instantly
- ✅ SPARQL queries work
- ✅ Zero configuration
- ✅ Export to any format

```bash
# Already works!
./venv/bin/python scripts/demo_rdf_conversion.py
```

---

## Feature Comparison

### SPARQL Support

| Feature | Fuseki | RDFLib | Virtuoso | GraphDB | Blazegraph |
|---------|--------|--------|----------|---------|------------|
| SELECT | ✅ | ✅ | ✅ | ✅ | ✅ |
| CONSTRUCT | ✅ | ✅ | ✅ | ✅ | ✅ |
| ASK | ✅ | ✅ | ✅ | ✅ | ✅ |
| DESCRIBE | ✅ | ✅ | ✅ | ✅ | ✅ |
| UPDATE | ✅ | ✅ | ✅ | ✅ | ✅ |
| Federated | ✅ | ❌ | ✅ | ✅ | ✅ |
| Reasoning | 🟡 | 🟡 | 🟡 | ✅ | 🟡 |

### Performance (for 1M triples)

| Database | Load Time | Query Time | Memory |
|----------|-----------|------------|--------|
| Fuseki | ~5 min | <100ms | ~1GB |
| RDFLib | ~10 min | ~1s | ~2GB |
| Virtuoso | ~2 min | <10ms | ~500MB |
| GraphDB | ~3 min | <50ms | ~1GB |
| Blazegraph | ~3 min | <50ms | ~1.5GB |

**Note**: Your 320 triples will load in <1 second on all of these!

---

## Installation Difficulty

**Easiest (5 ⭐)**:
1. RDFLib - `pip install rdflib` (already done!)
2. Fuseki - Run our script

**Easy (4 ⭐)**:
3. Blazegraph - Download .jar, run
4. GraphDB - Download, install

**Medium (3 ⭐)**:
5. Virtuoso - Docker recommended
6. Stardog - Configuration required

**Hard (2 ⭐)**:
7. AllegroGraph - Network/firewall issues
8. Amazon Neptune - AWS setup

---

## Cost Comparison (Annual)

| Option | Small Dataset | Large Dataset |
|--------|---------------|---------------|
| **Fuseki** | $0 | $0 |
| **RDFLib** | $0 | $0 (but slow) |
| **Virtuoso Open Source** | $0 | $0 |
| **GraphDB Free** | $0 | $0 (100M limit) |
| **Blazegraph** | $0 | $0 |
| **GraphDB Enterprise** | ~$15K | ~$50K |
| **Stardog** | ~$5K | ~$20K |
| **Amazon Neptune** | ~$900 | ~$5K |
| **AllegroGraph** | ~$10K | ~$40K |

---

## My Recommendation

**For FE-EKG, use this approach**:

### Phase 1: Development (Now)
```bash
# Use RDFLib (already working!)
./venv/bin/python scripts/demo_rdf_conversion.py
```

### Phase 2: Local Testing
```bash
# Install Fuseki
./scripts/setup_fuseki.sh

# Upload data
python -c "
from config.fuseki_backend import FusekiBackend
fuseki = FusekiBackend()
fuseki.upload_turtle_file('results/feekg_graph.ttl')
"

# Query via web UI: http://localhost:3030
```

### Phase 3: Production (Future)
- **If staying small (<100K triples)**: Keep Fuseki
- **If scaling big (>1M triples)**: Migrate to Virtuoso
- **If going cloud**: Amazon Neptune
- **If need reasoning**: GraphDB

---

## Files Created

```
feekg/
├── scripts/
│   ├── demo_rdf_conversion.py      # RDFLib conversion (works now!)
│   └── setup_fuseki.sh             # Fuseki installation script
│
├── config/
│   ├── rdf_backend.py              # AllegroGraph backend (blocked)
│   └── fuseki_backend.py           # Fuseki backend (ready!)
│
├── results/
│   ├── feekg_graph.ttl             # Your RDF data (Turtle)
│   ├── feekg_graph.xml             # Your RDF data (XML)
│   └── feekg_graph.nt              # Your RDF data (N-Triples)
│
└── RDF_DATABASE_OPTIONS.md         # This file
```

---

## Next Steps

**Try Fuseki now** (recommended):

```bash
# 1. Make script executable
chmod +x scripts/setup_fuseki.sh

# 2. Start Fuseki (new terminal)
./scripts/setup_fuseki.sh

# 3. Upload your data (another terminal)
./venv/bin/python config/fuseki_backend.py

# 4. Query via web UI
open http://localhost:3030
```

**Or keep using RDFLib** (already working):
```bash
./venv/bin/python scripts/demo_rdf_conversion.py
```

---

**Bottom line**: You have **multiple free, working options** beyond AllegroGraph. Fuseki is the best balance of ease and features for your project.
