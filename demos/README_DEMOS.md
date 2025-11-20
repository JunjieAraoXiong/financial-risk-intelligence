# FE-EKG Interactive Demos

**Purpose:** Local Jupyter notebooks for presentations, investor demos, and educational walkthroughs.

## 📚 Available Demos:

### 1. **quick_demo.ipynb** ⭐ RECOMMENDED
- **5-minute** investor pitch demo
- Shows: Problem → Solution → Live Query → ROI
- Business-focused (no technical jargon)
- Perfect for: Main investor presentation, Act 2 system overview

### 2. **crisis_timeline_demo.ipynb** - Interactive Explorer
- Toggle between Graph/Timeline/Triple views
- Click events to see connections
- September 2008 crisis narrative
- Perfect for: Interactive demonstrations, Q&A sessions

### 3. **triple_formation_demo.ipynb** - Technical Deep Dive
- 15-minute detailed walkthrough
- Explains RDF triples, three-layer architecture
- Shows transformation pipeline
- Perfect for: Technical due diligence, engineering interviews

---

## 🚀 Quick Start:

### **Step 1: Start Jupyter**

**Note:** Use the main project's virtual environment (all dependencies already installed).

```bash
cd /Users/hansonxiong/Desktop/DDP/feekg/demos

# Activate the main project venv
source ../venv/bin/activate  # On Mac/Linux
# OR: ..\venv\Scripts\activate  # On Windows

# Start Jupyter
jupyter notebook
```
This will open your browser at `http://localhost:8888`

### **Step 2: Open a Demo**
- Click on `triple_formation_demo.ipynb` or `crisis_timeline_demo.ipynb`
- Run all cells: Click "Cell" → "Run All"
- Interact with widgets and visualizations

---

## 📖 Demo Descriptions:

### **Triple Formation Demo** (`triple_formation_demo.ipynb`)

**Use Case:** Explain to investors/non-technical audience how the technology works

**What It Shows:**
1. **The Problem** - Unstructured CSV data
2. **The Solution** - Structured RDF knowledge graph
3. **Step-by-Step Transformation** - CSV → Events → Entities → Triples
4. **Real Example** - Lehman bankruptcy event transformation
5. **Three-Layer Architecture** - Entity/Event/Risk layers visualized
6. **Query Power** - SPARQL query returning results in <100ms
7. **Scale Metrics** - 429K triples, query speed, storage cost
8. **Business Value** - ROI comparison vs manual analysis

**Duration:** 10-15 minutes walkthrough

---

### **Crisis Timeline Demo** (`crisis_timeline_demo.ipynb`)

**Use Case:** Live presentation showing 2008 crisis traced automatically

**What It Shows:**
1. **View Toggle** - Switch between Graph/Timeline/Triples
2. **Crisis Narrative** - September 2008 key events chronologically:
   - Sept 7: Fannie/Freddie seized
   - Sept 15: Lehman bankruptcy ($613B)
   - Sept 16: AIG bailout ($85B)
   - Sept 19: Treasury guarantees ($3.2T)
3. **Interactive Filtering** - Date range, event types, impact threshold
4. **Connection Explorer** - Click event → See evolution links
5. **Business Framing** - Technical scores → Business explanations

**Duration:** 5-10 minutes demonstration

---

## 🎯 Presentation Tips:

### **For Investors (Business-Focused):**
1. Start with Crisis Timeline Demo
2. Show Timeline View (easy to understand)
3. Click Lehman bankruptcy → Show connections
4. Emphasize: "100ms to find 31 connections"
5. Ask: "How long would your risk team take?"

### **For Technical Due Diligence:**
1. Start with Triple Formation Demo
2. Walk through each cell explaining the process
3. Show SPARQL query live
4. Answer technical questions about data model

### **For Mixed Audience:**
1. Start with Timeline (engage everyone)
2. Then show Triple Formation (explain tech)
3. End with Q&A using both notebooks

---

## 🔧 Troubleshooting:

### **Issue: Jupyter won't start**
```bash
# Reinstall jupyter
pip install --upgrade jupyter notebook
```

### **Issue: AllegroGraph connection fails**
Check your `.env` file has correct credentials:
```
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_CATALOG=mycatalog
AG_REPO=FEEKG
```

### **Issue: Widgets not interactive**
```bash
# Enable widgets
jupyter nbextension enable --py widgetsnbextension
```

### **Issue: Plots not showing**
Run this in first cell of notebook:
```python
%matplotlib inline
```

---

## 📁 File Structure:

```
demos/
├── README_DEMOS.md                  ← This file
├── requirements_demo.txt            ← Python dependencies
├── triple_formation_demo.ipynb      ← Educational demo
├── crisis_timeline_demo.ipynb       ← Presentation demo
├── generate_demo_data.py            ← Extract Sept 2008 subset (if needed)
└── venv_demo/                       ← Virtual environment (created by you)
```

---

## 🎓 Learning Path:

**New to Knowledge Graphs?**
→ Start with `triple_formation_demo.ipynb`

**Preparing for Investor Pitch?**
→ Start with `crisis_timeline_demo.ipynb`

**Want to Build Your Own Demos?**
→ Study both notebooks, copy cells, modify for your use case

---

## 💡 Customization Ideas:

1. **Change Dataset:** Modify SPARQL queries to show Evergrande crisis instead of Lehman
2. **Add More Events:** Expand timeline to March-December 2008 (full crisis)
3. **Different Visualizations:** Use plotly instead of matplotlib for 3D graphs
4. **Export Slides:** Use nbconvert to create PowerPoint from notebooks
5. **Add Your Logo:** Insert your company branding in first cell

---

## 📞 Support:

Questions? Check the main FE-EKG documentation:
- Project README: `/Users/hansonxiong/Desktop/DDP/feekg/README.md`
- CLAUDE.md: Project guide for technical details
- API docs: `api/README.md`

---

**Last Updated:** 2025-11-16
**Version:** 1.0
**Status:** Production Ready
