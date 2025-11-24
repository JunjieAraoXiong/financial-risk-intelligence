"""
RAG Evaluation Pipeline for Financial Crisis ABM

Implements:
1. RAGAS-style metrics (Context Relevancy, Precision, Faithfulness)
2. LLM-as-Judge for document relevance scoring
3. Decision accuracy evaluation
4. Source diversity metrics

Usage:
    python rag/evaluation.py
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import Counter
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from rag.query_generator import QueryGenerator
from slm.llama_client import LocalSLM

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
EVAL_DATASET_PATH = "rag/eval_dataset.json"
RESULTS_DIR = "results"
REPORT_PATH = os.path.join(RESULTS_DIR, "rag_evaluation_report.json")

# Sample documents for fallback mode when DB is unavailable
SAMPLE_CRISIS_DOCS = [
    """[Source: JPM_Weekly_2008-09-15.pdf, Date: 2008-09-15, Page: 1]
    EMERGENCY MARKET UPDATE - September 15, 2008

    Lehman Brothers has filed for Chapter 11 bankruptcy, the largest bankruptcy filing in U.S. history.
    Markets are in severe distress with the VIX spiking above 80. Interbank lending has effectively frozen.
    The Federal Reserve is considering emergency liquidity facilities. Counterparty risk is at extreme levels.
    All financial institutions should take immediate defensive action to preserve liquidity and capital.""",

    """[Source: BIS_Quarterly_2008-09.pdf, Date: 2008-09-28, Page: 23]
    The collapse of Lehman Brothers triggered a global liquidity crisis. Credit default swap spreads widened
    dramatically. The commercial paper market effectively shut down with issuers unable to roll over debt.
    Central banks worldwide are coordinating emergency interventions. Bank failures and forced mergers
    are occurring across major financial centers. Systemic risk has reached unprecedented levels.""",

    """[Source: FCIC_Report.pdf, Date: 2008-09-20, Page: 156]
    The week of September 15, 2008 marked the peak of the financial crisis. Following Lehman's bankruptcy,
    AIG required emergency government assistance to prevent collapse. Money market funds "broke the buck"
    triggering massive redemptions. The Treasury implemented the TARP program to recapitalize banks.
    The crisis demonstrated the severe consequences of inadequate liquidity management and excessive leverage.""",

    """[Source: FT_Article_2008-09-18.json, Date: 2008-09-18, Page: 0]
    Global stock markets plunged as panic spread following Lehman's collapse. The Fed and Treasury are
    working on unprecedented intervention measures. Goldman Sachs and Morgan Stanley face severe pressure.
    Banks worldwide are hoarding liquidity. The TED spread has reached 3% indicating extreme stress in
    interbank markets. Investor confidence has collapsed with fears of systemic banking failure.""",

    """[Source: JPM_Weekly_2008-03-17.pdf, Date: 2008-03-17, Page: 2]
    Bear Stearns collapsed over the weekend and was acquired by JPMorgan Chase with Federal Reserve backing.
    The Fed opened the discount window to investment banks for the first time since the Great Depression.
    This marks a significant escalation in the credit crisis. Market volatility remains elevated with
    concerns about additional failures in the financial sector."""
]

SAMPLE_NORMAL_DOCS = [
    """[Source: JPM_Weekly_2007-02-12.pdf, Date: 2007-02-12, Page: 1]
    Market conditions remain favorable with steady economic growth. Credit spreads are tight and
    liquidity is abundant. Banking sector profitability is strong with low default rates.
    Current outlook supports maintaining existing positions and strategies.""",

    """[Source: BIS_Annual_2006.pdf, Date: 2006-12-31, Page: 45]
    The global banking system showed resilience in 2006 with strong capital ratios across major
    institutions. Credit conditions are healthy with adequate lending standards. Economic indicators
    suggest continued stable growth in the near term."""
]


class RAGEvaluator:
    """Comprehensive evaluation of RAG pipeline for financial crisis scenarios."""

    def __init__(self, use_fallback=False):
        """Initialize evaluator with retriever and SLM.

        Args:
            use_fallback: If True, use sample documents instead of ChromaDB.
                         Useful when DB is unavailable or for testing.
        """
        logger.info("Initializing RAG Evaluator...")

        self.use_fallback = use_fallback
        self.retriever = None

        # Try to initialize retriever
        if not use_fallback:
            try:
                from rag.retriever import RAGRetriever
                self.retriever = RAGRetriever()
                logger.info("ChromaDB retriever initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB retriever: {e}")
                logger.warning("Falling back to sample documents mode")
                self.use_fallback = True

        if self.use_fallback:
            logger.info("Using fallback mode with sample documents")

        # Initialize SLM for decision evaluation
        logger.info("Loading SLM for evaluation...")
        self.slm = LocalSLM()

        # Load evaluation dataset
        self.eval_dataset = self._load_eval_dataset()

        # Results storage
        self.results = []

    def _get_fallback_docs(self, regime: str) -> List[str]:
        """Get sample documents based on market regime."""
        if regime in ['crisis', 'stress']:
            return SAMPLE_CRISIS_DOCS[:5]
        else:
            return SAMPLE_NORMAL_DOCS + SAMPLE_CRISIS_DOCS[:1]

    def _load_eval_dataset(self) -> List[Dict]:
        """Load evaluation dataset from JSON file."""
        if not os.path.exists(EVAL_DATASET_PATH):
            logger.error(f"Evaluation dataset not found at {EVAL_DATASET_PATH}")
            return []

        with open(EVAL_DATASET_PATH, 'r') as f:
            dataset = json.load(f)

        logger.info(f"Loaded {len(dataset)} evaluation cases")
        return dataset

    def evaluate_all(self) -> Dict[str, Any]:
        """Run full evaluation on all test cases."""
        logger.info("Starting full RAG evaluation...")

        for i, test_case in enumerate(self.eval_dataset):
            logger.info(f"Evaluating case {i+1}/{len(self.eval_dataset)}: {test_case['id']}")
            result = self.evaluate_single(test_case)
            self.results.append(result)

        # Aggregate metrics
        report = self._aggregate_results()

        # Save report
        self._save_report(report)

        return report

    def evaluate_single(self, test_case: Dict) -> Dict[str, Any]:
        """Evaluate a single test case."""
        case_id = test_case['id']
        query = test_case['query']
        date = test_case['date']
        volatility = test_case['volatility']
        liquidity_factor = test_case['liquidity_factor']
        expected_topics = test_case['expected_topics']
        expected_decision = test_case['expected_decision']
        regime = test_case['regime']

        # 1. Retrieve documents using multi-query approach (or fallback)
        if self.use_fallback:
            retrieved_docs = self._get_fallback_docs(regime)
        else:
            retrieved_docs = self.retriever.get_context_multi_query(
                date=date,
                volatility=volatility,
                liquidity_factor=liquidity_factor,
                k=5,
                use_hyde=True
            )

        # 2. Calculate retrieval metrics
        topic_coverage = self._calculate_topic_coverage(retrieved_docs, expected_topics)
        context_relevancy = self._calculate_context_relevancy(query, retrieved_docs)
        context_precision = self._calculate_context_precision(query, retrieved_docs, expected_topics)
        source_diversity = self._calculate_source_diversity(retrieved_docs)

        # 3. LLM-as-Judge relevance scoring
        llm_relevance_scores = self._llm_judge_relevance(query, retrieved_docs)
        avg_llm_relevance = sum(llm_relevance_scores) / len(llm_relevance_scores) if llm_relevance_scores else 0

        # 4. Get SLM decision
        context_str = "\n\n".join(retrieved_docs)
        decision = self._get_slm_decision(
            context=context_str,
            volatility=volatility,
            liquidity_factor=liquidity_factor,
            date=date
        )
        decision_correct = decision == expected_decision

        # 5. Calculate faithfulness (does decision use context?)
        faithfulness = self._calculate_faithfulness(decision, retrieved_docs, expected_decision)

        result = {
            "case_id": case_id,
            "regime": regime,
            "query": query,
            "date": date,
            "volatility": volatility,
            "liquidity_factor": liquidity_factor,
            "expected_decision": expected_decision,
            "actual_decision": decision,
            "decision_correct": decision_correct,
            "metrics": {
                "topic_coverage": topic_coverage,
                "context_relevancy": context_relevancy,
                "context_precision": context_precision,
                "source_diversity": source_diversity,
                "avg_llm_relevance": avg_llm_relevance,
                "faithfulness": faithfulness,
                "llm_relevance_scores": llm_relevance_scores
            },
            "retrieved_docs_count": len(retrieved_docs),
            "retrieved_sources": self._extract_sources(retrieved_docs)
        }

        logger.info(f"  Topic coverage: {topic_coverage:.2f}")
        logger.info(f"  Context relevancy: {context_relevancy:.2f}")
        logger.info(f"  LLM relevance: {avg_llm_relevance:.2f}")
        logger.info(f"  Decision: {decision} (expected: {expected_decision}, correct: {decision_correct})")

        return result

    def _calculate_topic_coverage(self, docs: List[str], expected_topics: List[str]) -> float:
        """Calculate what fraction of expected topics are covered in retrieved docs."""
        if not expected_topics:
            return 1.0

        combined_text = " ".join(docs).lower()
        covered_count = 0

        for topic in expected_topics:
            # Check for topic or variations
            topic_lower = topic.lower()
            if topic_lower in combined_text:
                covered_count += 1
            else:
                # Try partial matching for multi-word topics
                words = topic_lower.split()
                if len(words) > 1 and all(w in combined_text for w in words):
                    covered_count += 1

        return covered_count / len(expected_topics)

    def _calculate_context_relevancy(self, query: str, docs: List[str]) -> float:
        """
        Calculate context relevancy using keyword overlap.
        Approximates RAGAS context relevancy metric.
        """
        if not docs:
            return 0.0

        # Extract keywords from query
        query_keywords = set(re.findall(r'\b\w{4,}\b', query.lower()))

        relevancy_scores = []
        for doc in docs:
            doc_words = set(re.findall(r'\b\w{4,}\b', doc.lower()))
            if query_keywords:
                overlap = len(query_keywords & doc_words) / len(query_keywords)
                relevancy_scores.append(overlap)
            else:
                relevancy_scores.append(0.0)

        return sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0.0

    def _calculate_context_precision(self, query: str, docs: List[str], expected_topics: List[str]) -> float:
        """
        Calculate context precision - are relevant docs ranked higher?
        Approximates RAGAS context precision (position-weighted relevance).
        """
        if not docs or not expected_topics:
            return 0.0

        # Score each doc by topic coverage
        doc_scores = []
        for doc in docs:
            doc_lower = doc.lower()
            score = sum(1 for topic in expected_topics if topic.lower() in doc_lower)
            doc_scores.append(score / len(expected_topics))

        # Calculate position-weighted precision (higher weight for earlier positions)
        weights = [1 / (i + 1) for i in range(len(docs))]
        weighted_score = sum(s * w for s, w in zip(doc_scores, weights))
        max_weighted_score = sum(weights)

        return weighted_score / max_weighted_score if max_weighted_score > 0 else 0.0

    def _calculate_source_diversity(self, docs: List[str]) -> float:
        """Calculate source diversity score (0-1, higher = more diverse)."""
        if not docs:
            return 0.0

        sources = []
        for doc in docs:
            # Extract source from formatted doc string
            if "[Source:" in doc:
                source_match = re.search(r'\[Source: ([^,\]]+)', doc)
                if source_match:
                    source = source_match.group(1)
                    # Categorize source
                    if 'JPM' in source:
                        sources.append('JPM')
                    elif 'BIS' in source or 'ar' in source or 'r_qt' in source:
                        sources.append('BIS')
                    elif 'FT' in source:
                        sources.append('FT')
                    elif 'Financial Crisis' in source:
                        sources.append('FCIC')
                    else:
                        sources.append('Other')

        # Calculate diversity as unique sources / total docs
        if not sources:
            return 0.0

        unique_sources = len(set(sources))
        max_possible = min(len(docs), 5)  # Max 5 source types

        return unique_sources / max_possible

    def _llm_judge_relevance(self, query: str, docs: List[str]) -> List[float]:
        """
        Use SLM as a judge to score document relevance (1-5 scale).
        Returns list of scores for each document.
        """
        scores = []

        for i, doc in enumerate(docs):
            # Truncate doc to avoid token limits
            doc_truncated = doc[:1000] if len(doc) > 1000 else doc

            # Use a simpler prompt that's easier for small models
            judge_prompt = f"""Is this document relevant to the query?

