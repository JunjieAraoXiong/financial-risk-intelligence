# Capital IQ → FE-EKG Workflow

## TL;DR - Quick Start

```bash
# 1. Download data from Capital IQ (you do this)
# 2. Save to: data/capital_iq_raw/your_file.xlsx
# 3. Process it:
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/your_file.xlsx \
    --filter lehman

# 4. Done! Lehman case study ready in:
#    data/capital_iq_processed/lehman_case_study.json
```

---

## Complete Workflow

### Step 1: Download Bulk Data from Capital IQ

**📖 See detailed guide:** `data/CAPITAL_IQ_DOWNLOAD_GUIDE.md`

**Quick version:**
1. Access Capital IQ via university library
2. Search: Financial Services companies, 2007-2009, All event types
3. Export to Excel or CSV
4. Save to: `data/capital_iq_raw/financial_crisis_2007_2009.xlsx`

**Expected result:**
- 500-2,000 events
- 50-200 MB file
- Columns: company, date, event_type, headline, description

---

### Step 2: Process the Data

**Basic processing (extract Lehman):**
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --filter lehman \
    --output data/capital_iq_processed/lehman_case_study.json
```

**Process all data:**
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --filter all \
    --output data/capital_iq_processed/all_events.json
```

**Filter specific companies:**
```bash
./venv/bin/python ingestion/process_capital_iq.py \
    --input data/capital_iq_raw/financial_crisis_2007_2009.xlsx \
    --companies "Lehman Brothers,Bear Stearns,AIG" \
    --output data/capital_iq_processed/custom_case_study.json
```

---

### Step 3: Load into FE-EKG

**Load into Neo4j:**
```bash
./venv/bin/python ingestion/load_lehman.py
```

**Convert to RDF:**
```bash
./venv/bin/python scripts/demo_rdf_conversion.py
```

---

### Step 4: Generate Visualizations

```bash
# Generate all visualizations
./venv/bin/python scripts/demo_visualizations.py

# View results
open results/three_layer_graph.png
open results/evolution_network.png
```

---

## File Organization

```
data/
├── capital_iq_raw/               # Your downloads from Capital IQ
│   ├── financial_crisis_2007_2009.xlsx  ← You put bulk data here
│   ├── lehman_only.csv           ← Or company-specific exports
│   └── ...
│
├── capital_iq_processed/         # Processed data (auto-generated)
│   ├── lehman_case_study.json    ← Lehman Brothers case study
│   ├── all_events.json           ← All processed events
│   └── ...
│
├── CAPITAL_IQ_DOWNLOAD_GUIDE.md  # Download instructions
└── README_WORKFLOW.md             # This file
```

---

## What the Processing Pipeline Does

### Input (from Capital IQ):
```csv
Company Name,Event Date,Event Type,Headline,Description
"Lehman Brothers Holdings Inc.",2008-09-15,Bankruptcy,Lehman files for bankruptcy,"Lehman Brothers filed for Chapter 11..."
"Bear Stearns",2008-03-14,Acquisition,JPMorgan acquires Bear,"JPMorgan Chase agreed to acquire..."
```

### Output (FE-EKG format):
```json
{
  "events": [
    {
      "eventId": "evt_001",
      "date": "2008-09-15",
      "type": "bankruptcy",
      "actor": "Lehman Brothers Holdings Inc.",
      "headline": "Lehman files for bankruptcy",
      "description": "Lehman Brothers filed for Chapter 11...",
      "entities": ["Lehman Brothers", "Barclays"],
      "source": "Capital IQ"
    }
  ],
  "entities": [...]
}
```

---

## Processing Features

### Automatic Filtering

**By Company:**
```python
# Extracts events mentioning these companies
processor.filter_by_company(['Lehman Brothers', 'AIG'])
```

**By Date Range:**
```python
# Crisis period only
processor.filter_by_date_range('2007-01-01', '2009-12-31')
```

