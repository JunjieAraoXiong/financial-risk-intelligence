# FE-EKG Documentation Audit & Reorganization Plan

**Date:** 2025-11-16
**Status:** Analysis Complete - Ready for Implementation

---

## Executive Summary

After reviewing all README files and the documentation hub (docs_hub.html), I've identified:
- **1 redundant file** to delete (docs/README.md)
- **1 file** to update (results/README.md)
- **1 file** to relocate (data/README_WORKFLOW.md → docs/DATA_PIPELINE.md)
- **6 new documentation files** needed
- **Major docs_hub.html reorganization** with 2 new categories

---

## 1. Redundant/Problematic Files

### ❌ DELETE: `docs/README.md`

**Why Delete:**
- 95% duplicate of main README.md
- Outdated (still heavily references Neo4j)
- Wrong Stage 7 description (says LLM, should be ABM)
- Confuses users between "main" and "docs" README
- All content already covered better in main README.md

**Evidence:**
```
docs/README.md:
- Lines 52-72: Neo4j Browser instructions (DEPRECATED)
- Line 214: "Stage 7: LLM/Nemotron integration" (WRONG - that's complete)
- Line 227: Says "Stage 8: Mini ABM (optional)" (ABM is Week 2-4, not optional)
```

**Action:** Delete file entirely, ensure all links point to main README.md

---

### ⚠️ UPDATE: `results/README.md`

**Why Update:**
- References Evergrande crisis (20 events) - OUTDATED
- Current data is Lehman Brothers (4,000 events)
- File sizes/counts are wrong
- Mentions RDF exports that may not exist

**Changes Needed:**
```diff
- **Total Events:** 20 (Evergrande)
+ **Total Events:** 4,000 (Lehman Brothers)

- **Time Range:** Aug 2020 - Aug 2022 (24 months)
+ **Time Range:** 2007-2009 (Financial Crisis)

- Evolution Links:** 154 computed causal connections
+ Evolution Links:** ~31,173 evolution links

- Total Size:** ~3.0 MB
+ Total Size:** ~150 MB (interactive HTML visualizations)
```

**Action:** Update with current Lehman dataset statistics

---

### 📦 RELOCATE: `data/README_WORKFLOW.md`

**Why Relocate:**
- Excellent workflow documentation
- But buried in data/ folder (low visibility)
- Should be prominently featured in docs/

**New Location:** `docs/DATA_PIPELINE.md`

**Changes:**
- Move file
- Update all references in docs_hub.html
- Add to "Getting Started" quick links

---

## 2. Missing Documentation Files (Create These)

### 🆕 Priority 1: `DEPLOYMENT_GUIDE.md` (MAJOR)

**Why Needed:**
- README has deployment section, but it's scattered
- Users need clear Railway + Vercel guide
- Current FRONTEND_STATUS.md doesn't cover backend deployment

**Structure:**
```markdown
# FE-EKG Deployment Guide

## Quick Deploy (5 minutes)

### Backend → Railway
1. Connect GitHub repo
2. Set environment variables
3. Deploy

### Frontend → Vercel
1. Import frontend repo
2. Set NEXT_PUBLIC_API_URL
3. Deploy

## Detailed Setup
...
```

**Location:** Root directory (major doc)

---

### 🆕 Priority 2: `ABM_INTEGRATION.md` (MAJOR)

**Why Needed:**
- ABM is complete but not in docs_hub.html
- Users don't know ABM exists
- Need to explain ABM ↔ KG integration

**Structure:**
```markdown
# Agent-Based Model Integration

## What is the ABM?
- 10 bank agents + regulator + market
- Simulates financial contagion
- Uses KG topology for network

## How to Run
...

## Integration Points
- Loads network from AllegroGraph
- SLM decision-making (Week 3)
- RAG for historical context (Week 4)
```

**Location:** Root directory (major doc)

---

### 🆕 Priority 3: `GETTING_STARTED.md` (MAJOR)

