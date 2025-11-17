# Dynamic Knowledge Graph Vision

**Living Knowledge Graph System for FE-EKG**

---

## Table of Contents

1. [Vision Overview](#vision-overview)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [System Architecture](#system-architecture)
5. [Data Ingestion Pipeline](#data-ingestion-pipeline)
6. [Entity Extraction](#entity-extraction)
7. [Smart Deduplication](#smart-deduplication)
8. [Evolution Link Updates](#evolution-link-updates)
9. [RAG Index Refresh](#rag-index-refresh)
10. [ABM Integration](#abm-integration)
11. [Scheduled Processing](#scheduled-processing)
12. [Complete Workflow Example](#complete-workflow-example)
13. [Future Enhancements](#future-enhancements)
14. [Implementation Roadmap](#implementation-roadmap)

---

## Vision Overview

**The Big Idea:** Transform FE-EKG from a static knowledge graph into a **living, continuously learning system** that automatically ingests new financial data, extracts knowledge, and enables AI agents to make better decisions based on the latest information.

### Current State (Static KG)

```
Historical Data (Fixed) → Knowledge Graph → ABM Agents
                                              ↓
                                    Decisions based on old data
```

**Problem:** Once data is loaded, the system is frozen. New events require manual processing.

### Future State (Dynamic KG)

```
Continuous Data Feeds → Auto Extraction → Updated KG → RAG/SLM → ABM Agents
                              ↓                            ↓            ↓
                        Deduplication              Fresh Context   Smart Decisions
```

**Benefit:** System continuously learns from new information without manual intervention.

---

## The Problem

### Current Limitations

1. **Manual Data Loading**
   - Each new dataset requires custom processing script
   - Time-consuming: 1-2 hours per data source
   - Error-prone: Manual entity mapping, risk of duplicates

2. **Static Knowledge**
   - Graph frozen after initial load (5,105 events)
   - Cannot incorporate breaking news or real-time events
   - ABM agents make decisions based on outdated information

3. **No Incremental Updates**
   - Adding 100 new events requires recomputing ALL evolution links
   - Evolution link computation: O(n²) = 13 million pairs (10 minutes)
   - FAISS index: Full rebuild required

4. **Duplicate Entities**
   - "JP Morgan", "JPMorgan Chase", "J.P. Morgan & Co." treated as separate
   - Manual deduplication required
   - Data quality degrades over time

### Real-World Scenario

**Imagine:** You're simulating the 2008 crisis with your ABM. Lehman Brothers files for bankruptcy on September 15, 2008 (in your historical data). But what if you want to add:

- Breaking news from September 16 (AIG bailout)
- SEC filing from September 17 (Merrill Lynch merger)
- Fed announcement on September 18 (emergency rate cut)

**Currently:** You'd need to:
1. Manually create JSON entries
2. Write custom loader script
3. Recompute all evolution links
4. Rebuild FAISS index
5. Restart ABM simulation

**Total time:** ~2-3 hours of manual work

**With Dynamic KG:** Upload → 5 minutes → Done

---

## The Solution

### Automated Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: DATA INGESTION                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   JSON   │  │   CSV    │  │ Web Scrape│                 │
│  │  Upload  │  │  Upload  │  │ (SEC, etc)│                 │
│  └────┬─────┘  └────┬─────┘  └────┬──────┘                 │
│       └─────────────┴─────────────┘                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: NLP EXTRACTION (Rule-Based)                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  spaCy Financial NER                               │    │
│  │  • Entities: Banks, Regulators, Companies          │    │
│  │  • Events: Bankruptcies, Downgrades, Mergers       │    │
│  │  • Relationships: "X acquired Y", "Z defaulted"    │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: SMART DEDUPLICATION                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Name Normalization + Entity Resolution            │    │
│  │  "JP Morgan" ──┐                                   │    │
│  │  "JPMorgan"    ├──→ Canonical: "JPMorgan Chase"   │    │
│  │  "J.P. Morgan" ┘                                   │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 4: INCREMENTAL EVOLUTION LINKS                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Only compute links for NEW events                 │    │
│  │  100 new × 5,105 old = 510K pairs (vs 13M)        │    │
│  │  Speedup: 26x faster (2 sec vs 52 sec)            │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: ALLEGROGRAPH UPDATE                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Insert new triples (entities, events, links)      │    │
│  │  Merge duplicate entities                          │    │
│  │  Update metadata (sources, timestamps)             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 6: FAISS INDEX REFRESH                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Add new event embeddings (incremental)            │    │
│  │  Update vector index for RAG retrieval             │    │
│  │  Background refresh (non-blocking)                 │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 7: ABM STATE REFRESH                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Invalidate agent query caches                     │    │
│  │  Update network topology (if new entities)         │    │
│  │  Notify agents: "New knowledge available"          │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
                    COMPLETE
            ✅ Knowledge Graph Updated
            ✅ RAG Ready with New Context
            ✅ ABM Agents Can Query New Data
```

---

## System Architecture

### Component Integration

```
┌──────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │JSON/CSV  │  │ SEC EDGAR│  │  NewsAPI │  │  GDELT   │   │
│  │ Uploads  │  │ Scraper  │  │  (future)│  │ (future) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        └─────────────┴─────────────┴─────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│              INGESTION & PROCESSING LAYER                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DynamicIngestionPipeline                           │   │
│  │  • Format detection (JSON, CSV, HTML)               │   │
│  │  • Data validation & cleaning                       │   │
│  │  • Batch processing orchestration                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  NLPEntityEventExtractor                            │   │
│  │  • spaCy financial NER                              │   │
│  │  • Custom pattern matching                          │   │
│  │  • Relationship extraction                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  EntityResolver (Deduplication)                     │   │
│  │  • Name normalization                               │   │
│  │  • String similarity matching                       │   │
│  │  • Canonical entity mapping                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  IncrementalEvolutionComputer                       │   │
│  │  • Temporal correlation (TCDI)                      │   │
│  │  • Entity overlap (Jaccard)                         │   │
│  │  • 6 evolution algorithms                           │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────────┐
│                  STORAGE LAYER                               │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  AllegroGraph    │         │  FAISS Index     │         │
│  │                  │         │                  │         │
│  │  • 5,105 events  │         │  • 5,105 vectors │         │
│  │  • 31K evo links │         │  • 2048-dim      │         │
│  │  • 429K triples  │         │  • 40MB size     │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
└───────────┼──────────────────────────────┼──────────────────┘
            └──────────────┬───────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│                  QUERY & REASONING LAYER                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RAG System (FAISS + AllegroGraph)                  │   │
│  │  • Hybrid retrieval (semantic + temporal)           │   │
│  │  • Context augmentation for SLM                     │   │
│  │  • Query caching (3-tier)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SLM (Llama-3.2-1B) - Week 3                        │   │
│  │  • Agent decision-making                            │   │
│  │  • Historical context reasoning                     │   │
│  │  • Natural language queries                         │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────────┐
│                  SIMULATION LAYER (ABM)                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  BankAgent   │  │ RegulatorAgent│  │ MarketAgent  │     │
│  │              │  │               │  │              │     │
│  │ Queries KG   │  │ Queries KG    │  │ Queries KG   │     │
│  │ for context  │  │ for context   │  │ for context  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Decision Flow:                                              │
│  1. Agent observes state (capital, liquidity, VIX)           │
│  2. Query KG: "What happened in similar situations?"         │
│  3. SLM reasons: "Historical analogs → Best action"          │
│  4. Agent acts: DEFENSIVE / MAINTAIN / AGGRESSIVE            │
│  5. Simulation evolves based on collective decisions         │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Ingestion Pipeline

### Supported Formats

#### 1. JSON Upload (Existing Format)

**Use Case:** Direct upload of processed data (Capital IQ, manual entries)

**Example Input:**
```json
{
  "entities": [
    {
      "entityId": "ent_jpmorgan",
      "name": "JPMorgan Chase",
      "type": "bank",
      "sector": "financial_services"
    }
  ],
  "events": [
    {
      "eventId": "evt_lehman_bankruptcy",
      "type": "bankruptcy",
      "date": "2008-09-15",
      "description": "Lehman Brothers files for Chapter 11 bankruptcy",
      "entities": ["ent_lehman"],
      "severity": "critical"
    }
  ]
}
```

**Processing:**
- Validate JSON schema
- Extract entities and events
- Direct insertion (minimal processing)
- **Time:** ~5 seconds for 100 events

#### 2. CSV Upload

**Use Case:** Tabular financial data (event logs, timeline data)

**Example Input:**
```csv
date,entity,event_type,description,severity
2008-09-15,Lehman Brothers,bankruptcy,Filed Chapter 11,critical
2008-09-16,AIG,government_intervention,Fed provides $85B loan,high
2008-09-18,Federal Reserve,policy_change,Emergency rate cut to 2%,medium
```

**Processing:**
- Parse CSV with pandas
- Map columns to entity/event schema
- Extract relationships from description field
- **Time:** ~10 seconds for 100 events

#### 3. Web Scraping (SEC EDGAR)

**Use Case:** Automated collection of regulatory filings

**Target Sites:**
- SEC EDGAR (https://www.sec.gov/edgar/)
- Company 8-K filings (material events)
- 10-Q/10-K reports (quarterly/annual)

**Example Code:**
```python
# ingestion/sec_scraper.py

import requests
from bs4 import BeautifulSoup
import re

class SECFilingScraper:
    """
    Scrape SEC EDGAR for financial events

    Usage:
        scraper = SECFilingScraper()
        events = scraper.get_company_filings(
            ticker='LEH',  # Lehman Brothers
            form_type='8-K',
            start_date='2008-01-01',
            end_date='2008-12-31'
        )
    """

    BASE_URL = 'https://www.sec.gov/cgi-bin/browse-edgar'

    def get_company_filings(self, ticker, form_type, start_date, end_date):
        """
        Fetch filings for a company

        Returns:
            List of filing dicts with text content
        """
        # Build URL
        params = {
            'action': 'getcompany',
            'CIK': ticker,
            'type': form_type,
            'dateb': end_date,
            'datea': start_date,
            'count': 100
        }

        response = requests.get(self.BASE_URL, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')

        filings = []
        for row in soup.find_all('tr'):
            # Extract filing date, document link
            filing_date = self.extract_date(row)
            document_url = self.extract_document_link(row)

            if document_url:
                # Fetch document text
                doc_text = self.fetch_document_text(document_url)

                filings.append({
                    'date': filing_date,
                    'type': form_type,
                    'source': document_url,
                    'text': doc_text
                })

        return filings

    def fetch_document_text(self, url):
        """Extract text from filing document"""
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script/style tags
        for tag in soup(['script', 'style']):
            tag.decompose()

        return soup.get_text()
```

**Processing Flow:**
1. Scrape SEC EDGAR for 8-K filings (material events)
2. Extract filing date, company, event type
3. Parse text for key information (NLP extraction)
4. Create event entries
5. **Time:** ~2-5 seconds per filing (rate-limited by SEC)

**Legal Compliance:**
- SEC allows programmatic access (Fair Access policy)
- Must include User-Agent header
- Rate limit: 10 requests/second
- Reference: https://www.sec.gov/os/accessing-edgar-data

---

## Entity Extraction

### Rule-Based NLP with spaCy

**Strategy:** Fast, reliable extraction using pattern matching + named entity recognition

#### Installation

```bash
pip install spacy
python -m spacy download en_core_web_trf  # Transformer-based model
```

#### Custom Financial Patterns

```python
# ingestion/nlp_extractor.py

import spacy
from spacy.matcher import Matcher
import re

class FinancialNERExtractor:
    """
    Extract financial entities and events using spaCy

    Entities:
    - Banks, investment banks, insurance companies
    - Regulators (Fed, SEC, Treasury)
    - Rating agencies (Moody's, S&P, Fitch)

    Events:
    - Bankruptcies, defaults, downgrades
    - Mergers, acquisitions
    - Government interventions
    """

    def __init__(self):
        # Load transformer-based model (95% accuracy)
        self.nlp = spacy.load("en_core_web_trf")

        # Custom matcher for financial terms
        self.matcher = Matcher(self.nlp.vocab)

        # Define patterns
        self.add_financial_patterns()

        # Entity type mapping
        self.entity_types = {
            'bank': ['bank', 'banking', 'financial institution'],
            'regulator': ['federal reserve', 'sec', 'treasury', 'fdic'],
            'rating_agency': ["moody's", 'standard & poor', 'fitch']
        }

        # Event type patterns
        self.event_patterns = {
            'bankruptcy': r'\b(bankruptcy|chapter 11|insolvent)\b',
            'default': r'\b(default|missed payment|failed to pay)\b',
            'downgrade': r'\b(downgrade|rating cut|lowered rating)\b',
            'merger': r'\b(merger|acquisition|acquired|bought)\b',
            'bailout': r'\b(bailout|rescue|emergency loan|government intervention)\b'
        }

    def add_financial_patterns(self):
        """Add custom patterns for financial entities"""

        # Pattern: "Bank of America", "JPMorgan Chase Bank"
        bank_pattern = [
            {"LOWER": {"IN": ["bank", "banking"]}},
            {"POS": "ADP", "OP": "?"},
            {"POS": "PROPN", "OP": "+"}
        ]
        self.matcher.add("BANK", [bank_pattern])

        # Pattern: "Federal Reserve", "SEC"
        regulator_pattern = [
            {"LOWER": {"IN": ["federal", "reserve", "sec", "treasury", "fdic"]}}
        ]
        self.matcher.add("REGULATOR", [regulator_pattern])

    def extract_from_text(self, text: str, source: str = 'unknown') -> dict:
        """
        Extract entities and events from text

        Args:
            text: Raw text to process
            source: Source identifier (URL, filename)

        Returns:
            {
                'entities': [...],
                'events': [...],
                'relationships': [...]
            }
        """
        doc = self.nlp(text)

        # Extract entities
        entities = []
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE']:
                entity_type = self.classify_entity(ent.text)
                if entity_type:
                    entities.append({
                        'name': ent.text,
                        'type': entity_type,
                        'span': (ent.start_char, ent.end_char),
                        'confidence': 0.90
                    })

        # Extract events
        events = []
        for event_type, pattern in self.event_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Find sentence containing match
                sentence = self.get_sentence_containing(doc, match.start())

                # Extract event details
                event = self.extract_event_details(
                    sentence,
                    event_type,
                    entities
                )

                if event:
                    events.append(event)

        # Extract relationships
        relationships = self.extract_relationships(doc, entities)

        return {
            'entities': self.deduplicate_entities(entities),
            'events': events,
            'relationships': relationships
        }

    def classify_entity(self, name: str) -> str:
        """Classify entity type based on keywords"""
        name_lower = name.lower()

        for entity_type, keywords in self.entity_types.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return entity_type

        # Default: check if it's a financial company
        if any(word in name_lower for word in ['bank', 'financial', 'capital']):
            return 'bank'

        return 'company'

    def extract_event_details(self, sentence, event_type, entities):
        """
        Extract event details from sentence

        Example:
            "Lehman Brothers filed for bankruptcy on September 15, 2008"
            → {
                'type': 'bankruptcy',
                'actor': 'Lehman Brothers',
                'date': '2008-09-15',
                'description': '...'
              }
        """
        doc = self.nlp(sentence.text)

        # Extract date
        dates = [ent.text for ent in doc.ents if ent.label_ == 'DATE']
        event_date = self.parse_date(dates[0]) if dates else None

        # Find actor (entity mentioned in sentence)
        actor = None
        for entity in entities:
            if entity['name'] in sentence.text:
                actor = entity['name']
                break

        if not actor:
            return None

        return {
            'type': event_type,
            'date': event_date,
            'actor': actor,
            'description': sentence.text.strip(),
            'confidence': 0.85
        }

    def extract_relationships(self, doc, entities):
        """
        Extract relationships between entities

        Example: "JPMorgan acquired Bear Stearns"
        → ('JPMorgan', 'acquired', 'Bear Stearns')
        """
        relationships = []

        # Look for verb patterns between entities
        for token in doc:
            if token.pos_ == 'VERB':
                # Find entities before and after verb
                subjects = [ent for ent in entities if ent['span'][1] < token.idx]
                objects = [ent for ent in entities if ent['span'][0] > token.idx]

                if subjects and objects:
                    relationships.append({
                        'subject': subjects[-1]['name'],
                        'predicate': token.lemma_,
                        'object': objects[0]['name']
                    })

        return relationships

    def parse_date(self, date_str: str) -> str:
        """
        Parse date string to YYYY-MM-DD format

        Examples:
            "September 15, 2008" → "2008-09-15"
            "Sep 15 2008" → "2008-09-15"
            "9/15/2008" → "2008-09-15"
        """
        from dateutil import parser
        try:
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
```

**Accuracy Benchmarks:**

| Task | spaCy Accuracy | Notes |
|------|---------------|-------|
| Entity recognition | 92% | Transformers model (en_core_web_trf) |
| Entity typing | 85% | Rule-based classification |
| Event detection | 80% | Regex patterns |
| Date extraction | 95% | Built-in DATE entity |
| Relationship extraction | 70% | Dependency parsing |

---

## Smart Deduplication

### The Challenge

Financial data has many entity name variations:

- **Official names:** "JPMorgan Chase & Co."
- **Common names:** "JPMorgan", "JP Morgan"
- **Abbreviations:** "JPM"
- **Historical names:** "J.P. Morgan & Co." (pre-merger)

**Problem:** Without deduplication, these create 4 separate entities in the graph.

### Solution: Entity Resolution Pipeline

#### Step 1: Name Normalization

```python
# ingestion/entity_resolver.py

import re
from difflib import SequenceMatcher

class EntityResolver:
    """
    Resolve entity name variations to canonical forms

    Strategy:
    1. Normalize names (lowercase, remove punctuation)
    2. String similarity matching (Levenshtein distance)
    3. Manual canonical mapping (for known entities)
    4. Maintain alias list for future lookups
    """

    def __init__(self, graph_backend):
        self.graph = graph_backend

        # Cache: normalized_name → canonical_id
        self.cache = {}

        # Known canonical mappings (financial institutions)
        self.canonical_map = {
            'jpmorgan': 'JPMorgan Chase',
            'jp morgan': 'JPMorgan Chase',
            'jpm': 'JPMorgan Chase',
            'chase': 'JPMorgan Chase',

            'bank of america': 'Bank of America',
            'bofa': 'Bank of America',
            'boa': 'Bank of America',

            'lehman': 'Lehman Brothers',
            'lehman bros': 'Lehman Brothers',

            'aig': 'American International Group',
            'american international': 'American International Group',

            'goldman': 'Goldman Sachs',
            'gs': 'Goldman Sachs',
        }

        # Preload existing entities into cache
        self.load_existing_entities()

    def normalize_name(self, name: str) -> str:
        """
        Normalize entity name for comparison

        Transformations:
        - Lowercase
        - Remove punctuation (., &, -)
        - Remove legal suffixes (Inc., Corp., LLC)
        - Trim whitespace
        """
        normalized = name.lower()

        # Remove legal suffixes
        suffixes = [
            r'\binc\.?$', r'\bcorp\.?$', r'\bllc\.?$',
            r'\bltd\.?$', r'\bco\.?$', r'\b& co\.?$'
        ]
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)

        # Remove punctuation
        normalized = re.sub(r'[.,&\-]', ' ', normalized)

        # Collapse whitespace
        normalized = ' '.join(normalized.split())

        return normalized.strip()

    def resolve_entity(self, name: str, entity_type: str = 'company') -> str:
        """
        Resolve entity name to canonical ID

        Args:
            name: Entity name as it appears in text
            entity_type: Type hint (bank, regulator, etc.)

        Returns:
            canonical_id: Existing entity ID or new ID

        Example:
            resolve_entity("JP Morgan") → "ent_jpmorgan_chase"
            resolve_entity("JPMorgan Chase") → "ent_jpmorgan_chase"  (same)
        """
        normalized = self.normalize_name(name)

        # Step 1: Check cache
        if normalized in self.cache:
            return self.cache[normalized]

        # Step 2: Check canonical map
        if normalized in self.canonical_map:
            canonical_name = self.canonical_map[normalized]
            entity_id = self.get_or_create_entity(canonical_name, entity_type)
            self.cache[normalized] = entity_id
            return entity_id

        # Step 3: String similarity search
        similar_entity = self.find_similar_entity(normalized, threshold=0.85)
        if similar_entity:
            # Match found - add as alias
            self.cache[normalized] = similar_entity['id']
            self.add_alias(similar_entity['id'], name)
            return similar_entity['id']

        # Step 4: Create new entity
        entity_id = self.get_or_create_entity(name, entity_type)
        self.cache[normalized] = entity_id
        return entity_id

    def find_similar_entity(self, normalized_name: str, threshold=0.85):
        """
        Find existing entity with similar name

        Uses Levenshtein distance (sequence matching)
        """
        existing_entities = self.graph.get_all_entities()

        best_match = None
        best_score = 0.0

        for entity in existing_entities:
            entity_norm = self.normalize_name(entity['name'])

            # Compute similarity
            similarity = SequenceMatcher(None, normalized_name, entity_norm).ratio()

            if similarity > best_score:
                best_score = similarity
                best_match = entity

        if best_score >= threshold:
            return best_match

        return None

    def get_or_create_entity(self, name: str, entity_type: str) -> str:
        """
        Get existing entity or create new one
        """
        # Check if entity exists
        existing = self.graph.find_entity_by_name(name)
        if existing:
            return existing['id']

        # Create new entity
        entity_id = f"ent_{self.normalize_name(name).replace(' ', '_')}"

        self.graph.create_entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            aliases=[]
        )

        return entity_id

    def add_alias(self, entity_id: str, alias: str):
        """
        Add alias to existing entity

        Example:
            Entity: "JPMorgan Chase" (ent_jpmorgan_chase)
            Aliases: ["JP Morgan", "JPM", "Chase"]
        """
        self.graph.add_entity_alias(entity_id, alias)
```

#### Step 2: Deduplication Report

After processing, generate report on duplicates found:

```
Deduplication Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Entities processed: 156
New entities: 22
Duplicates merged: 134 (85.9%)

Top Merged Entities:
  1. JPMorgan Chase (14 variations)
     - "JP Morgan", "JPMorgan", "JPM", "Chase", ...

  2. Bank of America (11 variations)
     - "BofA", "BoA", "Bank of America Corp.", ...

  3. Lehman Brothers (8 variations)
     - "Lehman", "Lehman Bros", "Lehman Brothers Holdings", ...

Manual Review Required:
  • "Merrill Lynch" vs "Merrill Lynch Bank of America"
    (Post-acquisition naming - need temporal context)
```

---

## Evolution Link Updates

### Incremental Computation Strategy

**Problem:** Computing evolution links is O(n²):
- 5,105 events × 5,104 / 2 = **13,021,620 pairs**
- At 100 comparisons/second = **36 hours**

**Solution:** Only compute links for NEW events:

```python
# evolution/incremental_evolution.py

from evolution.methods import EventEvolutionScorer

class IncrementalEvolutionComputer:
    """
    Compute evolution links incrementally for new events

    Key Optimization: Only compare new events against existing events

    Complexity:
    - Old: O(n²) = 13M comparisons
    - New: O(n_new × n_total) = 510K comparisons (26x faster)
    """

    def __init__(self, graph_backend):
        self.graph = graph_backend
        self.scorer = EventEvolutionScorer()

    def compute_new_links(self, new_events: list, threshold=0.5):
        """
        Compute evolution links for newly added events

        Args:
            new_events: List of new event dicts
            threshold: Minimum score to create link (default: 0.5)

        Returns:
            List of evolution link dicts
        """
        # Fetch all existing events (includes old + new)
        all_events = self.graph.get_all_events()
        existing_events = [e for e in all_events if e not in new_events]

        print(f"\n🔗 Computing evolution links...")
        print(f"   New events: {len(new_events)}")
        print(f"   Existing events: {len(existing_events)}")
        print(f"   Comparisons: {len(new_events) * len(all_events):,}")

        new_links = []

        # Compare each new event against ALL events
        for new_evt in new_events:
            # Compare against existing events
            for other_evt in all_events:
                # Skip self-comparison
                if new_evt['eventId'] == other_evt['eventId']:
                    continue

                # Ensure temporal ordering (source before target)
                if other_evt['date'] >= new_evt['date']:
                    continue

                # Compute evolution score
                score, components = self.scorer.compute_evolution_score(
                    other_evt, new_evt
                )

                # Create link if above threshold
                if score >= threshold:
                    new_links.append({
                        'source': other_evt['eventId'],
                        'target': new_evt['eventId'],
                        'score': score,
                        'temporal': components.get('temporal', 0.0),
                        'entity_overlap': components.get('entity_overlap', 0.0),
                        'semantic': components.get('semantic', 0.0),
                        'topic': components.get('topic', 0.0),
                        'causality': components.get('causality', 0.0),
                        'emotional': components.get('emotional', 0.0)
                    })

        print(f"   ✅ Created {len(new_links)} evolution links")
        print(f"   Avg score: {sum(l['score'] for l in new_links) / len(new_links):.3f}" if new_links else "")

        return new_links

    def compute_with_temporal_window(self, new_events, window_days=365, threshold=0.5):
        """
        Further optimization: Only compare events within temporal window

        Rationale: Events 5+ years apart unlikely to have evolution links

        Example:
            New event: 2008-09-15 (Lehman bankruptcy)
            Window: ±1 year
            Only compare against events from 2007-09-15 to 2009-09-15

        Speedup: 10-50x depending on dataset timespan
        """
        from datetime import datetime, timedelta

        # Find date range of new events
        new_dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in new_events]
        min_date = min(new_dates) - timedelta(days=window_days)
        max_date = max(new_dates) + timedelta(days=window_days)

        # Fetch only events within window
        relevant_events = self.graph.get_events_in_range(
            start_date=min_date.strftime('%Y-%m-%d'),
            end_date=max_date.strftime('%Y-%m-%d')
        )

        print(f"   Temporal window: {min_date.date()} to {max_date.date()}")
        print(f"   Relevant events: {len(relevant_events)} (vs {self.graph.count_events()} total)")

        # Now compute links only within window
        # ... (same logic as above, but with relevant_events instead of all_events)
```

**Performance Comparison:**

| Scenario | Events | Full Computation | Incremental | Windowed | Speedup |
|----------|--------|-----------------|-------------|----------|---------|
| +100 new | 5,205 | 13.5M pairs (36 hrs) | 520K pairs (1.4 hrs) | 50K pairs (8 min) | **270x** |
| +1,000 new | 6,105 | 18.6M pairs (52 hrs) | 6.1M pairs (17 hrs) | 600K pairs (1.7 hrs) | **30x** |

---

## RAG Index Refresh

### FAISS Incremental Updates

**Goal:** Add new event embeddings without rebuilding entire index

```python
# rag/faiss_manager.py

import faiss
import numpy as np
import pickle
import os

class FAISSIndexManager:
    """
    Manage FAISS vector index with incremental updates

    Features:
    - Add new embeddings (O(n) operation)
    - Persist to disk
    - Fast similarity search (<10ms)
    """

    def __init__(self, dimension=2048, index_path='data/faiss/event_embeddings.faiss'):
        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = index_path.replace('.faiss', '_metadata.pkl')

        # Create directories if needed
        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        # Load or create index
        if os.path.exists(index_path):
            print(f"📂 Loading existing FAISS index from {index_path}")
            self.index = faiss.read_index(index_path)

            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)

            print(f"   ✅ Loaded {self.index.ntotal:,} event embeddings")
        else:
            print(f"🆕 Creating new FAISS index")
            # Use IndexFlatIP for inner product similarity (cosine similarity)
            self.index = faiss.IndexFlatIP(dimension)
            self.metadata = []  # List of event IDs

    def add_events(self, event_ids: list, embeddings: list):
        """
        Add new events to index (incremental)

        Args:
            event_ids: ['evt_new_001', 'evt_new_002', ...]
            embeddings: List of 2048-dim numpy arrays

        Time complexity: O(n) where n = number of new events
        """
        if not event_ids:
            return

        # Convert to numpy array (float32 required by FAISS)
        embedding_matrix = np.array(embeddings).astype('float32')

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embedding_matrix)

        # Add to index
        self.index.add(embedding_matrix)

        # Update metadata
        self.metadata.extend(event_ids)

        # Persist to disk
        self.save()

        print(f"✅ Added {len(event_ids)} events to FAISS index")
        print(f"   Total events in index: {self.index.ntotal:,}")

    def search(self, query_embedding: np.ndarray, top_k=10):
        """
        Search for similar events

        Args:
            query_embedding: 2048-dim numpy array
            top_k: Number of results to return

        Returns:
            List of (event_id, similarity_score) tuples
        """
        # Normalize query vector
        query_vec = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vec)

        # Search
        similarities, indices = self.index.search(query_vec, k=top_k)

        # Map indices to event IDs
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx < len(self.metadata):  # Safety check
                event_id = self.metadata[idx]
                results.append((event_id, float(sim)))

        return results

    def save(self):
        """Persist index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)

        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def get_stats(self):
        """Return index statistics"""
        index_size_mb = os.path.getsize(self.index_path) / 1024 / 1024 if os.path.exists(self.index_path) else 0

        return {
            'total_events': self.index.ntotal,
            'dimension': self.dimension,
            'index_size_mb': round(index_size_mb, 2),
            'metadata_count': len(self.metadata)
        }
```

**Usage Example:**

```python
# Generate embeddings for new events
from llm.embedding_client import EmbeddingClient

embedding_client = EmbeddingClient()
faiss_manager = FAISSIndexManager()

new_events = [...]  # List of new event dicts
event_ids = [e['eventId'] for e in new_events]
descriptions = [e['description'] for e in new_events]

# Generate embeddings (batch processing)
embeddings = embedding_client.generate_embeddings(descriptions)

# Add to FAISS
faiss_manager.add_events(event_ids, embeddings)
```

**Performance:**
- Add 100 events: ~50ms (FAISS add is very fast)
- Search: <10ms (even with 10,000+ events)
- Memory: ~8KB per event (2048 float32s)
- Disk: ~40MB for 5,000 events

---

## ABM Integration

### How Agents Query Updated KG

**Vision:** ABM agents make decisions based on **real-time KG context**

#### Enhanced BankAgent with KG Queries

```python
# abm/agents_enhanced.py

from abm.agents import BankAgent

class KGAwareBankAgent(BankAgent):
    """
    Enhanced BankAgent that queries knowledge graph for context

    New Capabilities:
    - Query historical analogies via RAG
    - Analyze outcomes of similar situations
    - Make decisions based on precedents
    """

    def __init__(self, model, unique_id, name, entity_id, **kwargs):
        super().__init__(model, unique_id, name, entity_id, **kwargs)

        # NEW: Query interfaces
        self.kg_query = model.kg_query_interface
        self.rag_retriever = model.rag_retriever
        self.query_cache = {}  # Cache queries for performance

    def get_situation_context(self) -> dict:
        """
        Get context with historical analogies (ENHANCED)
        """
        # 1. Base context (existing)
        base_context = {
            'capital': self.capital,
            'liquidity': self.liquidity,
            'leverage_ratio': self.leverage_ratio,
            'liquidity_ratio': self.liquidity_ratio,
            'risk_score': self.risk_score,
            'market_vix': self.model.market_agent.vix,
            'market_ted_spread': self.model.market_agent.ted_spread,
            'n_failed_banks': len(self.model.failed_banks),
            'crisis_intensity': self.model.crisis_intensity
        }

        # 2. Query KG for historical analogies (NEW)
        query_text = f"""
        Historical situations similar to:
        - Entity type: {self.get_entity_type()}
        - Leverage ratio: {self.leverage_ratio:.1f}x
        - Liquidity crisis: {self.liquidity_ratio < 0.2}
        - Market stress: VIX {self.model.market_agent.vix}
        - Failed banks: {len(self.model.failed_banks)}
        """

        # Check cache first
        cache_key = f"{self.risk_score:.2f}_{self.model.market_agent.vix:.1f}"
        if cache_key in self.query_cache:
            historical_context = self.query_cache[cache_key]
        else:
            # RAG retrieval (semantic search)
            similar_events = self.rag_retriever.retrieve(
                query=query_text,
                entity_filter=[self.entity_id],  # Focus on this entity's history
                top_k=5
            )

            # Analyze what happened next in those situations
            historical_context = self.analyze_historical_outcomes(similar_events)

            # Cache result
            self.query_cache[cache_key] = historical_context

        # 3. Merge contexts
        base_context['historical_context'] = historical_context

        return base_context

    def analyze_historical_outcomes(self, similar_events):
        """
        Analyze outcomes of similar historical events

        Query: "What happened after these events?"

        Returns:
            {
                'avg_failure_rate': 0.6,
                'avg_days_to_failure': 45,
                'successful_strategies': ['DEFENSIVE', ...],
                'failed_strategies': ['AGGRESSIVE', ...]
            }
        """
        outcomes = []

        for event in similar_events:
            # Query graph: What happened next?
            sparql = f"""
            PREFIX feekg: <http://feekg.org/ontology#>

            SELECT ?next_event ?next_type ?days_diff ?severity
            WHERE {{
                <{event['event_id']}> feekg:evolvesTo ?next_event .
                ?next_event feekg:eventType ?next_type .
                ?next_event feekg:date ?next_date .
                ?next_event feekg:severity ?severity .

                BIND((xsd:date(?next_date) - xsd:date("{event['date']}")) AS ?days_diff)
            }}
            ORDER BY ?days_diff
            LIMIT 5
            """

            next_events = self.kg_query.execute_sparql(sparql)

            # Classify outcome
            outcome = self.classify_outcome(next_events)
            outcomes.append(outcome)

        # Aggregate
        if not outcomes:
            return {'confidence': 0.0}

        return {
            'avg_failure_rate': sum(o['failed'] for o in outcomes) / len(outcomes),
            'avg_days_to_event': np.mean([o['days_to_event'] for o in outcomes]),
            'confidence': len(outcomes) / 5.0,  # More examples = higher confidence
            'precedents': similar_events
        }

    def classify_outcome(self, next_events):
        """
        Classify whether outcome was failure or success
        """
        failure_types = ['bankruptcy', 'default', 'downgrade']

        for evt in next_events:
            if evt['next_type'] in failure_types:
                return {
                    'failed': True,
                    'days_to_event': evt['days_diff'],
                    'event_type': evt['next_type']
                }

        return {'failed': False, 'days_to_event': 365}

    def decide_action(self, context: dict) -> str:
        """
        Make decision using historical context (ENHANCED)

        Logic:
        - If historical failure rate > 60% → DEFENSIVE
        - If historical data shows DEFENSIVE succeeded → DEFENSIVE
        - Otherwise, use existing rule-based logic
        """
        historical = context.get('historical_context', {})

        # Check historical precedent
        if historical.get('confidence', 0) > 0.5:
            failure_rate = historical.get('avg_failure_rate', 0)

            if failure_rate > 0.6:
                print(f"   📊 {self.name}: Historical data shows {failure_rate:.0%} failure rate → Going DEFENSIVE")
                return 'DEFENSIVE'

        # Fallback to existing logic
        return super().decide_action(context)
```

#### Query Caching for Performance

**Problem:** 100 agents × 100 steps = 10,000 KG queries
- If each query takes 200ms = **33 minutes simulation time**

**Solution:** 3-tier caching

```python
# abm/kg_cache_manager.py

from functools import lru_cache
import hashlib

class KGCacheManager:
    """
    Three-tier caching for ABM KG queries

    Tier 1: Agent cache (agent's own history, 100% hit rate)
    Tier 2: Model cache (shared across agents, 80% hit rate)
    Tier 3: Actual KG query (20% hit rate, 200ms)

    Average latency: 0.8 × 5ms + 0.2 × 200ms = 44ms
    """

    def __init__(self, rag_retriever):
        self.rag = rag_retriever

        # Tier 1: Per-agent caches
        self.agent_caches = {}  # agent_id -> {query_hash -> result}

        # Tier 2: Model-level shared cache
        self.model_cache = {}  # query_hash -> result
        self.cache_size_limit = 1000

    def query_with_cache(self, query: str, agent_id: str, **kwargs):
        """
        Execute query with 3-tier caching
        """
        # Generate cache key from query + parameters
        cache_key = self.generate_cache_key(query, kwargs)

        # Tier 1: Agent-specific cache
        if agent_id in self.agent_caches:
            if cache_key in self.agent_caches[agent_id]:
                return self.agent_caches[agent_id][cache_key]

        # Tier 2: Model-level cache
        if cache_key in self.model_cache:
            return self.model_cache[cache_key]

        # Tier 3: Actual query (cache miss)
        result = self.rag.retrieve(query, **kwargs)

        # Update caches
        if agent_id not in self.agent_caches:
            self.agent_caches[agent_id] = {}

        self.agent_caches[agent_id][cache_key] = result
        self.model_cache[cache_key] = result

        # Evict oldest if cache full
        if len(self.model_cache) > self.cache_size_limit:
            oldest = next(iter(self.model_cache))
            del self.model_cache[oldest]

        return result

    def generate_cache_key(self, query: str, params: dict) -> str:
        """Generate hash key for caching"""
        key_string = f"{query}_{params.get('risk_score', 0):.2f}_{params.get('vix', 0):.1f}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def invalidate_all(self):
        """Clear all caches (called after KG update)"""
        self.agent_caches = {}
        self.model_cache = {}
        print("✅ ABM query caches invalidated")
```

**Performance with Caching:**
- 10,000 queries
- 80% cache hit rate → 8,000 × 5ms = 40 seconds
- 20% cache miss → 2,000 × 200ms = 400 seconds
- **Total: 7.3 minutes** (vs 33 minutes without caching)

---

## Scheduled Processing

### Automated Batch Updates

**Goal:** Run update pipeline daily at 2am without manual intervention

#### Using APScheduler

```python
# ingestion/scheduled_updater.py

from apscheduler.schedulers.background import BackgroundScheduler
from ingestion.update_orchestrator import KGUpdateOrchestrator
import os
from datetime import datetime

class ScheduledKGUpdater:
    """
    Automated scheduled updates for knowledge graph

    Schedule:
    - Daily at 2:00 AM: Process new data uploads
    - Logs results to file
    - Email notifications on errors
    """

    def __init__(self, data_dir='data/uploads/', log_dir='logs/'):
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.orchestrator = KGUpdateOrchestrator()

        # Create directories
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        # Initialize scheduler
        self.scheduler = BackgroundScheduler()

    def start(self):
        """
        Start scheduled updates

        Schedule:
        - Daily at 2:00 AM
        - Monday-Friday only (optional)
        """
        # Daily update job
        self.scheduler.add_job(
            self.run_daily_update,
            'cron',
            hour=2,
            minute=0,
            # day_of_week='mon-fri',  # Uncomment for weekdays only
            id='daily_kg_update'
        )

        self.scheduler.start()
        print("✅ Scheduled updater started")
        print(f"   Next run: {self.scheduler.get_job('daily_kg_update').next_run_time}")

    def run_daily_update(self):
        """
        Execute daily update pipeline

        Process:
        1. Scan uploads directory for new files
        2. Process each file
        3. Log results
        4. Move processed files to archive
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = os.path.join(self.log_dir, f'update_{timestamp}.log')

        print(f"\n{'='*70}")
        print(f"  Daily KG Update - {timestamp}")
        print(f"{'='*70}\n")

        # Find new files
        new_files = self.find_new_files()

        if not new_files:
            print("ℹ️  No new files to process")
            return

        print(f"📁 Found {len(new_files)} new files")

        # Process each file
        reports = []
        errors = []

        for file_path in new_files:
            try:
                print(f"\n📄 Processing: {os.path.basename(file_path)}")

                report = self.orchestrator.process_new_data(file_path)
                reports.append(report)

                # Move to archive
                self.archive_file(file_path, timestamp)

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                errors.append({'file': file_path, 'error': str(e)})

        # Generate summary report
        self.write_summary_report(log_file, reports, errors)

        # Send notifications if errors
        if errors:
            self.send_error_notification(errors)

        print(f"\n✅ Daily update complete")
        print(f"   Processed: {len(reports)} files")
        print(f"   Errors: {len(errors)}")
        print(f"   Log: {log_file}")

    def find_new_files(self):
        """
        Find new files in uploads directory

        Supported formats: .json, .csv
        """
        new_files = []

        for filename in os.listdir(self.data_dir):
            if filename.endswith(('.json', '.csv')):
                file_path = os.path.join(self.data_dir, filename)
                new_files.append(file_path)

        return new_files

    def archive_file(self, file_path, timestamp):
        """Move processed file to archive"""
        archive_dir = os.path.join(self.data_dir, 'archive', timestamp)
        os.makedirs(archive_dir, exist_ok=True)

        filename = os.path.basename(file_path)
        archive_path = os.path.join(archive_dir, filename)

        os.rename(file_path, archive_path)

    def write_summary_report(self, log_file, reports, errors):
        """Write summary to log file"""
        with open(log_file, 'w') as f:
            f.write("Daily KG Update Report\n")
            f.write("=" * 70 + "\n\n")

            # Summary stats
            total_entities = sum(r.entities_new for r in reports)
            total_events = sum(r.events_new for r in reports)
            total_links = sum(r.links_new for r in reports)

            f.write(f"Files processed: {len(reports)}\n")
            f.write(f"Total new entities: {total_entities}\n")
            f.write(f"Total new events: {total_events}\n")
            f.write(f"Total new evolution links: {total_links}\n\n")

            # Individual file reports
            for report in reports:
                f.write(f"\nFile: {report.file_path}\n")
                f.write(report.summary() + "\n")

            # Errors
            if errors:
                f.write("\n\nERRORS:\n")
                for err in errors:
                    f.write(f"  {err['file']}: {err['error']}\n")

    def send_error_notification(self, errors):
        """Send email notification on errors (optional)"""
        # TODO: Implement email notification
        pass

    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
```

#### Usage

```python
# Start scheduled updater (run once at application startup)
from ingestion.scheduled_updater import ScheduledKGUpdater

updater = ScheduledKGUpdater(
    data_dir='data/uploads/',
    log_dir='logs/updates/'
)

updater.start()

# Keep application running
import time
while True:
    time.sleep(60)
```

**Deployment with systemd (Linux):**

```ini
# /etc/systemd/system/feekg-updater.service

[Unit]
Description=FE-EKG Scheduled Updater
After=network.target

[Service]
Type=simple
User=feekg
WorkingDirectory=/home/feekg/feekg
ExecStart=/home/feekg/feekg/venv/bin/python -m ingestion.scheduled_updater
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable feekg-updater
sudo systemctl start feekg-updater
sudo systemctl status feekg-updater
```

---

## Complete Workflow Example

### Scenario: Adding 2008 Crisis Timeline from SEC Filings

**User Action:** Upload 50 SEC 8-K filings from September 2008

**Step-by-Step Execution:**

```
Day 0, 2:00 AM - Scheduled Update Triggered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] SCAN UPLOADS DIRECTORY
    ✅ Found: 50 files in data/uploads/
       - lehman_8k_2008-09-15.html
       - aig_8k_2008-09-16.html
       - merrill_lynch_8k_2008-09-17.html
       ...

[2] PARSE FILES (Format Detection)
    ✅ Detected: HTML (SEC EDGAR filings)
    ⏱️  Time: 2 minutes

    Extracted:
    - 50 filing texts
    - Dates, companies, filing types

[3] NLP EXTRACTION (spaCy)
    ✅ Running entity/event extraction...

    Results:
    - Entities: 156 mentions
      • "Lehman Brothers Holdings Inc."
      • "JPMorgan Chase Bank"
      • "Federal Reserve Bank of New York"
      ...

    - Events: 87 detected
      • 2008-09-15: "Lehman Brothers files Chapter 11"
      • 2008-09-16: "AIG receives $85B emergency loan"
      • 2008-09-18: "Fed cuts rate to 2.0%"
      ...

    ⏱️  Time: 3 minutes

[4] SMART DEDUPLICATION
    ✅ Running entity resolution...

    Deduplication:
    - "Lehman Brothers Holdings Inc." → ent_lehman_brothers
    - "Lehman Brothers" → ent_lehman_brothers (matched)
    - "Lehman" → ent_lehman_brothers (matched)
    - "JPMorgan Chase Bank" → ent_jpmorgan_chase
    - "JP Morgan" → ent_jpmorgan_chase (matched)

    Summary:
    - 156 entity mentions → 22 canonical entities
    - 134 duplicates merged (85.9%)

    ⏱️  Time: 30 seconds

[5] EVOLUTION LINK COMPUTATION
    ✅ Computing incremental evolution links...

    Configuration:
    - New events: 87
    - Existing events: 5,105
    - Comparisons: 87 × 5,105 = 444,135 pairs
    - Threshold: 0.5

    Results:
    - Evolution links created: 213
    - Avg score: 0.68

    Top links:
    - lehman_bankruptcy (2008-09-15) → aig_bailout (2008-09-16)
      Score: 0.92 (temporal: 0.98, entity: 0.85, semantic: 0.94)

    - aig_bailout (2008-09-16) → fed_rate_cut (2008-09-18)
      Score: 0.87 (temporal: 0.95, topic: 0.92, causality: 0.88)

    ⏱️  Time: 2 minutes

[6] ALLEGROGRAPH UPDATE
    ✅ Inserting triples...

    Operations:
    - Insert 22 new entities (after deduplication)
    - Insert 87 new events
    - Insert 213 evolution links
    - Update 134 entity aliases

    Total triples added: 2,341
    Total graph size: 431,360 triples (was 429,019)

    ⏱️  Time: 10 seconds

[7] FAISS INDEX REFRESH
    ✅ Generating embeddings...

    Embedding generation:
    - Model: nvidia/llama-3.2-nv-embedqa-1b-v2
    - Batch size: 87 events
    - Dimension: 2048

    ✅ Adding to FAISS index...

    Index stats:
    - Previous: 5,105 events
    - New: 5,192 events
    - Size: 41.5 MB (was 40.8 MB)

    ⏱️  Time: 5 seconds (embedding) + 50ms (FAISS add)

[8] ABM STATE REFRESH
    ✅ Invalidating agent query caches...
    ✅ Updating network topology (2 new entities added)

    ABM agents notified: 10 BankAgents, 1 RegulatorAgent, 1 MarketAgent

    ⏱️  Time: <1 second

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPDATE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total time: 8 minutes 35 seconds

Summary:
✅ Entities: 22 new (134 duplicates merged)
✅ Events: 87 new
✅ Evolution links: 213 new
✅ Graph: 431,360 triples (+2,341)
✅ FAISS: 5,192 events (+87)

Log file: logs/updates/update_2025-11-16_02-00-00.log
Archive: data/uploads/archive/2025-11-16_02-00-00/

Next steps:
- ABM agents can now query updated KG
- RAG retrieval includes Sept 2008 events
- SLM has access to latest context
```

**User Experience (next day):**

```python
# Run ABM simulation with updated KG
model = FinancialCrisisModel(
    n_banks=20,
    crisis_trigger_step=50
)

# Agents automatically use new 2008 data
for step in range(200):
    model.step()

    # BankAgents query: "What happened after Lehman bankruptcy?"
    # RAG retrieves: AIG bailout, Fed rate cut, market crash
    # SLM reasons: "Defensive strategy recommended"
    # Agents act based on historical precedent
```

**Result:** ABM simulation now reflects **real 2008 crisis dynamics** based on actual SEC filings!

---

## Future Enhancements

### Phase 2: PDF Parsing

**Goal:** Extract events from PDF financial reports

**Tools:**
- LlamaParse (best for complex layouts)
- pdfplumber (good for structured PDFs)
- PyPDF2 (simple text extraction)

**Use Cases:**
- Earnings reports
- Annual reports (10-K)
- Research papers

**Timeline:** Week 6-7

---

### Phase 3: News API Integration

**Goal:** Real-time financial news ingestion

**Sources:**
- **GDELT** - Global event database (free)
- **NewsAPI** - News aggregator ($0-449/month)
- **Bloomberg Terminal API** (if available)

**Use Cases:**
- Breaking news (Lehman bankruptcy announcement)
- Market-moving events
- Regulatory announcements

**Timeline:** Week 8-10

---

### Phase 4: Streaming Pipeline

**Goal:** <1 minute latency for real-time updates

**Architecture:**
```
News API → Kafka → NLP Extractor → AllegroGraph → FAISS → ABM
           (queue)                    (parallel)    (async)
```

**Tools:**
- Apache Kafka (message queue)
- Celery (async task processing)
- Redis (fast cache)

**Timeline:** Week 12-16 (production deployment)

---

## Implementation Roadmap

### Week 1-2: MVP (Quick Start)

**Goal:** Basic JSON/CSV upload with manual trigger

**Tasks:**
- [x] Create `ingestion/dynamic_pipeline.py` skeleton
- [ ] Implement JSON parser (reuse existing)
- [ ] Implement CSV parser (pandas)
- [ ] Basic spaCy NER extraction
- [ ] Simple name-matching deduplication
- [ ] Incremental evolution link computation
- [ ] Manual upload API endpoint
- [ ] Basic testing

**Deliverables:**
- Upload JSON/CSV → Auto-extract → Update graph (manually triggered)
- **Demo:** Add 100 events in 5 minutes

---

### Week 3-4: Automation

**Goal:** Scheduled batch processing + web scraping

**Tasks:**
- [ ] SEC EDGAR scraper
- [ ] Scheduled updater (APScheduler)
- [ ] Logging and monitoring
- [ ] Error handling + rollback
- [ ] Email notifications

**Deliverables:**
- Daily automated updates at 2am
- SEC filings automatically ingested
- **Demo:** Zero-touch daily operations

---

### Week 5-6: Intelligence

**Goal:** Smarter extraction and deduplication

**Tasks:**
- [ ] Hybrid spaCy + LLM extraction (optional upgrade)
- [ ] Semantic entity resolution (FAISS + string matching)
- [ ] Temporal entity tracking (mergers/acquisitions)
- [ ] Data quality validation
- [ ] Confidence scores

**Deliverables:**
- 95%+ extraction accuracy
- <5% duplicate entities
- **Demo:** "JP Morgan" = "JPMorgan Chase" automatically

---

### Week 7-8: Advanced Features (Optional)

**Goal:** PDF parsing + news APIs

**Tasks:**
- [ ] PDF parser (LlamaParse or pdfplumber)
- [ ] GDELT news integration
- [ ] Streaming pipeline (Kafka)
- [ ] Monitoring dashboard

**Deliverables:**
- Multi-format ingestion (JSON, CSV, PDF, HTML, News)
- Real-time updates (<1 min latency)

---

## Summary

### The Vision

**Transform FE-EKG from a static knowledge graph into a living, learning system** that:

1. **Continuously ingests** new data (uploads, web scraping, APIs)
2. **Automatically extracts** entities, events, relationships (NLP)
3. **Intelligently deduplicates** entities (smart resolution)
4. **Updates incrementally** (evolution links, FAISS index)
5. **Enables real-time decisions** (ABM agents query updated KG)

### Key Benefits

| Benefit | Impact |
|---------|--------|
| **Zero manual processing** | Upload → 5 min → Done (vs 2-3 hrs manual) |
| **Always current** | ABM decisions based on latest data |
| **Incremental updates** | 26x faster than full recomputation |
| **High data quality** | 85%+ deduplication rate |
| **Scalable** | Handle 100-1000 events/day |

### Technology Stack

- **Extraction:** spaCy (rule-based NER)
- **Deduplication:** String matching + normalization
- **Evolution Links:** Existing 6 algorithms (incremental)
- **Vector DB:** FAISS (incremental add)
- **Graph DB:** AllegroGraph (existing)
- **Scheduling:** APScheduler
- **Web Scraping:** BeautifulSoup + requests

### Next Steps

This document captures the **vision** for a dynamic knowledge graph system. Implementation can proceed incrementally:

1. **Week 1-2:** MVP with JSON/CSV upload
2. **Week 3-4:** Automation + web scraping
3. **Week 5-6:** Smart extraction + deduplication
4. **Week 7-8:** Advanced features (PDF, news APIs)

**Start simple, iterate based on needs!**

---

**Questions or feedback? Discuss with the team and prioritize features based on MVP timeline.**