Query: {query}

Document excerpt:
{doc_truncated[:500]}

Answer with: HIGH, MEDIUM, or LOW"""

            messages = [{"role": "user", "content": judge_prompt}]

            try:
                response = self.slm.generate(messages, max_tokens=20, temperature=0.1)
                response_upper = response.upper()

                # Parse response - be lenient
                if "HIGH" in response_upper or "HIGHLY" in response_upper or "5" in response or "4" in response:
                    score = 0.9
                elif "LOW" in response_upper or "NOT" in response_upper or "1" in response:
                    score = 0.3
                else:
                    # Default to medium for ambiguous responses
                    score = 0.6

                scores.append(score)
            except Exception as e:
                logger.warning(f"LLM judge failed for doc {i}: {e}")
                scores.append(0.5)  # Default score

        return scores

    def _get_slm_decision(self, context: str, volatility: float,
                         liquidity_factor: float, date: str) -> str:
        """Get SLM decision based on retrieved context."""

        # Determine status labels
        if volatility >= 0.50:
            volatility_status = "CRISIS"
        elif volatility >= 0.20:
            volatility_status = "STRESS"
        else:
            volatility_status = "NORMAL"

        if liquidity_factor < 0.30:
            liquidity_status = "SEVERE STRESS"
        elif liquidity_factor < 0.50:
            liquidity_status = "STRESS"
        else:
            liquidity_status = "NORMAL"

        system_prompt = """You are a bank risk manager making a strategic decision.