**Why Needed:**
- New users overwhelmed by 50+ docs
- Need clear 5-minute quickstart
- Point to docs_hub.html early

**Structure:**
```markdown
# Getting Started with FE-EKG

## 5-Minute Quick Start

### 1. View Interactive Visualizations (No Setup)
open results/optimized_knowledge_graph.html

### 2. Explore All Documentation
open docs_hub.html

### 3. Run the API (Requires Setup)
./venv/bin/python api/app.py

## Next Steps
- Production setup: See DEPLOYMENT_GUIDE.md
- Development: See CLAUDE.md
- Case study: See CASE_STUDY_LEHMAN.md
```

**Location:** Root directory (major doc)

---

### 🆕 Priority 4: `RAILWAY_DEPLOYMENT.md` (MAJOR)

**Why Needed:**
- Railway deployment is mentioned but not documented
- Current README section is minimal
- Need troubleshooting section

**Structure:**
```markdown
# Railway Deployment Guide

## Prerequisites
- Railway account
- GitHub repository connected

## Step-by-Step
1. Install Railway CLI
2. Configure environment variables
3. Deploy backend
4. Test deployment

## Environment Variables
AG_URL=...
AG_USER=...
...

## Troubleshooting
...
```

---

### 🆕 Priority 5: `VERCEL_DEPLOYMENT.md` (MAJOR)

**Why Needed:**
- Frontend deployment needs dedicated guide
- CORS configuration is critical
- Environment variable setup is tricky

**Structure:**
```markdown
# Vercel Frontend Deployment

## One-Click Deploy
...

## Manual Deploy
...

## Environment Variables
NEXT_PUBLIC_API_URL=...

## CORS Configuration
Update backend api/app.py:
...
```

---

### 🆕 Priority 6: `ARCHITECTURE.md` (NEW)

**Why Needed:**
- System architecture is explained in CLAUDE.md but scattered
- Need visual diagram + component overview
- Helpful for new developers

**Structure:**
```markdown
# FE-EKG System Architecture

## High-Level Overview
[Diagram: Frontend ↔ Backend ↔ AllegroGraph]

## Components
1. AllegroGraph (Database)
2. Flask API (Backend)
3. Next.js Frontend
4. ABM Simulation

## Data Flow
...
```

---

## 3. Documentation Hub (docs_hub.html) Updates

### Current Stats (Outdated)
```javascript
// Line 838
<span class="prompt">&gt;&gt;</span> 5,105 Events | 22 Entities | 31,173 Evolution Links | 429K Triples in AllegroGraph
```

**Update to:**
```javascript
<span class="prompt">&gt;&gt;</span> 4,000 Events | 22 Entities | 31,173 Evolution Links | 59,090 Triples in AllegroGraph
```

### New Categories to Add

#### Category: 🚀 Getting Started (NEW)
```html
<div class="category-section" id="cat-getting-started" data-category="getting-started">
    <h2>Getting Started</h2>
    <p class="category-description">Quick start guides for new users</p>
    <div class="doc-list">
        <div class="doc-item major" data-keywords="getting started quick start 5 minute setup">
            <div class="doc-info">
                <div class="doc-title">
                    GETTING_STARTED.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">5-minute quick start - view visualizations, run API, explore docs</div>
                <div class="doc-path">./GETTING_STARTED.md</div>
            </div>
            <div class="doc-actions">
                <a href="GETTING_STARTED.md" class="doc-link">Open</a>
            </div>
        </div>

        <!-- Add other getting started docs -->
    </div>
</div>
```

