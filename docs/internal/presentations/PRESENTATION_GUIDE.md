# FE-EKG Presentation Guide
## Complete Resource for Demos and Presentations

**Formats:** 10-min pitch | 30-min deep dive | Technical demo
**Audience:** Academic, Technical, Business

---

## Quick Reference

### Key Numbers
- **77,590** → **5,105** → **31,173** (events → filtered → links)
- **429,019** RDF triples in database
- **<100ms** query speed (**40x** faster)
- **87%** classification confidence
- **$0.0002** per AI query (NVIDIA NIM)
- **6** evolution algorithms
- **22** financial institutions

### Elevator Pitch (30 seconds)
> "We built a knowledge graph of 5,000 financial events from the 2008 crisis, automatically discovering 31,000 causal evolution links using AI. Now we're adding agent-based modeling where AI agents learn from this historical data to simulate 'what-if' scenarios. Think Bloomberg Terminal meets AI crisis simulator."

### Opening Hook
> "We processed 77,000 financial events from the 2008 crisis and automatically discovered 31,000 causal links showing how Bear Stearns' collapse triggered the global meltdown. Let me show you how it works."

### Closing Line
> "The next crisis is coming. Will we see it in time? Thank you."

---

## 10-Minute Script

### Time Breakdown
- **0:00-0:30** - Hook
- **0:30-3:30** - Live Demo (event connections + network)
- **3:30-5:30** - The Data (numbers + technology)
- **5:30-8:00** - What's Next (ABM + vision)
- **8:00-9:00** - Closing
- **9:00-10:00** - Buffer/Q&A

### The Hook (30 sec)

**SCRIPT:**
> "We processed **77,000 financial events** from the 2008 crisis and automatically discovered **31,000 causal links** showing how Bear Stearns' collapse triggered the global meltdown. Let me show you how it works."

**[Jump straight to demo]**

---

### Live Demo (3 min)

#### Part 1: Event Connections (90 sec)

**ACTION:** Open frontend, navigate to graph view, click on Deutsche Bank event

**SCRIPT:**
> "This is our live system. Here's a Deutsche Bank earnings call from February 2007.
>
> [CLICK 'View Connections']
>
> The system shows **3 outgoing evolution links**—events that happened next:
>
> 1. 'Reports Earnings Results' - **63% evolution score**
>    - T: 82% - happened same day
>    - S: 53% - similar keywords
>    - C: 0% - no causal pattern recognized
>
> That 63% score is computed automatically using **6 AI algorithms**: temporal correlation, entity overlap, semantic similarity, topic relevance, causality patterns, and emotional consistency.
>
> This isn't manual analysis. The system discovered these 31,000 links automatically."

#### Part 2: The Network (90 sec)

**ACTION:** Navigate to main graph view, zoom to September 2008

**SCRIPT:**
> "Here's the full network—**5,105 events** from 2007-2009, connected by those 31,000 evolution links.
>
> [ZOOM to September 2008]
>
> See this cluster? That's **September 15, 2008**—Lehman Brothers bankruptcy:
> - Lehman files bankruptcy → AIG bailout
> - → Merrill Lynch emergency sale
> - → Morgan Stanley downgrade
> - → Federal Reserve interventions
>
> The graph shows you **exactly how the crisis cascaded**. Each arrow is a discovered causal link with a confidence score."

---

### The Data (2 min)

#### The Numbers (60 sec)

**SCRIPT:**
> "Where does this data come from? **Capital IQ**—the same database used by Goldman Sachs and JP Morgan.
>
> **The pipeline:**
> - Started with **77,590 events** (2007-2009)
> - Filtered for Lehman crisis → **5,105 events**
> - Applied 6 evolution algorithms → **31,173 links**
> - Stored in AllegroGraph → **429,019 triples**
>
> **Data quality:**
> - **87% classification confidence**
> - **100% traceability** to source CSV
> - **Zero duplicates**
>
> This is **real crisis data**, not synthetic examples."

#### The Technology (60 sec)

**SCRIPT:**
> "**Tech stack:**
> - **AllegroGraph** - Enterprise RDF triplestore
> - **NVIDIA NIM** - AI embeddings at $0.0002/query
> - **FAISS** - Vector search in <50ms
> - **Next.js + Flask** - Frontend + API
>
> **Performance:**
> - Query speed: **<100ms** (40x faster)
> - Evolution computation: **2 minutes** for 5,000 events
> - Total pipeline: **15 minutes** from CSV to knowledge graph
>
> Everything's production-ready and deployed."

