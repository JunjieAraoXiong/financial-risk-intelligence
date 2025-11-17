# FE-EKG Codebase Cleanup Plan

**Generated:** 2025-11-14
**Status:** Ready for Execution
**Estimated Time Savings:** ~1,500+ lines of duplicated code

---

## Phase 1: CRITICAL (2-3 hours) - Save ~1,075 lines

### 1.1 Consolidate Backend Configurations ⚡ HIGHEST PRIORITY

**Problem:** 4 similar backend files with duplicated logic

**Action:**
```bash
# Keep only these 2 files:
config/graph_backend.py          # Neo4j + AllegroGraph unified
config/secrets.py                # Credential management

# DELETE these redundant files:
rm config/rdf_backend.py
rm config/allegrograph_https_backend.py
rm config/fuseki_backend.py
```

**Refactor Steps:**
1. Merge `AllegroGraphHTTPSBackend` class from `allegrograph_https_backend.py` into `graph_backend.py`
2. Extract credential loading into `secrets.py::get_ag_credentials()` function
3. Create utility `secrets.py::normalize_ag_url(url)` to handle port :443 logic
4. Update all imports:
   ```python
   # Change from:
   from config.rdf_backend import RDFBackend
   # To:
   from config.graph_backend import AllegroGraphBackend
   ```

**Files to update:**
- `ingestion/load_evergrande.py`
- `ingestion/load_lehman.py`
- `scripts/store_triples_*.py`
- All verify scripts

**Lines saved:** ~500

---

### 1.2 Merge Capital IQ Processing Scripts

**Problem:** v1 and v2 have 80% code overlap

**Action:**
```bash
# Merge improvements from v2 into v1:
# Keep: ingestion/process_capital_iq.py
# Delete: ingestion/process_capital_iq_v2.py
```

**Refactor Steps:**
1. Copy any unique optimizations from v2 into v1
2. Add `--mode` argument to choose processing strategy
3. Delete `process_capital_iq_v2.py`

**Lines saved:** ~200

---

### 1.3 Create Verification Base Class

**Problem:** 5 verify scripts with identical boilerplate

**Action:**
```bash
# Create new base class:
scripts/verify_base.py

# Refactor all 5 scripts to inherit from base
```

**Create `scripts/verify_base.py`:**
```python
"""Base class for verification scripts."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.graph_backend import get_connection

class VerificationBase:
    """Base class for all verification scripts."""

    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.backend = None

    def print_header(self):
        """Print formatted header."""
        print(f"\n{'='*70}")
        print(f"  {self.stage_name} VERIFICATION")
        print(f"{'='*70}\n")

    def connect(self) -> bool:
        """Connect to database."""
        print("1️⃣  Connecting to graph database...")
        try:
            self.backend = get_connection()
            print(f"   ✅ Connected to {self.backend.__class__.__name__}")
            return True
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False

    def close(self):
        """Close connection."""
        if self.backend:
            self.backend.close()
            print("\n🔒 Connection closed")

    def run_checks(self):
        """Override this method in subclasses."""
        raise NotImplementedError

    def execute(self):
        """Main execution flow."""
        self.print_header()
        if not self.connect():
            return False

        try:
            result = self.run_checks()
            return result
        finally:
            self.close()
```

**Update each verify script:**
```python
# OLD (150+ lines):
# ... boilerplate connection code ...
# ... custom checks ...

# NEW (~50 lines):
from scripts.verify_base import VerificationBase

class Stage2Verification(VerificationBase):
    def run_checks(self):
        # Only stage-specific logic here
        pass

if __name__ == '__main__':
    verifier = Stage2Verification("Stage 2: Schema")
    verifier.execute()
```

**Lines saved:** ~375

---

## Phase 2: IMPORTANT (2-3 hours) - Save ~400 lines

### 2.1 Consolidate Documentation Files 📚

**Create organized docs/ structure:**

