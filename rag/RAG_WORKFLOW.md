# RAG Integration Workflow

This document outlines the procedure for integrating Retrieval-Augmented Generation (RAG) into the FE-EKG system. This will allow your agents to make decisions based on real-world financial documents rather than just generic model knowledge.

## 1. Data Acquisition (Capital IQ)

Since you have access to Capital IQ and want to improve data quality, we will focus on high-signal documents.

### Recommended Data Strategy
For a research paper on "KG + SLM + ABM", you need data that contains both **events** (what happened) and **reasoning** (why it happened).

**Target Cohort**: Select 5-10 major financial institutions (e.g., JPM, BAC, C, WFC, GS, MS).
**Time Period**: Choose a volatile period (e.g., **2007-2009** for the Great Financial Crisis, or **2022-2023** for the Regional Banking Crisis).

### What to Download (from Document Intelligence)
1.  **Transcripts (High Priority)**:
    *   **Why**: Earnings calls contain direct Q&A between management and analysts. They reveal sentiment, strategy, and defensive posturing.
    *   **Filter**: `Transcripts & Investor Presentations` -> `Earnings Calls`.
2.  **Filings (Medium Priority)**:
    *   **8-K (Current Reports)**: Real-time disclosure of material events (e.g., CEO departure, impairments).
    *   **10-Q (Quarterly Reports)**: specifically the "Management's Discussion and Analysis" (MD&A) section.
    *   **Filter**: `Filings` -> `Current Events` (8-K) and `Annuals and Interims` (10-K/10-Q).

### Export Instructions
1.  In Capital IQ Document Intelligence, select your companies and time range.
2.  Filter for **Transcripts** and **8-Ks**.
3.  **Batch Download**: Download as **PDF** (or Text if available).
4.  Save them in a new folder: `feekg/rag/data/raw/`.

### Option B: User-Provided Dataset (High Value)
You have access to a curated dataset which is excellent for this research:
1.  **JPM Weekly 2002-2009**:
    *   **Value**: **Platinum**. This covers the entire pre-crisis bubble and the crash.
    *   **Use Case**: Primary data source for `BankAgent`. It provides the "Insider/Market" view week-by-week.
2.  **Financial Crisis Enquiry Report 2008.pdf**:
    *   **Value**: **Gold**. This is the definitive post-mortem.
    *   **Use Case**: "Ground Truth" for evaluation. Use this to grade your agents' reasoning (Did they see the risks the report identified?).

---

## 2. RAG Architecture

We will build a **Local RAG Pipeline** to ensure data privacy and speed.

### Technology Stack
*   **Orchestration**: `LangChain` (industry standard for RAG).
*   **Embeddings**: `HuggingFaceEmbeddings` (using `all-MiniLM-L6-v2` - fast and effective).
*   **Vector Store**: `ChromaDB` (local, file-based, no server setup required).
*   **PDF Parsing**: `pypdf` or `unstructured`.

### Pipeline Steps

#### Step 1: Ingestion (`rag/ingest.py`)
1.  **Load**: Read PDF files from `rag/data/raw/`.
2.  **Chunk**: Split text into chunks of ~500 tokens with 50 token overlap.
    *   *Crucial*: Keep metadata (Company Name, Date, Document Type) with each chunk.
3.  **Embed**: Convert text chunks into vector embeddings.
4.  **Store**: Save vectors into `rag/data/chroma_db`.

#### Step 2: Retrieval (`rag/retriever.py`)
1.  **Query**: When an agent needs to decide, generate a query (e.g., *"What is Bank X's liquidity position in Q3 2008?"*).
2.  **Search**: Find top-k most similar chunks in ChromaDB.
3.  **Filter**: Restrict search to the specific agent's company and the current simulation date (to prevent look-ahead bias).

#### Step 3: Generation (Updated `abm/agents.py`)
1.  **Context Injection**: Insert the retrieved chunks into the SLM prompt.
2.  **Reasoning**: The SLM uses the real document excerpts to justify its decision.

---

## 3. Implementation Plan (Week 4)

### Task List
1.  [ ] **Setup**: Install `langchain`, `chromadb`, `sentence-transformers`, `pypdf`.
2.  [ ] **Data**: User uploads Capital IQ PDFs to `rag/data/raw/`.
3.  [ ] **Ingestion Script**: Create `rag/ingest.py` to process PDFs and build the vector DB.
4.  [ ] **Retrieval Interface**: Create `rag/interface.py` for agents to query the DB.
5.  [ ] **Agent Integration**: Modify `BankAgent.decide_action()` to call the retrieval interface.
6.  [ ] **Verification**: Run simulation and verify agents quote the documents.

## 4. Research Value (For your Paper)
This approach allows you to measure:
*   **Alignment**: Do SLM agents make the same decisions as the real banks did?
*   **Information Sensitivity**: How does access to specific documents (e.g., a negative 8-K) change agent behavior?