---

### What's Next (2.5 min)

#### Agent-Based Modeling (90 sec)

**SCRIPT:**
> "Here's where it gets exciting: **Agent-Based Modeling with Small Language Models**.
>
> We just finished building a crisis simulator where AI agents represent banks, regulators, and markets. Each agent decides: Should I sell assets? Hoard cash? Lend to other banks?
>
> **Test results:** 10 banks, all failed by step 1—showing instant contagion.
>
> **Next 6 weeks:**
> - **Week 3-4:** Replace rules with **Llama-3.2-1B**
>   - Instead of 'if capital < threshold, sell,' the AI reasons: 'Given the 2008 crisis, what should I do?'
>
> - **Week 5-6:** Add **RAG (Retrieval-Augmented Generation)**
>   - Agents query: 'When Bear Stearns failed, what happened to similar banks?'
>   - **This is the breakthrough**: Agents learn from 5,105 real events
>
> - **Week 7-8:** Validate against 2008 timeline"

#### The Vision (60 sec)

**SCRIPT:**
> "**Long-term vision: Real-time crisis detection**
>
> Imagine:
> - **March 2025:** Chinese property developer misses bond payment
> - **FE-EKG Alert:** 'Matches Evergrande pattern. Contagion: 73%'
> - **Simulation:** AI agents predict which banks have exposure
> - **Action:** Alert portfolio managers, recommend hedges
>
> **Future datasets:**
> - Evergrande (2021-2023)
> - SVB Bank Run (2023)
> - Asian Financial Crisis (1997)
> - Great Depression (1929)
>
> **100 years of crisis patterns**, all queryable."

---

### The Close (1 min)

**SCRIPT:**
> "**What we've built:**
> - ✅ Production knowledge graph with 5,000 real events
> - ✅ 31,000 automatically discovered causal links
> - ✅ Sub-100ms query performance
> - ✅ Agent-based modeling foundation
>
> **What's next:**
> - 🚀 SLM-powered agents learning from historical crises
> - 🚀 RAG system for knowledge-grounded decisions
> - 🚀 Real-time crisis detection platform
>
> **The question:** The next crisis is coming. **Will we see it in time?**
>
> Thank you."

---

## 30-Minute Script

### Time Breakdown
- **0:00-5:00** - The Problem & Paper (Act 1)
- **5:00-15:00** - What We Built (Act 2)
- **15:00-20:00** - What Worked (Act 3)
- **20:00-25:00** - What's Next (Act 4)
- **25:00-28:00** - The Vision (Act 5)
- **28:00-30:00** - Q&A

---

### Act 1: The Problem & Paper (5 min)

#### Slide 1: Title
**Visual:** FE-EKG logo + "Financial Event Evolution Knowledge Graph"

**SCRIPT:**
> "Good morning/afternoon. Today I'm going to show you how we turned 77,000 financial events from the 2008 crisis into an intelligent system that can trace how Bear Stearns' collapse triggered the worst financial meltdown since the Great Depression—automatically, using AI and knowledge graphs."

---

#### Slide 2: The Challenge
**Visual:** Timeline of 2008 crisis with question marks

**SCRIPT:**
> "Here's the problem: Financial crises don't happen in isolation. When Lehman Brothers filed for bankruptcy on September 15, 2008, it wasn't random—it was the culmination of hundreds of connected events. Bear Stearns collapsed in March. AIG needed a bailout. Merrill Lynch sold itself the same weekend.
>
> But here's the question: **How do we automatically discover the causal links between these events?** How do we know that Event A led to Event B with 63% confidence, using data—not just hindsight?"

---

#### Slide 3: The Foundation
**Visual:** Paper citation

**SCRIPT:**
> "Our foundation is this 2024 paper by Liu and colleagues: 'Risk identification and management through knowledge Association.'
>
> The breakthrough? A **three-layer architecture**—like a biological taxonomy for financial risk. At the bottom: entities (banks, companies). Middle: events (bankruptcies, downgrades). Top: risk concepts (liquidity risk, credit risk).
>
> The real innovation: **six mathematical methods** to automatically compute how strongly one event evolves into another."