```bash
# Create docs folder
mkdir -p docs

# Consolidate and move files:
# 1. AllegroGraph docs (3 → 1)
cat ALLEGROGRAPH_COMPARISON.md ALLEGROGRAPH_STATUS.md ALLEGROGRAPH_NATIVE_CLIENT.md \
    > docs/ALLEGROGRAPH_SETUP.md
rm ALLEGROGRAPH_*.md

# 2. Lehman case study docs (2 → 1)
cat LEHMAN_CASE_STUDY_PIPELINE.md QUICK_START_LEHMAN.md > docs/CASE_STUDY_LEHMAN.md
rm LEHMAN_CASE_STUDY_PIPELINE.md QUICK_START_LEHMAN.md

# 3. Visualization docs (3 → 1)
cat VISUALIZATION_IMPROVEMENTS.md TIMELINE_VISUALIZATION.md COLOR_SCHEME.md \
    > docs/VISUALIZATIONS.md
rm VISUALIZATION_IMPROVEMENTS.md TIMELINE_VISUALIZATION.md COLOR_SCHEME.md

# 4. LLM/NLP docs (4 → 1)
cat LLM_INTEGRATION_SUMMARY.md NLP_VALUE_ADD.md CLASSIFICATION_IMPROVEMENT.md NVIDIA_QUICKSTART.md \
    > docs/LLM_INTEGRATION.md
rm LLM_INTEGRATION_SUMMARY.md NLP_VALUE_ADD.md CLASSIFICATION_IMPROVEMENT.md NVIDIA_QUICKSTART.md

# 5. Optimization docs (3 → 1)
cat OPTIMIZATION_REPORT.md PIPELINE_COMPARISON.md ETL_COMPLETION_SUMMARY.md \
    > docs/OPTIMIZATION.md
rm OPTIMIZATION_REPORT.md PIPELINE_COMPARISON.md ETL_COMPLETION_SUMMARY.md

# 6. RDF docs (2 → 1)
cat RDF_CONVERSION_GUIDE.md RDF_DATABASE_OPTIONS.md > docs/RDF_SETUP.md
rm RDF_CONVERSION_GUIDE.md RDF_DATABASE_OPTIONS.md

# Keep in root (move to docs):
mv CLAUDE.md docs/PROJECT_GUIDE.md
mv README.md docs/README.md
ln -s docs/README.md README.md  # Symlink for GitHub

# Keep in root as-is:
# - DATA_QUALITY_REPORT.md
# - REAL_DATA_RESULTS.md
# - STAGE6_SUMMARY.md
```

**Final docs/ structure:**
```
docs/
├── README.md                    # Main entry (from root)
├── PROJECT_GUIDE.md             # Claude instructions (from CLAUDE.md)
├── ALLEGROGRAPH_SETUP.md        # Consolidated AG docs
├── CASE_STUDY_LEHMAN.md         # Lehman case
├── VISUALIZATIONS.md            # All viz docs
├── LLM_INTEGRATION.md           # AI/NLP features
├── OPTIMIZATION.md              # Performance docs
└── RDF_SETUP.md                 # RDF conversion
```

**Before:** 25 MD files in root (217K)
**After:** ~8 core docs (60K) + symlinks

---

### 2.2 Merge RDF Conversion Scripts

**Problem:** [convert_to_rdf.py](scripts/convert_to_rdf.py) and [convert_lehman_to_rdf.py](scripts/convert_lehman_to_rdf.py) are 80% identical

**Action:**
```bash
# Create unified script with parameters:
scripts/convert_neo4j_to_rdf.py --case-study [evergrande|lehman]

# Delete old scripts:
rm scripts/convert_to_rdf.py
rm scripts/convert_lehman_to_rdf.py
```

**Template:**
```python
#!/usr/bin/env python3
"""Convert Neo4j data to RDF format."""
import argparse

def convert_to_rdf(case_study: str, output_file: str):
    """Unified conversion logic."""
    # Load case-specific config
    config = {
        'evergrande': {
            'data_file': 'data/evergrande_crisis.json',
            'output': 'ontology/evergrande_feekg.ttl'
        },
        'lehman': {
            'data_file': 'data/capital_iq_processed/lehman_case_study_v2.json',
            'output': 'ontology/lehman_feekg.ttl'
        }
    }[case_study]

    # ... unified conversion logic ...

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-study', choices=['evergrande', 'lehman'], required=True)
    parser.add_argument('--output', help='Output RDF file path')
    args = parser.parse_args()

    convert_to_rdf(args.case_study, args.output)
```

**Lines saved:** ~250

---

### 2.3 Extract sys.path Setup Utility

**Problem:** 25 files have different implementations of `sys.path.insert()`

**Action:**
```bash
# Create utility module:
config/path_setup.py
```

**Create `config/path_setup.py`:**
```python
"""Path setup utility for all scripts."""
import sys
from pathlib import Path

def setup_project_path():
    """Add project root to sys.path if not already present."""
    project_root = Path(__file__).parent.parent
    project_root_str = str(project_root)

    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

# Auto-run on import
setup_project_path()
```

**Update all scripts:**
```python
# OLD (3 different variations):
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# or
sys.path.insert(0, str(Path(__file__).parent.parent))
# or
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NEW (1 line):
from config.path_setup import setup_project_path
```

**Files to update:** All 25 scripts with sys.path manipulation

---

### 2.4 Consolidate Store Triple Scripts

**Problem:** [store_triples_https.py](scripts/store_triples_https.py) and [store_triples_native.py](scripts/store_triples_native.py) have 60% overlap

