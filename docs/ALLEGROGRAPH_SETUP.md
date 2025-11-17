# AllegroGraph Setup Guide

Complete guide to connecting FE-EKG to AllegroGraph using HTTPS.

**Status:** ✅ Connection working via HTTPS port 443
**Issue:** ⚠️ Write permissions required for full functionality

---

## Quick Start

### Working Connection Method

```python
from franz.openrdf.connect import ag_connect

conn = ag_connect(
    'KG_200203',  # Repository name
    user='sadmin',
    host='https://qa-agraph.nelumbium.ai:443',  # ← Explicit :443 is key!
    password='your_password'
)

print(f"✅ Connected! Triples: {conn.size()}")
conn.close()
```

### Key Requirements

1. **Install dependencies:**
   ```bash
   ./venv/bin/pip install agraph-python pycurl
   ```

2. **Use explicit port 443** in host URL
3. **Use `ag_connect`** (not `AllegroGraphServer`)

---

## Problem & Solution

### The Port 10035 Problem ❌

**Original approach (blocked):**
```python
from franz.openrdf.sail.allegrographserver import AllegroGraphServer

server = AllegroGraphServer(
    host="qa-agraph.nelumbium.ai",
    port=10035,  # ← BLOCKED BY FIREWALL
    user="sadmin",
    password=password
)
# Result: Connection timeout
```

**Why it fails:**
- 🔥 Port 10035 blocked by corporate firewall
- 🔒 Requires special network access (VPN)
- ⚠️ Native AllegroGraph protocol not accessible

### The HTTPS Solution ✅

**Working approach:**
```python
from franz.openrdf.connect import ag_connect

conn = ag_connect(
    'repository_name',
    user='sadmin',
    host='https://qa-agraph.nelumbium.ai:443',  # ← HTTPS with explicit :443
    password='your_password'
)
# Result: ✅ Connected!
```

**Why it works:**
- ✅ Uses HTTPS (port 443) - never blocked
- ✅ REST API instead of native protocol
- ✅ Standard HTTP authentication
- ✅ Firewall-friendly

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# AllegroGraph connection
AG_URL=https://qa-agraph.nelumbium.ai:443/
AG_USER=sadmin
AG_PASS=your_password
AG_REPO=feekg_dev
```

### Backend Configuration

Your backends have been updated to use port 443:

**[config/rdf_backend.py](../config/rdf_backend.py):**
```python
# Ensure URL has explicit port 443
if ':443' not in self.ag_url and self.ag_url.startswith('https://'):
    self.ag_url = self.ag_url.rstrip('/') + ':443'

self.conn = ag_connect(
    self.ag_repo,
    user=self.ag_user,
    host=self.ag_url,  # ← Full HTTPS URL with :443
    password=self.ag_pass
)
```

**[config/graph_backend.py](../config/graph_backend.py):**
Same configuration applied to `AllegroGraphBackend` class.

---

## Current Capabilities

### What Works ✅

- ✅ **Connect** to AllegroGraph via HTTPS port 443
- ✅ **List** repositories (28 repositories available)
- ✅ **Read** from existing repositories (e.g., `KG_200203`)
- ✅ **Query** with SPARQL
- ✅ **Get** triple counts and statistics

### What Requires Permissions ⚠️

- ⚠️ **Create** new repositories (e.g., `feekg_dev`)
- ⚠️ **Write** to repositories
- ⚠️ **Delete** triples
- ⚠️ **Modify** repository settings

**Error seen:**
```
401 User 'sadmin' does not have sufficient permissions to perform this operation.
```

---

## Usage Examples

### Test Connection

```bash
./venv/bin/python -c "
from franz.openrdf.connect import ag_connect
import os
from dotenv import load_dotenv
load_dotenv()

conn = ag_connect('KG_200203', user='sadmin',
                  host='https://qa-agraph.nelumbium.ai:443',
                  password=os.getenv('AG_PASS'))
print(f'✅ Connected! Triples: {conn.size()}')
conn.close()
"
```

### Using RDFBackend

```bash
AG_REPO=KG_200203 ./venv/bin/python -c "
from config.rdf_backend import RDFBackend

backend = RDFBackend()
backend.connect()