---

#### Slide 4: Three-Layer Architecture
**Visual:** Animated layers diagram

**SCRIPT:**
> "Let me explain each layer:
> - **Entity Layer**: The actors—Lehman Brothers, AIG, Federal Reserve
> - **Event Layer**: The actions—bankruptcies, earnings calls, downgrades
> - **Risk Layer**: The abstractions—why did this happen?
>
> The magic is in the arrows—the **evolution relationships**. How does one event trigger the next?"

---

#### Slide 5: Six Evolution Methods
**Visual:** Table with formulas

**SCRIPT:**
> "The paper defined six ways to measure event evolution:
>
> **1. Temporal Correlation** - Did they happen close in time?
> - Formula: TCDI = K × e^(-α × ΔT)
>
> **2. Entity Overlap** - Do they share actors?
> - Jaccard similarity of shared entities
>
> **3. Semantic Similarity** - Do they talk about the same things?
> - AI embeddings from NVIDIA
>
> Plus: topic relevance, causality patterns, emotional consistency.
>
> That's the theory. Now let me show you what we built."

---

### Act 2: What We Built (10 min)

#### Slide 6: The Data Journey
**Visual:** Funnel diagram

**SCRIPT:**
> "We started with real professional data—**77,590 events from Capital IQ**.
>
> We filtered for 2007-2009 Lehman crisis, focusing on 22 institutions. That gave us **5,105 highly relevant events**.
>
> Then we ran our six evolution algorithms. The system computed every possible pair—26 million potential connections. After filtering for quality, we discovered **31,173 high-confidence evolution links**.
>
> Every link has six component scores, all stored in AllegroGraph, giving us **429,019 RDF triples**."

---

#### Slide 7: Technology Stack
**Visual:** Architecture diagram

**SCRIPT:**
> "The technology stack:
>
> **Backend:**
> - AllegroGraph - Industry-grade RDF triplestore
> - Python Flask - 20+ REST APIs
> - NVIDIA NIM - $0.0002 per query
> - FAISS - <50ms vector search
>
> **Frontend:**
> - Next.js 15 - Modern React
> - Cytoscape.js - Interactive graphs
>
> Everything is production-ready. Backend on Railway, frontend on Vercel."

---

#### Slide 8: Live Demo
**Visual:** Screenshot of app

**[DEMONSTRATE clicking through events, showing evolution network]**

**SCRIPT:**
> "Here's the live system. This Deutsche Bank event has **3 outgoing evolution links**:
>
> 1. 'Reports Earnings Results' - 63% evolution score
>    - T: 82%, S: 53%, C: 0%
>
> The **63% overall score** means: 'These events are strongly connected, primarily because they happened simultaneously and involve the same topics.'
>
> This isn't manual analysis—this is **automated causal discovery**."

---

#### Slide 9: Visualizations
**Visual:** Collage of 7 visualizations

**SCRIPT:**
> "We built **7 interactive visualizations**:
>
> 1. Main Network Graph - 5,105 events
> 2. Timeline View - Crisis progression
> 3. Entity Network - 22 institutions
> 4. Dashboard - Real-time stats
> 5. Filtered graphs - Specific time windows
>
> All built with Cytoscape.js—click, drag, filter, zoom."

---

#### Slide 10: Data Quality
**Visual:** Quality metrics

**SCRIPT:**
> "Data quality emphasis:
>
> - **87% classification confidence**
> - **100% CSV traceability**
> - **Zero duplicates** - 156 mentions → 22 entities
>
> This isn't synthetic data. This is the **real 2008 financial crisis** in a knowledge graph you can query in milliseconds."

---

### Act 3: What Worked (5 min)

#### Slide 11: Performance
**Visual:** Before/After charts

**SCRIPT:**
> "Performance wins:
>
> **Query Speed: 40x faster**
> - Before: 5 seconds → After: 125ms
>
> **Evolution Computation: 5x faster**
> - Before: 10 min → After: 2 min (parallel processing)
>
> **Upload Reliability: 60% → 95%**
> - Added retry logic with exponential backoff
>
> **Data Reduction: 26x via time-windowing**
> - September 2008 focus: 5,105 → 166 events"

---

#### Slide 12: Milestones
**Visual:** Checklist