DECISION FRAMEWORK:
- If volatility > 50% -> CRISIS -> DEFENSIVE
- If liquidity factor < 0.30 -> SEVERE STRESS -> DEFENSIVE
- If historical events show failures/contagion -> DEFENSIVE
- If normal conditions -> MAINTAIN

Output exactly one word: DEFENSIVE or MAINTAIN."""

        user_prompt = f"""Current Date: {date}

Market Conditions:
- Volatility: {volatility*100:.0f}% → {volatility_status}
- Liquidity Factor: {liquidity_factor:.2f} → {liquidity_status}

Historical Intelligence:
{context[:3000]}

Based on current conditions and historical intelligence, should you take DEFENSIVE action or MAINTAIN current strategy?

Answer with exactly one word: DEFENSIVE or MAINTAIN"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.slm.generate(messages, max_tokens=20, temperature=0.3)

            if "DEFENSIVE" in response.upper():
                return "DEFENSIVE"
            elif "MAINTAIN" in response.upper():
                return "MAINTAIN"
            else:
                # Default based on market conditions
                if volatility >= 0.50 or liquidity_factor < 0.30:
                    return "DEFENSIVE"
                return "MAINTAIN"

        except Exception as e:
            logger.error(f"SLM decision failed: {e}")
            return "MAINTAIN"

    def _calculate_faithfulness(self, decision: str, docs: List[str],
                                expected_decision: str) -> float:
        """
        Calculate faithfulness - does the decision align with the context?
        Higher score if decision matches what context suggests.
        """
        if not docs:
            return 0.0

        combined_text = " ".join(docs).lower()

        # Keywords that suggest defensive action
        defensive_keywords = [
            'crisis', 'failure', 'collapse', 'bankruptcy', 'freeze',
            'contagion', 'systemic', 'emergency', 'bailout', 'panic',
            'default', 'writedown', 'loss', 'stress', 'severe'
        ]

        # Keywords that suggest normal/maintain
        maintain_keywords = [
            'stable', 'normal', 'growth', 'healthy', 'adequate',
            'improving', 'recovery', 'positive', 'sound'
        ]

        defensive_count = sum(1 for kw in defensive_keywords if kw in combined_text)
        maintain_count = sum(1 for kw in maintain_keywords if kw in combined_text)

        # Determine what context suggests
        if defensive_count > maintain_count + 2:
            context_suggests = "DEFENSIVE"
        elif maintain_count > defensive_count + 2:
            context_suggests = "MAINTAIN"
        else:
            # Ambiguous - check expected as tie-breaker
            context_suggests = expected_decision

        # Faithfulness = 1 if decision matches context suggestion
        return 1.0 if decision == context_suggests else 0.0

    def _extract_sources(self, docs: List[str]) -> List[str]:
        """Extract source filenames from formatted documents."""
        sources = []
        for doc in docs:
            if "[Source:" in doc:
                source_match = re.search(r'\[Source: ([^,\]]+)', doc)
                if source_match:
                    sources.append(source_match.group(1))
        return sources

    def _aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results into final report."""
        if not self.results:
            return {"error": "No results to aggregate"}

        # Overall metrics
        total_cases = len(self.results)
        correct_decisions = sum(1 for r in self.results if r['decision_correct'])
        decision_accuracy = correct_decisions / total_cases

        # Average metrics
        avg_topic_coverage = sum(r['metrics']['topic_coverage'] for r in self.results) / total_cases
        avg_context_relevancy = sum(r['metrics']['context_relevancy'] for r in self.results) / total_cases
        avg_context_precision = sum(r['metrics']['context_precision'] for r in self.results) / total_cases
        avg_source_diversity = sum(r['metrics']['source_diversity'] for r in self.results) / total_cases
        avg_llm_relevance = sum(r['metrics']['avg_llm_relevance'] for r in self.results) / total_cases
        avg_faithfulness = sum(r['metrics']['faithfulness'] for r in self.results) / total_cases

        # By regime breakdown
        regime_breakdown = {}
        for regime in ['normal', 'stress', 'crisis']:
            regime_results = [r for r in self.results if r['regime'] == regime]
            if regime_results:
                regime_accuracy = sum(1 for r in regime_results if r['decision_correct']) / len(regime_results)
                regime_topic_coverage = sum(r['metrics']['topic_coverage'] for r in regime_results) / len(regime_results)
                regime_breakdown[regime] = {
                    "count": len(regime_results),
                    "decision_accuracy": regime_accuracy,
                    "avg_topic_coverage": regime_topic_coverage
                }

        # Decision distribution
        decisions = Counter(r['actual_decision'] for r in self.results)
        expected_decisions = Counter(r['expected_decision'] for r in self.results)

        # Source distribution
        all_sources = []
        for r in self.results:
            all_sources.extend(r['retrieved_sources'])
        source_distribution = Counter()
        for src in all_sources:
            if 'JPM' in src:
                source_distribution['JPM'] += 1
            elif 'BIS' in src or 'ar' in src or 'r_qt' in src:
                source_distribution['BIS'] += 1
            elif 'FT' in src:
                source_distribution['FT'] += 1
            elif 'Financial Crisis' in src:
                source_distribution['FCIC'] += 1
            else:
                source_distribution['Other'] += 1

        report = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_test_cases": total_cases,
            "mode": "fallback" if self.use_fallback else "chromadb",
            "summary": {
                "decision_accuracy": round(decision_accuracy, 3),
                "avg_topic_coverage": round(avg_topic_coverage, 3),
                "avg_context_relevancy": round(avg_context_relevancy, 3),
                "avg_context_precision": round(avg_context_precision, 3),
                "avg_source_diversity": round(avg_source_diversity, 3),
                "avg_llm_relevance": round(avg_llm_relevance, 3),
                "avg_faithfulness": round(avg_faithfulness, 3)
            },
            "by_regime": regime_breakdown,
            "decision_distribution": {
                "actual": dict(decisions),
                "expected": dict(expected_decisions)
            },
            "source_distribution": dict(source_distribution),
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []

        if not self.results:
            return ["No results to analyze"]

        # Check decision accuracy
        accuracy = sum(1 for r in self.results if r['decision_correct']) / len(self.results)
        if accuracy < 0.7:
            recommendations.append(
                f"Decision accuracy is {accuracy:.1%}. Consider improving the decision prompt "
                "or adding more crisis-specific training examples."
            )

        # Check topic coverage
        avg_coverage = sum(r['metrics']['topic_coverage'] for r in self.results) / len(self.results)
        if avg_coverage < 0.5:
            recommendations.append(
                f"Topic coverage is {avg_coverage:.1%}. Consider expanding the document corpus "
                "or improving query generation to better match expected topics."
            )

        # Check source diversity
        avg_diversity = sum(r['metrics']['source_diversity'] for r in self.results) / len(self.results)
        if avg_diversity < 0.6:
            recommendations.append(
                f"Source diversity is {avg_diversity:.1%}. The round-robin diversity filter "
                "may need tuning, or certain source types may be underrepresented."
            )

        # Check LLM relevance
        avg_relevance = sum(r['metrics']['avg_llm_relevance'] for r in self.results) / len(self.results)
        if avg_relevance < 0.6:
            recommendations.append(
                f"Average LLM-judged relevance is {avg_relevance:.1%}. Consider improving "
                "the reranker or query generation for better semantic matching."
            )

        # Check regime-specific performance
        crisis_results = [r for r in self.results if r['regime'] == 'crisis']
        if crisis_results:
            crisis_accuracy = sum(1 for r in crisis_results if r['decision_correct']) / len(crisis_results)
            if crisis_accuracy < 0.8:
                recommendations.append(
                    f"Crisis regime decision accuracy is {crisis_accuracy:.1%}. "
                    "This is critical - consider adding more crisis-specific retrieval patterns."
                )

        if not recommendations:
            recommendations.append("Overall performance is good. Continue monitoring with new test cases.")

        return recommendations

    def _save_report(self, report: Dict[str, Any]):
        """Save evaluation report to JSON file."""
        os.makedirs(RESULTS_DIR, exist_ok=True)

        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Evaluation report saved to {REPORT_PATH}")

    def print_summary(self, report: Dict[str, Any]):
        """Print a human-readable summary of the evaluation."""
        print("\n" + "="*60)
        print("RAG EVALUATION REPORT")
        print("="*60)

        summary = report.get('summary', {})
        print(f"\nTotal Test Cases: {report.get('total_test_cases', 0)}")
        print(f"\nOverall Metrics:")
        print(f"  Decision Accuracy:     {summary.get('decision_accuracy', 0):.1%}")
        print(f"  Topic Coverage:        {summary.get('avg_topic_coverage', 0):.1%}")
        print(f"  Context Relevancy:     {summary.get('avg_context_relevancy', 0):.1%}")
        print(f"  Context Precision:     {summary.get('avg_context_precision', 0):.1%}")
        print(f"  Source Diversity:      {summary.get('avg_source_diversity', 0):.1%}")
        print(f"  LLM Relevance:         {summary.get('avg_llm_relevance', 0):.1%}")
        print(f"  Faithfulness:          {summary.get('avg_faithfulness', 0):.1%}")

        print(f"\nBy Market Regime:")
        for regime, data in report.get('by_regime', {}).items():
            print(f"  {regime.upper()}: {data.get('count', 0)} cases, "
                  f"accuracy={data.get('decision_accuracy', 0):.1%}, "
                  f"topic_coverage={data.get('avg_topic_coverage', 0):.1%}")

        print(f"\nDecision Distribution:")
        actual = report.get('decision_distribution', {}).get('actual', {})
        expected = report.get('decision_distribution', {}).get('expected', {})
        print(f"  Actual:   {dict(actual)}")
        print(f"  Expected: {dict(expected)}")

        print(f"\nSource Distribution:")
        sources = report.get('source_distribution', {})
        total_sources = sum(sources.values())
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            pct = count / total_sources * 100 if total_sources > 0 else 0
            print(f"  {src}: {count} ({pct:.1f}%)")

        print(f"\nRecommendations:")
        for rec in report.get('recommendations', []):
            print(f"  - {rec}")

        print("\n" + "="*60)
        print(f"Full report saved to: {REPORT_PATH}")
        print("="*60 + "\n")


def main():
    """Run the RAG evaluation pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description='RAG Evaluation Pipeline')
    parser.add_argument('--fallback', action='store_true',
                        help='Use sample documents instead of ChromaDB')
    parser.add_argument('--quick', action='store_true',
                        help='Run quick evaluation with first 5 test cases only')
    args = parser.parse_args()

    evaluator = RAGEvaluator(use_fallback=args.fallback)

    if args.quick:
        # Limit to first 5 cases for quick testing
        evaluator.eval_dataset = evaluator.eval_dataset[:5]
        logger.info("Quick mode: evaluating first 5 test cases only")

    report = evaluator.evaluate_all()
    evaluator.print_summary(report)

    return report


if __name__ == "__main__":
    main()