#### Category: 🚀 Deployment (NEW)
```html
<div class="category-section" id="cat-deployment" data-category="deployment">
    <h2>Deployment</h2>
    <p class="category-description">Production deployment guides for Railway and Vercel</p>
    <div class="doc-list">
        <div class="doc-item major" data-keywords="deployment railway vercel production docker">
            <div class="doc-info">
                <div class="doc-title">
                    DEPLOYMENT_GUIDE.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">Complete deployment guide - Railway backend + Vercel frontend</div>
                <div class="doc-path">./DEPLOYMENT_GUIDE.md</div>
            </div>
            <div class="doc-actions">
                <a href="DEPLOYMENT_GUIDE.md" class="doc-link">Open</a>
            </div>
        </div>

        <div class="doc-item major" data-keywords="railway backend api flask deployment">
            <div class="doc-info">
                <div class="doc-title">
                    RAILWAY_DEPLOYMENT.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">Deploy Flask backend to Railway - step-by-step</div>
                <div class="doc-path">./RAILWAY_DEPLOYMENT.md</div>
            </div>
            <div class="doc-actions">
                <a href="RAILWAY_DEPLOYMENT.md" class="doc-link">Open</a>
            </div>
        </div>

        <div class="doc-item major" data-keywords="vercel frontend nextjs deployment">
            <div class="doc-info">
                <div class="doc-title">
                    VERCEL_DEPLOYMENT.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">Deploy Next.js frontend to Vercel - one-click setup</div>
                <div class="doc-path">./VERCEL_DEPLOYMENT.md</div>
            </div>
            <div class="doc-actions">
                <a href="VERCEL_DEPLOYMENT.md" class="doc-link">Open</a>
            </div>
        </div>
    </div>
</div>
```

#### Category: 🤖 ABM Simulation (NEW)
```html
<div class="category-section" id="cat-abm" data-category="abm">
    <h2>Agent-Based Model</h2>
    <p class="category-description">Financial crisis simulation using Mesa framework</p>
    <div class="doc-list">
        <div class="doc-item major" data-keywords="abm agent based model simulation mesa banks contagion">
            <div class="doc-info">
                <div class="doc-title">
                    abm/README.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">Agent-Based Model - simulate financial contagion with 10 banks</div>
                <div class="doc-path">./abm/README.md</div>
            </div>
            <div class="doc-actions">
                <a href="abm/README.md" class="doc-link">Open</a>
            </div>
        </div>

        <div class="doc-item major" data-keywords="abm integration knowledge graph network topology">
            <div class="doc-info">
                <div class="doc-title">
                    ABM_INTEGRATION.md
                    <span class="doc-badge badge-major">MAJOR</span>
                </div>
                <div class="doc-description">ABM ↔ Knowledge Graph integration guide</div>
                <div class="doc-path">./ABM_INTEGRATION.md</div>
            </div>
            <div class="doc-actions">
                <a href="ABM_INTEGRATION.md" class="doc-link">Open</a>
            </div>
        </div>
    </div>
</div>
```

### Update TOC
```html
<div class="toc">
    <h2>[ INDEX ]</h2>
    <ul>
        <li><a href="#cat-getting-started">Getting Started (3)</a></li> <!-- NEW -->
        <li><a href="#cat-main">Main Docs (3)</a></li>
        <li><a href="#cat-deployment">Deployment (3)</a></li> <!-- NEW -->
        <li><a href="#cat-stage">Stage Summaries (4)</a></li>
        <li><a href="#cat-migration">Migration (4)</a></li>
        <li><a href="#cat-data">Data (7)</a></li> <!-- Updated count -->
        <li><a href="#cat-evolution">Evolution (2)</a></li>
        <li><a href="#cat-frontend">Frontend (7)</a></li>
        <li><a href="#cat-viz">Visualization (3)</a></li>
        <li><a href="#cat-performance">Performance (3)</a></li>
        <li><a href="#cat-abm">ABM Simulation (2)</a></li> <!-- NEW -->
        <li><a href="#cat-cleanup">Cleanup (2)</a></li>
        <li><a href="#cat-api">API (1)</a></li>
        <li><a href="#cat-llm">LLM/AI (3)</a></li>
        <li><a href="#cat-case">Case Studies (1)</a></li>
        <li><a href="#cat-output">Output (1)</a></li>
        <li><a href="#cat-planning">Planning (2)</a></li> <!-- Updated -->
        <li><a href="#cat-consolidated">Consolidated (3)</a></li>
    </ul>
</div>
```