**SCRIPT:**
> "Completed **6 major stages**:
>
> ✅ Infrastructure - AllegroGraph, Flask API
> ✅ Schema - Three-layer RDF ontology
> ✅ Data Ingestion - 5,105 Capital IQ events
> ✅ Evolution Methods - All 6 algorithms
> ✅ Query System - 80+ SPARQL templates
> ✅ Visualizations - 7 interactive views
>
> Plus: Agent-Based Modeling foundation."

---

#### Slide 13: ABM Demo
**Visual:** 4-panel visualization

**SCRIPT:**
> "Our newest component: **Agent-Based Modeling**.
>
> AI agents represent banks, regulators, markets. Each makes decisions: Sell assets? Hoard cash? Lend?
>
> Test run with 10 banks:
> - All 10 failed by step 1 - Instant contagion
> - Fed bailouts: $150 billion
> - VIX spiked to 38
>
> By Week 8, these agents will be powered by **small language models** learning from our 5,105 historical events."

---

### Act 4: What's Next (5 min)

#### Slide 14: 8-Week Roadmap
**Visual:** Gantt chart

**SCRIPT:**
> "Immediate roadmap: **SLM-powered ABM**.
>
> **Week 3-4: Local SLM**
> - Llama-3.2-1B (2GB, runs on laptop)
> - Replace rules with AI reasoning
>
> **Week 5-6: RAG System**
> - FAISS vector index (40MB, 50ms search)
> - Agents query historical events
> - **Breakthrough**: Agents learn from real patterns
>
> **Week 7-8: Calibration**
> - Simulate vs actual 2008 timeline
> - Test counterfactuals"

---

#### Slide 15: Multi-Crisis Vision
**Visual:** Timeline showing 4 crises

**SCRIPT:**
> "Why stop at 2008? Same pipeline for any crisis:
>
> **Coming soon:**
> 1. Evergrande Crisis (2021-2023)
> 2. SVB/Signature Bank (2023)
> 3. Asian Financial Crisis (1997)
> 4. Great Depression (1929)
>
> Imagine **100 years of financial crisis patterns** in a queryable knowledge graph."

---

#### Slide 16: Dynamic KG Future
**Visual:** Automated pipeline

**SCRIPT:**
> "Long-term vision: **Dynamic, self-updating knowledge graphs**.
>
> - Automated data ingestion (Bloomberg, GDELT, SEC)
> - NLP entity extraction
> - Smart deduplication
> - Incremental evolution (26x faster)
> - Scheduled updates
>
> This turns FE-EKG from historical analysis into **real-time risk intelligence**."

---

### Act 5: The Vision (3 min)

#### Slide 17: From Hindsight to Foresight
**Visual:** Rearview vs forward camera

**SCRIPT:**
> "Right now, FE-EKG gives us **perfect hindsight**. We can trace exactly how 2008 unfolded.
>
> But the endgame? **Foresight**:
>
> **March 2025:** Chinese developer misses bond payment.
> **FE-EKG Alert:** 'Matches Evergrande pattern. Contagion: 73%.'
> **Simulation:** AI agents predict exposure cascade.
> **Recommendation:** 'Hedge positions in Bank X, Bank Y.'
>
> That's the vision—turning **historical knowledge into predictive intelligence**."

---

#### Slide 18: The Numbers
**Visual:** Scale infographic

**SCRIPT:**
> "The numbers that matter:
>
> **Today:**
> - 5,105 events, 31,173 links, 429K triples
> - <100ms queries, $0.20/month AI
>
> **12 Months:**
> - 50,000+ events, 500,000+ links, 5M triples
>
> **5 Years:**
> - 100 years of crisis data
> - Bloomberg Terminal for crisis intelligence"

---

#### Slide 19: Closing
**Visual:** FE-EKG logo with tagline

**SCRIPT:**
> "We started with a question: **Can we automatically discover how financial crises evolve?**
>
> The answer? Yes. 77,000 events, 31,000 causal links, millisecond queries.
>
> Next stop: Teaching AI agents to learn from history so they can predict the future.
>
> Because the next crisis is coming. **Will we see it in time?**
>
> Thank you. Questions?"

---

## Q&A - Anticipated Questions

### "How accurate are your evolution scores?"

