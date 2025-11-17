# 🎨 FE-EKG SLIDE DECK TEMPLATE
## Visual Specifications for PowerPoint/Keynote

**Slide Dimensions:** 16:9 (1920x1080px)
**Font:** Helvetica Neue / San Francisco (clean, modern)
**Color Palette:** Dark blue (#0f172a), Bright blue (#3b82f6), Gold (#fbbf24), White (#ffffff)

---

## SLIDE 1: Title Slide

### Layout
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                        FE-EKG                              │
│     Financial Event Evolution Knowledge Graph              │
│                                                            │
│           From 2008 Crisis Analysis to                     │
│           AI-Powered Risk Intelligence                     │
│                                                            │
│                     [Your Name]                            │
│                     [Your Title]                           │
│                      [Date]                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Background:** Dark gradient (#0f172a → #1e293b)
- **Title:** Large, white, bold (72pt)
- **Subtitle:** Medium, light gray (36pt)
- **Your Name:** Small, white (24pt)
- **Accent:** Thin gold line under subtitle

---

## SLIDE 2: The Hook

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  The Challenge                                             │
│                                                            │
│  [Image: 2008 crisis timeline with ? marks between events]│
│                                                            │
│  How do we automatically discover causal links             │
│  between financial events?                                 │
│                                                            │
│  ┌──────────┐    ?    ┌──────────┐    ?    ┌──────────┐  │
│  │Bear      │   -->   │Lehman    │   -->   │AIG       │  │
│  │Stearns   │         │Brothers  │         │Bailout   │  │
│  └──────────┘         └──────────┘         └──────────┘  │
│  Mar 2008             Sep 2008             Sep 2008       │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Question marks:** Large, red (#ef4444)
- **Event boxes:** White cards with shadow
- **Arrows:** Dotted lines (uncertainty)
- **Dates:** Small, gray text

---

## SLIDE 3: The Data Journey (Funnel)

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  From Raw Data to Knowledge Graph                          │
│                                                            │
│        ╔═══════════════════════════════╗                  │
│        ║   77,590 Capital IQ Events    ║                  │
│        ╚═══════════════════════════════╝                  │
│                     ↓                                      │
│           ╔═════════════════════╗                         │
│           ║   5,105 Events      ║                         │
│           ║   (Lehman Crisis)   ║                         │
│           ╚═════════════════════╝                         │
│                     ↓                                      │
│              ╔═══════════════╗                            │
│              ║  31,173 Links ║                            │
│              ║  Discovered   ║                            │
│              ╚═══════════════╝                            │
│                     ↓                                      │
│               ╔═══════════╗                               │
│               ║ 429,019   ║                               │
│               ║ RDF       ║                               │
│               ║ Triples   ║                               │
│               ╚═══════════╝                               │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Funnel:** Blue gradient (lighter → darker going down)
- **Numbers:** Bold, white, large
- **Labels:** Smaller, light gray
- **Arrows:** Solid, thick

---

## SLIDE 4: Three-Layer Architecture

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Knowledge Graph Architecture                              │
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │  RISK LAYER (Why?)                               │     │
│  │  [LiquidityRisk] → [CreditRisk] → [SystemicRisk]│     │
│  └────────────────────┬─────────────────────────────┘     │
│                       ↓                                    │
│  ┌──────────────────────────────────────────────────┐     │
│  │  EVENT LAYER (What?)                             │     │
│  │  [Bankruptcy] → [Downgrade] → [Bailout]         │     │
│  └────────────────────┬─────────────────────────────┘     │
│                       ↓                                    │
│  ┌──────────────────────────────────────────────────┐     │
│  │  ENTITY LAYER (Who?)                             │     │
│  │  [Lehman] ↔ [AIG] ↔ [Fed] ↔ [Treasury]         │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Risk Layer:** Red/orange gradient box
- **Event Layer:** Blue gradient box
- **Entity Layer:** Green gradient box
- **Arrows:** Thick, white, animated
- **Labels:** Why? What? Who? (in parentheses, italic)

---

## SLIDE 5: Six Evolution Methods

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  How We Compute Evolution Scores                           │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐  │
│  │ 1. Temporal     │  │ 2. Entity       │  │ 3. Semantic│ │
│  │    Correlation  │  │    Overlap      │  │    Similar │ │
│  │    TCDI formula │  │    Jaccard      │  │    AI embed│ │
│  │    82%          │  │    45%          │  │    53%     │ │
│  └─────────────────┘  └─────────────────┘  └──────────┘  │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐  │
│  │ 4. Topic        │  │ 5. Causality    │  │ 6. Emotion│  │
│  │    Relevance    │  │    Patterns     │  │    Consist│  │
│  │    Category     │  │    Domain rules │  │    Sentiment│ │
│  │    70%          │  │    0%           │  │    65%     │ │
│  └─────────────────┘  └─────────────────┘  └──────────┘  │
│                                                            │
│  Combined Score: 63% evolution confidence                 │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Cards:** White background, shadow
- **Numbers:** Large, colored (green=high, yellow=med, red=low)
- **Icons:** Simple icons for each method
- **Combined score:** Large, gold highlight box at bottom

---

## SLIDE 6: Technology Stack

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Production-Ready Technology Stack                         │
│                                                            │
│  Backend                        Frontend                   │
│  ┌───────────────────┐          ┌───────────────────┐     │
│  │ AllegroGraph      │          │ Next.js 15        │     │
│  │ RDF Triplestore   │          │ React Framework   │     │
│  └───────────────────┘          └───────────────────┘     │
│  ┌───────────────────┐          ┌───────────────────┐     │
│  │ Python Flask      │          │ Cytoscape.js      │     │
│  │ 20+ REST APIs     │          │ Graph Viz         │     │
│  └───────────────────┘          └───────────────────┘     │
│  ┌───────────────────┐          ┌───────────────────┐     │
│  │ NVIDIA NIM        │          │ TanStack Query    │     │
│  │ $0.0002/query     │          │ Smart Caching     │     │
│  └───────────────────┘          └───────────────────┘     │
│  ┌───────────────────┐          ┌───────────────────┐     │
│  │ FAISS Vector DB   │          │ Tailwind CSS      │     │
│  │ <50ms search      │          │ Modern Design     │     │
│  └───────────────────┘          └───────────────────┘     │
│                                                            │
│  Deployment: Railway (Backend) + Vercel (Frontend)        │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Two columns:** Backend (blue), Frontend (green)
- **Cards:** Rounded corners, icons
- **Key metrics:** Bold, highlighted ($0.0002, <50ms)
- **Deployment:** Footer bar with logos

---

## SLIDE 7: Live Demo Screenshot

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Event Evolution Discovery in Action                       │
│                                                            │
│  [Large screenshot of your mobile app showing:]            │
│  - Event: "Deutsche Bank AG, 2006 Earnings Call"          │
│  - Outgoing: 3 connections                                │
│  - Incoming: 0 connections                                │
│  - Evolution link with T:82%, S:53%, C:0%, Total: 63%     │
│                                                            │
│  Callout bubbles:                                         │
│  → "Automatically discovered"                              │
│  → "Confidence scores for each component"                  │
│  → "Click to navigate evolution chain"                     │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Screenshot:** Full quality, centered
- **Callout bubbles:** Yellow circles with arrows
- **Annotations:** Highlight key UI elements
- **Border:** Subtle shadow for depth

---

## SLIDE 8: Performance Achievements

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Performance Wins                                          │
│                                                            │
│  Query Speed        Before: 5.0s  ━━━━━━━━━━              │
│                     After:  125ms ▓                        │
│                     🚀 40x faster                           │
│                                                            │
│  Evolution Compute  Before: 10min ━━━━━━━━━━              │
│                     After:  2min  ▓▓                       │
│                     🚀 5x faster                            │
│                                                            │
│  Upload Reliability Before: 60%   ━━━━━━                  │
│                     After:  95%   ━━━━━━━━━▓              │
│                     🚀 35% improvement                      │
│                                                            │
│  Data Reduction     Before: 5,105 ━━━━━━━━━━              │
│  (time window)      After:  166   ▓                        │
│                     🚀 26x less (faster analysis)          │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Before:** Gray bars (dull)
- **After:** Blue gradient bars (vibrant)
- **Rockets:** Emoji or icon
- **Numbers:** Bold, contrasting colors

---

## SLIDE 9: Agent-Based Model Demo

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Simulating Financial Contagion with AI Agents            │
│                                                            │
│  [4-panel visualization if available, or description:]     │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Bank Failures   │  │ Capital Levels  │               │
│  │ Step 1: 10/10   │  │ Plummeting      │               │
│  │ ████████████    │  │ █▁▁▁▁▁          │               │
│  └─────────────────┘  └─────────────────┘               │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Market Stress   │  │ Network         │               │
│  │ VIX: 38.0       │  │ Fragmentation   │               │
│  │ TED: 1.55%      │  │ [Graph visual]  │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                            │
│  Test Result: All 10 banks failed → High contagion ✓     │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **4 panels:** Grid layout
- **Charts:** Simple bar/line charts
- **Red/Green:** Red for failures, green for healthy
- **Network:** Node-edge diagram (simplified)

---

## SLIDE 10: 8-Week Roadmap

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Next 8 Weeks: SLM-Powered Agent Intelligence              │
│                                                            │
│  Week 3-4: Local Small Language Model                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ • Download Llama-3.2-1B (2GB, runs on laptop)│         │
│  │ • Replace rules with AI reasoning           │          │
│  │ • Example: "Given 2008 crisis, should I sell?"│        │
│  └─────────────────────────────────────────────┘          │
│                                                            │
│  Week 5-6: RAG System (Knowledge-Grounded)                │
│  ┌─────────────────────────────────────────────┐          │
│  │ • FAISS vector index (40MB, <50ms search)   │          │
│  │ • Agents query: "When Bear Stearns failed,  │          │
│  │   what happened to similar banks?"          │          │
│  │ • SLM uses historical analogies             │          │
│  └─────────────────────────────────────────────┘          │
│                                                            │
│  Week 7-8: Calibration & Validation                       │
│  ┌─────────────────────────────────────────────┐          │
│  │ • Simulate vs actual 2008 timeline          │          │
│  │ • Test counterfactuals: "What if Fed...?"   │          │
│  └─────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Timeline:** Horizontal bars with week numbers
- **Checkboxes:** Progress indicators
- **Cards:** White boxes for each phase
- **Icons:** Brain (AI), Search (RAG), Chart (calibration)

---

## SLIDE 11: Multi-Crisis Vision

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Beyond 2008: 100 Years of Financial Crises                │
│                                                            │
│  1929  ─────┬───── Great Depression                       │
│             │      Stock market crash, bank runs          │
│             │                                              │
│  1997  ─────┬───── Asian Financial Crisis                 │
│             │      Currency contagion (Thailand→Korea)    │
│             │                                              │
│  2008  ─────┬───── Lehman Brothers ✓ IMPLEMENTED          │
│             │      Subprime mortgage crisis               │
│             │                                              │
│  2021  ─────┬───── Evergrande Crisis                      │
│             │      China real estate collapse             │
│             │                                              │
│  2023  ─────┬───── SVB/Signature Bank                     │
│             │      Social media-driven bank runs          │
│             │                                              │
│  Future     ????  Real-time crisis detection              │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Timeline:** Vertical line with dates
- **Crisis boxes:** Colored by severity
- **Checkmark:** Green for completed (2008)
- **Future:** Dotted line, question marks

---

## SLIDE 12: The Vision - Real-Time Detection

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  From Hindsight to Foresight                               │
│                                                            │
│  Scenario: March 2025                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 1. Chinese property dev misses bond payment │          │
│  │    ↓                                        │          │
│  │ 2. FE-EKG Alert                             │          │
│  │    "Matches Evergrande pattern (2021)"      │          │
│  │    "Contagion probability: 73%"             │          │
│  │    ↓                                        │          │
│  │ 3. AI Simulation                            │          │
│  │    SLM agents predict exposure cascade      │          │
│  │    "5 banks at high risk"                   │          │
│  │    ↓                                        │          │
│  │ 4. Action                                   │          │
│  │    Alert portfolio managers                 │          │
│  │    Recommend hedges for Bank X, Bank Y      │          │
│  └─────────────────────────────────────────────┘          │
│                                                            │
│  Historical knowledge → Predictive intelligence           │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Scenario box:** Narrative format
- **Arrows:** Flow showing progression
- **Alert:** Yellow warning box style
- **Timeline:** Left side showing Mar 2025 date

---

## SLIDE 13: The Numbers

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Scale & Impact                                            │
│                                                            │
│  Today                    →    12 Months     →    5 Years │
│  ────────────────────────────────────────────────────────  │
│  5,105 events             →    50,000+       →    500,000+│
│  31,173 links             →    500,000+      →    5M+     │
│  22 institutions          →    200+          →    1,000+  │
│  429K triples             →    5M triples    →    50M     │
│  <100ms queries           →    <50ms         →    <10ms   │
│  $0.20/mo AI              →    $5/mo         →    $20/mo  │
│                                                            │
│  ────────────────────────────────────────────────────────  │
│                                                            │
│  The Bloomberg Terminal for crisis intelligence           │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Table:** Three columns
- **Arrows:** Growth indicators
- **Numbers:** Bold, progressively larger
- **Footer:** Gold box with tagline

---

## SLIDE 14: Closing - The Question

### Layout
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                                                            │
│                  The next crisis                           │
│                  is coming.                                │
│                                                            │
│                  Will we see it                            │
│                  in time?                                  │
│                                                            │
│                                                            │
│                  Thank you.                                │
│                                                            │
│                  [Contact info]                            │
│                  [GitHub link]                             │
│                  [Demo URL]                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements
- **Background:** Dark blue → black gradient
- **Text:** White, large, centered
- **"The next crisis":** Highlighted in red
- **"Will we see it":** Fade-in animation
- **Contact:** Small, bottom-right

---

## 🎨 DESIGN SYSTEM

### Color Palette
```
Primary Blue:   #3b82f6  (buttons, highlights)
Dark Blue:      #0f172a  (backgrounds)
Gold:           #fbbf24  (accents, alerts)
Success Green:  #22c55e  (checkmarks, positive)
Warning Red:    #ef4444  (alerts, failures)
Text Dark:      #1f2937  (body text)
Text Light:     #9ca3af  (secondary text)
White:          #ffffff  (primary text on dark)
```

### Typography
```
Headings:       Helvetica Neue Bold, 48-72pt
Subheadings:    Helvetica Neue Medium, 32-36pt
Body:           Helvetica Neue Regular, 18-24pt
Captions:       Helvetica Neue Light, 14-16pt
Code/Numbers:   Monaco/Menlo, 16-20pt
```

### Spacing
```
Slide margins:  80px all sides
Element spacing: 40px between major sections
Card padding:   30px inside
Line height:    1.5x for readability
```

### Animation Suggestions (PowerPoint/Keynote)
1. **Slide 3 (Funnel):** Wipe down effect for each layer
2. **Slide 4 (Architecture):** Fade in layers from bottom to top
3. **Slide 5 (Methods):** Fly in cards from left, sequentially
4. **Slide 8 (Performance):** Grow bars from 0 to final value
5. **Slide 14 (Closing):** Fade in text line by line

---

## 📊 BONUS: Triple Creation Visualization Slide

(Addressing your request for "how we create triples")

### SLIDE: How RDF Triples Are Created

```
┌────────────────────────────────────────────────────────────┐
│  From Events to Knowledge Graph Triples                    │
│                                                            │
│  Input: Capital IQ Event                                  │
│  ┌─────────────────────────────────────────────┐          │
│  │ Event: "Lehman Brothers files bankruptcy"  │          │
│  │ Date: 2008-09-15                           │          │
│  │ Type: bankruptcy                            │          │
│  │ Entity: Lehman Brothers Holdings Inc.      │          │
│  └─────────────────────────────────────────────┘          │
│                     ↓                                      │
│  RDF Triple Generation (Subject-Predicate-Object)         │
│  ┌─────────────────────────────────────────────┐          │
│  │ 1. evt:lehman_bankruptcy_20080915           │          │
│  │    rdf:type                                 │          │
│  │    feekg:BankruptcyEvent                    │          │
│  │                                             │          │
│  │ 2. evt:lehman_bankruptcy_20080915           │          │
│  │    feekg:hasDate                            │          │
│  │    "2008-09-15"^^xsd:date                   │          │
│  │                                             │          │
│  │ 3. evt:lehman_bankruptcy_20080915           │          │
│  │    feekg:hasActor                           │          │
│  │    entity:lehman_brothers                   │          │
│  │                                             │          │
│  │ 4. evt:lehman_bankruptcy_20080915           │          │
│  │    rdfs:label                               │          │
│  │    "Lehman Brothers files bankruptcy"       │          │
│  └─────────────────────────────────────────────┘          │
│                     ↓                                      │
│  Result: 4 triples in AllegroGraph                        │
│  5,105 events × ~84 triples/event = 429,019 total        │
└────────────────────────────────────────────────────────────┘
```

### Visual Elements for This Slide
- **Input box:** Light blue, CSV-style format
- **Triples:** Monospace font, 3 columns (S-P-O)
- **Arrows:** Show transformation flow
- **Numbers:** Highlight the multiplication (5,105 × 84)
- **Color coding:**
  - Subject: Blue
  - Predicate: Green
  - Object: Orange

---

## 💾 Export Instructions

### For PowerPoint (.pptx)
1. Use "Design" → "Slide Size" → 16:9
2. Create custom color theme with the palette above
3. Use "Animations" → "Morph" for smooth transitions (Office 365)
4. Export as PDF for backup

### For Keynote (.key)
1. Use "Document" → "Slide Size" → Widescreen (16:9)
2. Create color palette in "Colors" panel
3. Use "Magic Move" for object transitions
4. Export as PDF for compatibility

### For Google Slides
1. Use "File" → "Page setup" → Widescreen (16:9)
2. Use custom color palette
3. Simpler animations (fade, slide)
4. Can present directly in browser

---

**All templates are ready to build! Use this as your design guide for creating the actual slides in your preferred tool.**