**By Event Type:**
```python
# Critical events only
processor.filter_by_event_type(['Bankruptcy', 'Bailout', 'Credit Downgrade'])
```

### Smart Extraction

**Lehman Case Study** includes:
- Lehman Brothers events
- Bear Stearns (precursor crisis)
- AIG (systemic contagion)
- Related institutions (Merrill Lynch, etc.)

**Automatically:**
- Normalizes event types
- Infers entity types (bank, regulator, etc.)
- Extracts related entities
- Sorts chronologically

---

## Troubleshooting

### Problem: "File not found"

```bash
# Check file exists:
ls -lh data/capital_iq_raw/

# Make sure filename matches:
./venv/bin/python ingestion/process_capital_iq.py --input data/capital_iq_raw/ACTUAL_FILENAME.xlsx
```

### Problem: "No 'company' column found"

The processor adapts to different Capital IQ column names:
- "Company Name" → normalized to "company"
- "Event Date" → normalized to "date"
- "Event Type" → normalized to "event_type"

If you get this warning, check what columns your file actually has:
```python
import pandas as pd
df = pd.read_excel('data/capital_iq_raw/your_file.xlsx')
print(df.columns)
```

### Problem: "Only got 10 events for Lehman"

Possible causes:
1. Company name mismatch: Check if Capital IQ uses "Lehman Brothers Holdings" vs "Lehman Brothers"
2. Date range issue: Events might be outside 2007-2009
3. Small initial download: Try downloading more data

Solution: Manually check your Excel file for Lehman events

### Problem: "Column names don't match"

No problem! The processor handles various Capital IQ export formats. It will normalize:
- "Company Name" or "CompanyName" → "company"
- "Event Date" or "Announcement Date" → "date"
- Etc.

---

## Advanced Usage

### Processing Multiple Files

If you downloaded data in chunks:

```bash
# Process each file
./venv/bin/python ingestion/process_capital_iq.py --input data/capital_iq_raw/2007_events.csv --output data/capital_iq_processed/2007.json
./venv/bin/python ingestion/process_capital_iq.py --input data/capital_iq_raw/2008_events.csv --output data/capital_iq_processed/2008.json
./venv/bin/python ingestion/process_capital_iq.py --input data/capital_iq_raw/2009_events.csv --output data/capital_iq_processed/2009.json

# Then merge them (I'll write a merge script if needed)
```

### Custom Filtering

Edit `ingestion/process_capital_iq.py` to add custom filters:

```python
# Example: Extract only bankruptcy events
def extract_bankruptcies(self):
    return self.filter_by_event_type(['Bankruptcy', 'Chapter 11'])
```

---

## Next Steps After Processing

Once you have `lehman_case_study.json`:

1. **Load into Neo4j**
   ```bash
   ./venv/bin/python ingestion/load_lehman.py
   ```

2. **Convert to RDF**
   ```bash
   ./venv/bin/python scripts/demo_rdf_conversion.py
   ```

3. **Run Evolution Analysis**
   ```bash
   ./venv/bin/python evolution/run_evolution.py
   ```

4. **Generate Visuals**
   ```bash
   ./venv/bin/python scripts/demo_visualizations.py
   ```

5. **Create Presentation**
   - 3 key visuals will be in `results/`
   - Demo notebook in `notebooks/` (to be created)

---

## Summary: What You Need to Do

### Your Tasks:

1. ✅ Access Capital IQ (via university library)
2. ✅ Download bulk data (aim for 500+ events)
   - Companies: Financial institutions
   - Dates: 2007-2009
   - Event types: All
3. ✅ Save to: `data/capital_iq_raw/your_filename.xlsx`
4. ✅ Tell me: "Data ready, filename is X"

### I Do Automatically:

1. ✅ Process your file
2. ✅ Extract Lehman case study
3. ✅ Convert to FE-EKG format
4. ✅ Generate RDF triples
5. ✅ Create visualizations
6. ✅ Prepare presentation materials

---

**Ready when you are!** Just download the data and we'll process it immediately.