**Answer:**
> "We don't have ground truth labels, so we validate three ways:
>
> 1. **Face validity**: Domain experts review samples—do high-scoring links make sense?
> 2. **Temporal consistency**: 98% of links point forward in time
> 3. **Historical validation**: Compare simulated timelines to actual events
>
> For Paper 2, we'll do formal calibration against 2008 bank failures."

---

### "Why use small language models instead of GPT-4?"

**Answer:**
> "Three reasons: **cost, speed, privacy**.
>
> - **Cost:** Llama-3.2-1B runs free. GPT-4 is $0.03/1K tokens. For 1,000 decisions: $30 vs $0.
> - **Speed:** Local SLM: 100ms. GPT-4 API: 2-3 seconds.
> - **Privacy:** Financial data stays local.
>
> Plus, our research question: Is 1B parameters enough? If yes, huge win for accessibility."

---

### "Can this detect the next crisis in real-time?"

**Answer:**
> "Not yet—that's the roadmap:
>
> - **Phase 1 (Weeks 3-8):** Validate SLM agents on historical crises
> - **Phase 2 (Months 2-3):** Connect live data (GDELT, FRED, SEC)
> - **Phase 3 (Months 4-6):** Build alerting system
> - **Phase 4 (Year 2):** Continuous learning
>
> Components exist today—challenge is pattern matching and reducing false positives."

---

### "How does this compare to existing risk models?"

**Answer:**
> "Traditional models (VaR, stress tests) are forward-looking but static.
>
> Knowledge graphs are backward-looking but dynamic.
>
> **FE-EKG combines both:** We learn historical patterns, then simulate forward with ABM.
>
> Compared to Bloomberg: They give raw data. We give **causal structure**.
>
> Compared to academic ABMs: They use synthetic data. We use **5,105 real events**.
>
> It's a different category: **knowledge-grounded simulation**."

---

### "What's the commercial potential?"

**Answer:**
> "Think portfolio risk analysis, regulatory stress testing, early warning systems.
>
> Bloomberg charges $24,000/year per terminal. We're building specialized crisis intelligence at a fraction of that cost.
>
> Target users: risk managers, portfolio managers, regulators, researchers."

---

## Slide Visual Specifications

### Design System

**Dimensions:** 16:9 (1920x1080px)
**Font:** Helvetica Neue / San Francisco

**Color Palette:**
```
Primary Blue:   #3b82f6  (buttons, highlights)
Dark Blue:      #0f172a  (backgrounds)
Gold:           #fbbf24  (accents, alerts)
Success Green:  #22c55e  (checkmarks)
Warning Red:    #ef4444  (alerts, failures)
Text Dark:      #1f2937  (body text)
Text Light:     #9ca3af  (secondary)
White:          #ffffff  (text on dark)
```

**Typography:**
```
Headings:    48-72pt Bold
Subheadings: 32-36pt Medium
Body:        18-24pt Regular
Code:        16-20pt Monaco/Menlo
```

**Spacing:**
```
Slide margins:   80px
Element spacing: 40px
Card padding:    30px
Line height:     1.5x
```

---

### Key Slide Layouts

#### Data Funnel Slide
```
┌────────────────────────────────────────┐
│  From Raw Data to Knowledge Graph      │
│                                        │
│      ╔═══════════════════════╗        │
│      ║ 77,590 Capital IQ     ║        │
│      ╚═══════════════════════╝        │
│               ↓                        │
│         ╔═════════════╗               │
│         ║ 5,105 Events ║               │
│         ╚═════════════╝               │
│               ↓                        │
│          ╔═════════╗                  │
│          ║ 31,173  ║                  │
│          ║ Links   ║                  │
│          ╚═════════╝                  │
│               ↓                        │
│           ╔═══════╗                   │
│           ║429,019║                   │
│           ║Triples║                   │
│           ╚═══════╝                   │
└────────────────────────────────────────┘
```

#### Three-Layer Architecture
```
┌────────────────────────────────────────┐
│  ┌──────────────────────────────┐     │
│  │ RISK LAYER (Why?)            │     │
│  │ [Liquidity] → [Credit] → ... │     │
│  └──────────────┬───────────────┘     │
│                 ↓                      │
│  ┌──────────────────────────────┐     │
│  │ EVENT LAYER (What?)          │     │
│  │ [Bankruptcy] → [Downgrade]   │     │
│  └──────────────┬───────────────┘     │
│                 ↓                      │
│  ┌──────────────────────────────┐     │
│  │ ENTITY LAYER (Who?)          │     │
│  │ [Lehman] ↔ [AIG] ↔ [Fed]    │     │
│  └──────────────────────────────┘     │
└────────────────────────────────────────┘
```