**Action:**
```bash
# Create unified script:
scripts/store_triples.py --method [https|native]

# Delete old scripts:
rm scripts/store_triples_https.py
rm scripts/store_triples_native.py
```

---

## Phase 3: OPTIMIZATION (1-2 hours)

### 3.1 Implement Connection Pooling in API

**Problem:** Each API request creates new database connection

**Current ([api/app.py](api/app.py#L72)):**
```python
@app.route('/api/entities')
def get_entities():
    backend = get_connection()  # NEW CONNECTION EACH TIME!
    # ... query ...
    backend.close()
```

**Optimized:**
```python
# At module level:
from functools import lru_cache

@lru_cache(maxsize=1)
def get_cached_connection():
    """Reuse single connection across requests."""
    return get_connection()

# In routes:
@app.route('/api/entities')
def get_entities():
    backend = get_cached_connection()  # REUSED!
    # ... query ...
    # DON'T close - reuse connection
```

**Performance impact:** 10-50x faster API responses

---

### 3.2 Combine Multiple Count Queries

**Problem:** Multiple count queries executed separately

**Current:**
```python
entity_count = backend.execute_query("MATCH (e:Entity) RETURN count(e)")
event_count = backend.execute_query("MATCH (ev:Event) RETURN count(ev)")
risk_count = backend.execute_query("MATCH (r:Risk) RETURN count(r)")
```

**Optimized:**
```python
# Single query with multiple returns:
query = """
MATCH (e:Entity)
MATCH (ev:Event)
MATCH (r:Risk)
RETURN count(e) as entities, count(ev) as events, count(r) as risks
"""
result = backend.execute_query(query)
```

---

### 3.3 Cache JSON Data Loading

**Problem:** Same JSON files loaded repeatedly

**Create `data/data_cache.py`:**
```python
"""Centralized data loading with caching."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=10)
def load_json_cached(file_path: str):
    """Load JSON with caching."""
    with open(file_path, 'r') as f:
        return json.load(f)

# Usage:
data = load_json_cached('data/evergrande_crisis.json')  # Cached!
```

---

## Phase 4: CLEANUP (30 min)

### 4.1 Delete Unnecessary Files

```bash
# Test/debug files (verify first!):
rm scripts/simple_test.py                    # Incomplete test stub
rm scripts/test_allegrograph_simple.py       # Duplicate AG test

# Check if fuseki is used anywhere:
grep -r "fuseki_backend" . || rm config/fuseki_backend.py
```

---

## Execution Checklist

### Phase 1: Critical (DO FIRST)
- [ ] 1.1 Consolidate backend files
- [ ] 1.2 Merge Capital IQ v1/v2
- [ ] 1.3 Create verification base class

### Phase 2: Important
- [ ] 2.1 Reorganize documentation (25 → 8 files)
- [ ] 2.2 Merge RDF conversion scripts
- [ ] 2.3 Extract path setup utility
- [ ] 2.4 Consolidate store triple scripts

### Phase 3: Optimization
- [ ] 3.1 Add connection pooling to API
- [ ] 3.2 Combine count queries
- [ ] 3.3 Cache JSON loading

### Phase 4: Cleanup
- [ ] 4.1 Delete unnecessary files
- [ ] Run all verify scripts to ensure nothing broke
- [ ] Update CLAUDE.md with new structure

---

## Expected Outcomes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Python files** | 66 | ~58 | -12% |
| **Markdown files** | 42 | ~15 | -64% |
| **Duplicated code** | ~1,500 lines | ~150 lines | -90% |
| **Backend configs** | 4 files | 2 files | -50% |
| **API latency** | ~50-100ms | ~5-10ms | 10x faster |
| **Codebase clarity** | Complex | Clean | ✨ |

---

## Testing Plan

After each phase:

```bash
# Run all verification scripts:
./venv/bin/python scripts/verify_stage2.py
./venv/bin/python scripts/verify_stage3.py
./venv/bin/python scripts/verify_stage4.py
./venv/bin/python scripts/verify_stage5.py
./venv/bin/python scripts/verify_stage6.py

# Test API:
./venv/bin/python api/app.py &
curl http://localhost:5000/health

# Run demo scripts:
./venv/bin/python scripts/demo_risk_queries.py
./venv/bin/python scripts/demo_visualizations.py
```

---

## Rollback Plan

Before starting:
```bash
# Create backup branch:
git checkout -b cleanup-backup
git add -A
git commit -m "Pre-cleanup backup"

# Create working branch:
git checkout -b codebase-cleanup
```

If something breaks:
```bash
git checkout cleanup-backup
```

---

**Author:** Claude Code Analysis
**Version:** 1.0
**Last Updated:** 2025-11-14