---

## 4. Implementation Checklist

### Phase 1: Cleanup (Do First)
- [ ] Delete `docs/README.md`
- [ ] Update `results/README.md` with Lehman statistics
- [ ] Move `data/README_WORKFLOW.md` → `docs/DATA_PIPELINE.md`
- [ ] Update all links referencing moved file

### Phase 2: Create New Docs (Priority Order)
- [ ] Create `GETTING_STARTED.md`
- [ ] Create `DEPLOYMENT_GUIDE.md`
- [ ] Create `RAILWAY_DEPLOYMENT.md`
- [ ] Create `VERCEL_DEPLOYMENT.md`
- [ ] Create `ABM_INTEGRATION.md`
- [ ] Create `ARCHITECTURE.md`

### Phase 3: Update docs_hub.html
- [ ] Update statistics (line 838)
- [ ] Add "Getting Started" category
- [ ] Add "Deployment" category
- [ ] Add "ABM Simulation" category
- [ ] Update TOC links
- [ ] Update quick links section
- [ ] Add new docs to search keywords

### Phase 4: Update Cross-References
- [ ] Update main README.md to reference new docs
- [ ] Update CLAUDE.md to reference new deployment guides
- [ ] Update FRONTEND_STATUS.md to reference deployment docs
- [ ] Verify all links work

### Phase 5: Testing
- [ ] Open docs_hub.html and test all links
- [ ] Search for keywords (deployment, abm, getting started)
- [ ] Verify all categories display correctly
- [ ] Check responsive design (mobile)

---

## 5. Priority Ranking

### Must Do (Week 1)
1. Delete docs/README.md
2. Create GETTING_STARTED.md
3. Create DEPLOYMENT_GUIDE.md
4. Update docs_hub.html with new categories

### Should Do (Week 2)
5. Create RAILWAY_DEPLOYMENT.md
6. Create VERCEL_DEPLOYMENT.md
7. Update results/README.md
8. Create ABM_INTEGRATION.md

### Nice to Have (Week 3)
9. Create ARCHITECTURE.md
10. Move data/README_WORKFLOW.md
11. Add changelog tracking

---

## 6. Estimated Effort

| Task | Time | Difficulty |
|------|------|------------|
| Delete docs/README.md | 5 min | Easy |
| Update results/README.md | 15 min | Easy |
| Move README_WORKFLOW.md | 10 min | Easy |
| Create GETTING_STARTED.md | 30 min | Medium |
| Create DEPLOYMENT_GUIDE.md | 60 min | Medium |
| Create RAILWAY_DEPLOYMENT.md | 45 min | Medium |
| Create VERCEL_DEPLOYMENT.md | 45 min | Medium |
| Create ABM_INTEGRATION.md | 30 min | Medium |
| Create ARCHITECTURE.md | 60 min | Hard |
| Update docs_hub.html | 45 min | Medium |

**Total: ~5 hours**

---

## 7. Benefits After Completion

### User Experience
- Clear onboarding path (Getting Started)
- Easy deployment (dedicated guides)
- Discoverability of ABM component
- No confusion between duplicate READMEs

### Maintainability
- Single source of truth (no docs/README.md duplicate)
- Logical category structure
- Easy to find deployment info
- Clear documentation hierarchy

### Completeness
- All components documented (ABM was missing)
- Deployment fully covered
- Data pipeline prominently featured

---

## Next Steps

Would you like me to:
1. **Delete docs/README.md** right now?
2. **Create GETTING_STARTED.md** as the first new doc?
3. **Update docs_hub.html** with new categories?
4. **Do all of Phase 1** (cleanup) immediately?

Let me know which approach you prefer!
