# How to View FE-EKG Documentation

## Quick Start

The documentation hub (`docs_hub.html`) provides a searchable interface for all 50+ markdown files, but **browser security restrictions** prevent loading markdown files directly in the modal viewer.

---

## Recommended Methods (Choose One)

### Method 1: HTTP Server (Best Experience)

This allows the modal viewer to work properly:

```bash
# Start HTTP server from project root
python -m http.server 8000

# Or use Python 3
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/docs_hub.html
```

**Now the markdown modal viewer will work!** ✅

---

### Method 2: Direct File Opening (Quick & Easy)

Use the documentation hub for search/navigation, then open files directly:

```bash
# 1. Open the docs hub
open docs_hub.html

# 2. Search for what you need (e.g., "deployment")
# 3. Click the doc you want
# 4. Copy the "open" command from the error message

# Example:
open GETTING_STARTED.md
open DEPLOYMENT_GUIDE.md
open abm/README.md
```

**Pros:** No setup required
**Cons:** Files open in separate windows

---

### Method 3: Command Line Browsing

If you prefer terminal:

```bash
# View file in terminal
cat GETTING_STARTED.md

# Or use a markdown viewer
brew install glow
glow GETTING_STARTED.md

# Or use less with syntax highlighting
bat GETTING_STARTED.md  # requires: brew install bat
```

---

### Method 4: VS Code / Text Editor

```bash
# Open specific file
code GETTING_STARTED.md

# Or open entire project
code .
```

VS Code has excellent markdown preview (⌘K V).

---

## All Important Documentation Files

### 🚀 Start Here

```bash
open GETTING_STARTED.md      # 5-minute quickstart
open VIEW.md                 # How to view system
open README.md               # Main overview
open CLAUDE.md               # Complete dev guide
```

### 🚀 Deployment

```bash
open DEPLOYMENT_GUIDE.md     # Full deployment guide
```

### 🤖 ABM Simulation

```bash
open ABM_INTEGRATION.md      # ABM ↔ KG integration
open abm/README.md           # ABM documentation
```

### 📊 Data

```bash
open REAL_DATA_RESULTS.md    # 4,000 Lehman events
open docs/DATA_PIPELINE.md   # Processing workflow
open CSV_TRACEABILITY_SUMMARY.md  # Data lineage
```

### 🗄️ Database

```bash
open ALLEGROGRAPH_MIGRATION.md  # Database guide
open SECURITY.md                # Credentials
```

### 🌐 Frontend

```bash
open FRONTEND_STATUS.md         # Current deployment
open FRONTEND_ARCHITECTURE.md   # Architecture
open VISUALIZATION_GUIDE.md     # Visualizations
```

### 🔌 API

```bash
open api/README.md              # REST API docs
```

---

## Search Documentation

### Using the Docs Hub

1. **Open:** `open docs_hub.html` (or via HTTP server)
2. **Search:** Press `Ctrl+K` or click search box
3. **Keywords:**
   - "getting started" → Quickstart guides
   - "deployment" → Railway/Vercel
   - "abm" → Simulation
   - "api" → REST endpoints
   - "data" → Data pipeline
   - "frontend" → Next.js app

### Using grep

```bash
# Search all markdown files
grep -r "deployment" *.md docs/*.md

# Find files mentioning specific topic
grep -l "AllegroGraph" *.md

# Search with context
grep -C 3 "Railway" DEPLOYMENT_GUIDE.md
```

---

## Browse Interactively

### With HTTP Server

```bash
# Terminal 1: Start server
python -m http.server 8000

# Terminal 2: Open browser
open http://localhost:8000/docs_hub.html

# Now browse and click any doc - modal will work!
```

### File Explorer

```bash
# macOS Finder
open .

# Then navigate to files and open with your preferred app
```

---

## Troubleshooting

### "Failed to fetch" Error

**Cause:** Browser security (CORS) prevents `file://` protocol from loading other files

**Solutions:**
1. Use HTTP server method (recommended)
2. Click doc link, copy `open` command from error
3. Open files manually from terminal

### Markdown Not Rendering

**If viewing in browser:**
- Use HTTP server method
- Or install browser extension: "Markdown Viewer"

**If viewing in terminal:**
- Install: `brew install glow` or `brew install bat`

### Can't Find File

**Check if file exists:**
```bash
ls -la | grep -i "getting"
ls docs/
ls abm/
```

**All docs listed in:**
```bash
cat DOCS_INDEX.md
```

---

## Quick Reference Commands

```bash
# ===== DOCUMENTATION HUB =====
open docs_hub.html                    # Browse docs (file mode)
python -m http.server 8000            # Start HTTP server
open http://localhost:8000/docs_hub.html  # Browse docs (HTTP mode)

# ===== IMPORTANT DOCS =====
open GETTING_STARTED.md               # Quickstart
open DEPLOYMENT_GUIDE.md              # Deploy guide
open CLAUDE.md                        # Dev guide
open ABM_INTEGRATION.md               # ABM integration

# ===== SEARCH =====
grep -r "keyword" *.md docs/*.md      # Search all docs
cat DOCS_INDEX.md                     # List all docs

# ===== TERMINAL VIEWING =====
glow GETTING_STARTED.md               # Render markdown
bat DEPLOYMENT_GUIDE.md               # Syntax highlighting
cat CLAUDE.md | less                  # Paginated view
```

---

## Summary

**For Best Experience:**
→ Use HTTP server: `python -m http.server 8000`

**For Quick Access:**
→ Use `open <filename>` commands above

**For Search:**
→ Open docs_hub.html, search, then use `open` command

**For Development:**
→ Use VS Code: `code GETTING_STARTED.md`

---

**All methods work!** Choose what's most comfortable for you.