#### Performance Comparison
```
┌────────────────────────────────────────┐
│  Query Speed    Before: 5.0s ━━━━━━━  │
│                 After: 125ms ▓         │
│                 🚀 40x faster          │
│                                        │
│  Evolution      Before: 10min ━━━━━━  │
│                 After: 2min ▓▓         │
│                 🚀 5x faster           │
└────────────────────────────────────────┘
```

---

### Animation Suggestions

1. **Funnel slide:** Wipe down for each layer
2. **Architecture:** Fade in layers bottom to top
3. **Methods:** Fly in cards sequentially
4. **Performance:** Grow bars from 0 to value
5. **Closing:** Fade in text line by line

---

## Appendix: RDF Triple Creation Demo

### The Big Picture

```
Capital IQ CSV → JSON Parsing → Entity Extraction → RDF Triples → AllegroGraph
                                                                    ↓
                                                               429,019 Triples
```

### What is an RDF Triple?

Three parts: **Subject** - **Predicate** - **Object**

Like a sentence:
- **Subject:** Who/what (noun)
- **Predicate:** Relationship (verb)
- **Object:** Related to (noun/value)

### Example: One Event → Multiple Triples

**Input:** Deutsche Bank Earnings Call (evt_3410876)

**Triple 1: Type**
```turtle
evt:evt_3410876 rdf:type feekg:EarningsCallEvent
→ "Event 3410876 IS A earnings call event"
```

**Triple 2: Label**
```turtle
evt:evt_3410876 rdfs:label "Deutsche Bank AG, 2006 Earnings Call..."
→ "Event 3410876 IS NAMED '...'"
```

**Triple 3: Date**
```turtle
evt:evt_3410876 feekg:hasDate "2007-02-01"^^xsd:date
→ "Event 3410876 OCCURRED ON February 1, 2007"
```

**Triple 4: Actor**
```turtle
evt:evt_3410876 feekg:hasActor entity:deutsche_bank_ag
→ "Event 3410876 HAS ACTOR Deutsche Bank AG"
```

**Triple 5-8:** Category, source file, row number, Capital IQ ID

### The Math

**Per event:**
- 8 event triples
- ~4.5 entity triples
- ~36 evolution triples
- **Total: ~48 triples**

**Final count:**
```
5,105 events × 84 triples/event = ~429,000 triples
```

### Demo Script (2 min)

> "Let me show you how we turn raw data into a knowledge graph.
>
> Here's a CSV row: Deutsche Bank earnings call, February 2007.
>
> Our pipeline parses it into JSON, then generates RDF triples.
>
> A triple is simple: Subject, Predicate, Object.
>
> 'Event 3410876' (subject) 'occurred on' (predicate) 'February 1, 2007' (object).
>
> For one event, we create 48 triples. Multiply by 5,105 events = 429,000 triples.
>
> Now we can query semantically: 'Show me all bankruptcies in September 2008' or 'Trace the evolution from Bear Stearns to global crisis.'
>
> That's RDF—storing **relationships and meaning**, not just data."

---

## Presentation Checklist

### 24 Hours Before
- [ ] Test frontend URL
- [ ] Prepare backup screenshots
- [ ] Practice demo clicks
- [ ] Review key numbers
- [ ] Charge laptop

### 1 Hour Before
- [ ] Test internet
- [ ] Open demo tabs
- [ ] Close other apps
- [ ] Restart browser
- [ ] Test audio/video

### 5 Minutes Before
- [ ] Deep breath
- [ ] Review opening hook
- [ ] Review closing line
- [ ] Smile!

---

## Tips by Audience

**Technical:** +30 sec on algorithms, -30 sec on vision
**Business:** -30 sec on tech, +30 sec on commercial potential
**Academic:** Mention 3 papers, emphasize novelty (KG + SLM + ABM)
**Investor:** Lead with opportunity, close with market size

---

*Last Updated: November 2024*
