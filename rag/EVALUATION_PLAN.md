# Evaluation Strategy: KG + SLM + ABM

For your research paper, you need to evaluate three distinct layers of the system. Here is the standard methodology for evaluating RAG-enhanced Agent-Based Models.

## 1. Micro-Level: SLM Benchmarks (Reasoning & RAG)
*Focus: Does the individual brain work?*

### Framework: RAGAS (Retrieval Augmented Generation Assessment)
We will use the **RAGAS** library to generate automated scores, aligning with standard SLM benchmarks for reasoning accuracy.

| Metric | What it Measures | How to Calculate |
| :--- | :--- | :--- |
| **Context Precision** | Is the retrieved information actually relevant? | `ragas.metrics.context_precision` |
| **Context Recall** | Did we find *all* the relevant information? | `ragas.metrics.context_recall` |
| **Faithfulness** | Is the answer derived *only* from the context (no hallucinations)? | `ragas.metrics.faithfulness` |
| **Answer Relevance** | Does the answer directly address the query? | `ragas.metrics.answer_relevancy` |

## 2. Meso-Level: Multi-Agent Benchmarks (Interaction & Alignment)
*Focus: Do agents behave like real banks?*

This addresses the gap in current Multi-Agent benchmarks (which focus on games) by applying it to **Financial Alignment**.

*   **Behavioral Cloning Score**: Accuracy of agent decisions compared to historical actions (e.g., Did the agent raise capital when the real bank did?).
*   **Information Sensitivity**: Measure how agent behavior changes when "Rumors" are introduced (The "Narrative Contagion" experiment).

## 3. Macro-Level: ABM & Systemic Risk Benchmarks
*Focus: Does the system crash correctly?*

Standard ABM validation (Allen & Gale style):

*   **Systemic Risk Curve**: Compare simulated `systemic_risk` to historical **VIX Index** or **TED Spread**.
*   **Default Cascades**: Does the failure of Bank A cause the failure of Bank B? (Contagion validation).

---

## Implementation Plan for Evaluation

1.  **Week 4 (RAG)**: Implement `ragas` to test retrieval quality.
2.  **Week 5 (ABM)**: Run "Historical Replay" scenarios to test Behavioral Alignment.
3.  **Week 6 (Paper)**: Generate comparative plots (Model A vs Model B) for the results section.
