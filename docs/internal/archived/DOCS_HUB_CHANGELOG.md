# Documentation Hub Changelog

## Version 2.2.0 (2025-11-16)

### Major Updates

#### Statistics Updated
- **Events:** 5,105 → **4,000** (Lehman Brothers dataset)
- **Triples:** 429K → **59K** (AllegroGraph actual count)
- **Evolution Links:** 31,173 (unchanged)
- **Entities:** 22 (unchanged)

#### New Categories Added

1. **🚀 Getting Started** (NEW - Priority 1)
   - `GETTING_STARTED.md` - 5-minute quickstart
   - `VIEW.md` - How to view system
   - `FRONTEND_SETUP_GUIDE.md` - 30-min setup

2. **🚀 Deployment** (NEW)
   - `DEPLOYMENT_GUIDE.md` - Complete Railway + Vercel guide
   - `RAILWAY_DEPLOYMENT.md` - Backend deployment (coming soon)
   - `VERCEL_DEPLOYMENT.md` - Frontend deployment (coming soon)

3. **🤖 ABM Simulation** (NEW)
   - `abm/README.md` - Agent-Based Model documentation
   - `ABM_INTEGRATION.md` - ABM ↔ KG integration

#### Documentation Improvements

**Data Category:**
- Added `docs/DATA_PIPELINE.md` (moved from `data/README_WORKFLOW.md`)
- Now 7 documents (was 6)

**Footer Links:**
- Added "Quick Start" link
- Added "Deploy" link
- Updated version number

#### Technical Improvements

**Markdown Viewer:**
- Better error handling
- Shows attempted file path
- Provides troubleshooting steps
- Suggests `open` command for direct access

**Path Resolution:**
- Improved relative path handling
- Removes leading `./` for consistency

### Files Changed

#### Deleted
- ❌ `docs/README.md` (redundant, 95% duplicate of main README)

#### Created
- ✅ `GETTING_STARTED.md` - New quickstart guide
- ✅ `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- ✅ `ABM_INTEGRATION.md` - ABM integration docs
- ✅ `DOCUMENTATION_AUDIT.md` - Analysis and planning doc
- ✅ `DOCS_HUB_CHANGELOG.md` - This file

#### Moved
- 📦 `data/README_WORKFLOW.md` → `docs/DATA_PIPELINE.md`

#### Updated
- 🔄 `docs_hub.html` - Major updates (stats, categories, error handling)
- 🔄 `results/README.md` - Updated to Lehman dataset statistics

### Category Count

**Before:** 15 categories
**After:** 18 categories

**New:**
1. Getting Started
2. Deployment
3. ABM Simulation

### Index Structure

```
├── 🚀 Getting Started (3)          ← NEW
├── 📚 Main Docs (3)
├── 🚀 Deployment (3)               ← NEW
├── 📋 Stage Summaries (4)
├── 🗄️ Migration (4)
├── 📊 Data (7)                     ← Updated (was 6)
├── 🧬 Evolution (2)
├── 🌐 Frontend (7)
├── 📊 Visualization (3)
├── ⚡ Performance (3)
├── 🤖 ABM Simulation (2)           ← NEW
├── 🔧 Cleanup (2)
├── 🔌 API (1)
├── 🧠 LLM/AI (3)
├── 📖 Case Studies (1)
├── 📁 Output (1)
├── 📈 Planning (2)
└── 📋 Consolidated (3)
```

### Search Keywords Added

New searchable terms:
- "getting started", "quick start", "beginner", "intro"
- "deployment", "railway", "vercel", "production"
- "abm", "agent based model", "simulation", "mesa"
- "pipeline", "workflow", "etl"

### Breaking Changes

⚠️ **None** - All changes are additive or improvements

### Migration Guide

If you have links to the old documentation:

| Old Path | New Path | Status |
|----------|----------|--------|
| `docs/README.md` | Use main `README.md` | Deleted |
| `data/README_WORKFLOW.md` | `docs/DATA_PIPELINE.md` | Moved |

### Testing Checklist

To verify the update:

- [ ] Open `docs_hub.html` in browser
- [ ] Search for "getting started" → Should find new category
- [ ] Search for "deployment" → Should find deployment docs
- [ ] Search for "abm" → Should find ABM simulation docs
- [ ] Click any markdown link → Should open in modal
- [ ] Check footer shows v2.2.0
- [ ] Verify statistics show 4,000 events and 59K triples

### Known Issues

**Fixed in v2.2.0:**
- ✅ Improved markdown file path resolution
- ✅ Better error messages for failed loads
- ✅ Relative path handling

**Remaining:**
- Browser CORS restrictions may prevent local file loading in some browsers
- Workaround: Use `open <filename>` command shown in error message

### Next Steps

**Planned for v2.3.0:**
- [ ] Create `RAILWAY_DEPLOYMENT.md` (extract from DEPLOYMENT_GUIDE.md)
- [ ] Create `VERCEL_DEPLOYMENT.md` (extract from DEPLOYMENT_GUIDE.md)
- [ ] Add "Recent Updates" section to homepage
- [ ] Add version history modal

### Contributors

- Documentation reorganization based on audit findings
- User experience improvements
- Better onboarding for new users

---

**Version:** 2.2.0
**Release Date:** 2025-11-16
**Total Documentation Files:** 50+ markdown files
**Categories:** 18 (up from 15)
**New Guides:** 3 major additions