# Get stats
stats = backend.get_stats()
print(f\"Total triples: {stats['total_triples']}\")

# Query
results = backend.query_sparql('''
SELECT * WHERE { ?s ?p ?o } LIMIT 5
''')

backend.close()
"
```

### Using Native Script

```bash
# Query existing repository (read-only)
AG_REPO=KG_200203 ./venv/bin/python scripts/store_triples_native.py --mode query

# Store triples (requires write permissions)
./venv/bin/python scripts/store_triples_native.py --mode sample
./venv/bin/python scripts/store_triples_native.py --mode neo4j
```

---

## Getting Write Access

### Option 1: Request Repository Creation (Recommended)

Ask your AllegroGraph admin to:

1. Create repository: `feekg_dev`
2. Grant write access to user: `sadmin`

Then you can:
```bash
# Store sample triples
./venv/bin/python scripts/store_triples_native.py --mode sample

# Load from Neo4j
./venv/bin/python scripts/store_triples_native.py --mode neo4j

# Upload RDF files
python -c "
from config.rdf_backend import RDFBackend
backend = RDFBackend()
backend.connect()
backend.upload_turtle_file('ontology/feekg_minimal.ttl')
backend.close()
"
```

### Option 2: Use Existing Writable Repository

Test which repositories you can write to:

```bash
for repo in Crisis_report Event_risk Events2018; do
  echo "Testing $repo..."
  AG_REPO=$repo python scripts/store_triples_native.py --mode sample
done
```

Update `.env` with writable repository:
```bash
AG_REPO=<writable_repository>
```

---

## Alternative Solutions

### Option A: Apache Jena Fuseki (Local Triplestore)

**Advantages:**
- ✅ No permission issues
- ✅ Full control
- ✅ Runs locally
- ✅ Already integrated: [config/fuseki_backend.py](../config/fuseki_backend.py)

**Setup:**
```bash
./scripts/setup_fuseki.sh

# Upload data
python -c "
from config.fuseki_backend import FusekiBackend
fuseki = FusekiBackend()
fuseki.upload_turtle_file('ontology/feekg_minimal.ttl')
"

# Open web UI
open http://localhost:3030
```

### Option B: RDFLib (File-Based RDF)

**Advantages:**
- ✅ Already working
- ✅ Zero setup
- ✅ No server needed

**Usage:**
```bash
./venv/bin/python scripts/demo_rdf_conversion.py
```

### Option C: Keep Using Neo4j

**Your current setup already works great:**
- ✅ Neo4j as primary database
- ✅ RDFLib for RDF export
- ✅ REST API for queries
- ✅ Full visualization support

---

## Connection Method Comparison

| Feature | Port 10035 (Original) | HTTPS Port 443 (Working) |
|---------|----------------------|---------------------------|
| **Library** | franz.openrdf | franz.openrdf + pycurl |
| **Works remotely?** | ❌ No | ✅ Yes |
| **Firewall-friendly?** | ❌ No | ✅ Yes |
| **Triple storage** | ✅ Yes | ✅ Yes |
| **SPARQL queries** | ✅ Yes | ✅ Yes |
| **Authentication** | Basic | HTTPS Basic |

---

## Available Repositories

Your AllegroGraph server has **28 repositories**:

- BIS2008
- Crisis_report
- Event_risk
- Events&Risk
- Events2018
- KG_200203 (currently used for testing)
- ... and 22 more

---

## Files Created/Updated

### Core Backends ✅
- [config/rdf_backend.py](../config/rdf_backend.py) - HTTPS port 443 connection
- [config/graph_backend.py](../config/graph_backend.py) - AllegroGraphBackend updated
- [requirements.txt](../requirements.txt) - Added pycurl dependency

### Scripts ✨
- [scripts/store_triples_native.py](../scripts/store_triples_native.py) - Native client with HTTPS
- [scripts/store_triples_https.py](../scripts/store_triples_https.py) - REST API approach
- [scripts/test_allegrograph_simple.py](../scripts/test_allegrograph_simple.py) - Connection test

---

## Troubleshooting

### Connection Timeout

**Problem:** Connection hangs or times out

**Solution:** Ensure you're using HTTPS with explicit port 443:
```python
host='https://qa-agraph.nelumbium.ai:443'  # ← Must include :443
```

### Permission Denied (401)

**Problem:** `401 Unauthorized` or insufficient permissions

**Solution:**
1. Request admin to grant write access
2. Use existing writable repository
3. Use Fuseki or RDFLib alternatives

### Import Error: pycurl

**Problem:** `ImportError: No module named 'pycurl'`

**Solution:**
```bash
./venv/bin/pip install pycurl
```

### SSL Certificate Errors

**Problem:** SSL verification fails

**Solution:** Update certificates or use verify=False in requests (development only)

---

## Next Steps

### For Immediate Use (Read-Only)

```bash
# Test connection
AG_REPO=KG_200203 ./venv/bin/python -c "
from franz.openrdf.connect import ag_connect
import os
from dotenv import load_dotenv
load_dotenv()
conn = ag_connect(os.getenv('AG_REPO'), user=os.getenv('AG_USER'),
                  host='https://qa-agraph.nelumbium.ai:443',
                  password=os.getenv('AG_PASS'))
print(f'✅ Connected! Triples: {conn.size()}')
conn.close()
"
```

### For Full Integration (Requires Permissions)

1. **Request repository creation** from admin
2. **Test write access** with sample data
3. **Load Neo4j data** to AllegroGraph
4. **Run SPARQL queries** via backend

### For Alternative Setup

```bash
# Option A: Install Fuseki (5 minutes)
./scripts/setup_fuseki.sh

# Option B: Use RDFLib (works now)
./venv/bin/python scripts/demo_rdf_conversion.py
```

---

## Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **HTTPS Connection** | ✅ Working | Port 443, firewall-friendly |
| **Read Access** | ✅ Working | Can query 28 repositories |
| **Write Access** | ⚠️ Pending | Requires admin permissions |
| **Native Client** | ✅ Configured | Using ag_connect with pycurl |
| **HTTPS Backend** | ✅ Working | REST API alternative |
| **Backends Updated** | ✅ Done | RDF and Graph backends |

**Bottom Line:** Connection works perfectly via HTTPS port 443. Just need write permissions for full functionality, or use Fuseki/RDFLib alternatives.

---

**Last Updated:** 2025-11-14
**Status:** Production Ready (Read-Only)
**Next Action:** Request write permissions or use alternatives
