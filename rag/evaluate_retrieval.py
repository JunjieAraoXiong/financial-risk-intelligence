#!/usr/bin/env python3
"""
RAG Retrieval Quality Evaluation Script

Benchmarks the retrieval pipeline using standard IR metrics:
- Precision@k (k=1, 3, 5, 10)
- Recall@k
- NDCG@k (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)
- MAP (Mean Average Precision)

Usage:
    python rag/evaluate_retrieval.py
    python rag/evaluate_retrieval.py --k-values 1 3 5 10 20
    python rag/evaluate_retrieval.py --output results/retrieval_metrics.json
    python rag/evaluate_retrieval.py --fallback  # Use sample docs for testing

The script uses a labeled evaluation dataset with ground truth relevance patterns
to assess retrieval quality across diverse financial crisis queries.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retrieval_metrics import RetrievalMetrics, extract_doc_id_from_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
EVAL_DATASET_PATH = "rag/eval/retrieval_eval_dataset.json"
DEFAULT_OUTPUT_PATH = "results/retrieval_quality_report.json"

# Sample documents for fallback/testing mode
SAMPLE_DOCS = [
    """[Source: JPM_Weekly_2008-09-15.pdf, Date: 2008-09-15, Page: 1]
    EMERGENCY MARKET UPDATE - September 15, 2008
    Lehman Brothers has filed for Chapter 11 bankruptcy, the largest bankruptcy filing in U.S. history.
    Markets are in severe distress with the VIX spiking above 80. Interbank lending has effectively frozen.
    The Federal Reserve is considering emergency liquidity facilities. Counterparty risk at extreme levels.""",

    """[Source: BIS_Quarterly_2008-09.pdf, Date: 2008-09-28, Page: 23]
    The collapse of Lehman Brothers triggered a global liquidity crisis. Credit default swap spreads widened
    dramatically. The commercial paper market effectively shut down. Central banks worldwide coordinating
    emergency interventions. Systemic risk has reached unprecedented levels. Contagion spreading rapidly.""",

    """[Source: FCIC_Report.pdf, Date: 2008-09-20, Page: 156]
    The week of September 15, 2008 marked the peak of the financial crisis. Following Lehman's bankruptcy,
    AIG required emergency government assistance. Money market funds broke the buck triggering massive
    redemptions. The Treasury implemented TARP to recapitalize banks. Inadequate liquidity management.""",

    """[Source: FT_Article_2008-09-18.json, Date: 2008-09-18, Page: 0]
    Global stock markets plunged as panic spread following Lehman's collapse. Goldman Sachs and Morgan Stanley
    face severe pressure. Banks worldwide hoarding liquidity. TED spread reached 3% indicating extreme stress.
    Volatility index VIX at record highs. Investor confidence collapsed.""",

    """[Source: JPM_Weekly_2008-03-17.pdf, Date: 2008-03-17, Page: 2]
    Bear Stearns collapsed over the weekend and was acquired by JPMorgan Chase with Federal Reserve backing.
    The Fed opened the discount window to investment banks for the first time since the Great Depression.
    Market volatility elevated with concerns about additional failures. Credit crisis escalating.""",

    """[Source: BIS_Annual_2008.pdf, Date: 2008-12-31, Page: 45]
    The 2008 financial crisis exposed severe weaknesses in bank capital adequacy frameworks. Basel II
    requirements proved insufficient. Tier 1 capital ratios declined sharply across major institutions.
    Regulatory capital needs urgent review. Leverage ratios critically important.""",

    """[Source: JPM_Weekly_2008-10-03.pdf, Date: 2008-10-03, Page: 1]
    Treasury Secretary Paulson secured Congressional approval for TARP - the Troubled Asset Relief Program.
    $700 billion authorized for bank bailouts and capital injections. Government intervention unprecedented
    in scale. Capital adequacy concerns drove emergency recapitalization efforts.""",

    """[Source: BIS_Quarterly_2007-09.pdf, Date: 2007-09-15, Page: 12]
    Northern Rock experienced first UK bank run in 150 years. Depositors queued to withdraw savings after
    Bank of England emergency support announced. Subprime mortgage exposure triggered liquidity crisis.
    Funding model reliance on wholesale markets proved fatal vulnerability.""",

    """[Source: JPM_Weekly_2008-09-22.pdf, Date: 2008-09-22, Page: 1]
    Goldman Sachs and Morgan Stanley converted to bank holding companies, ending era of independent
    investment banks. Federal Reserve approved conversion to allow access to Fed lending facilities.
    Surviving investment banks seeking regulatory protection. Historic transformation of Wall Street.""",

    """[Source: FCIC_Report.pdf, Date: 2008-09-16, Page: 340]
    AIG's massive exposure to credit default swaps on mortgage backed securities MBS required
    $85 billion government rescue. Counterparty risk across financial system. CDO losses accelerating.
    Derivatives exposure far exceeded capital reserves. Subprime mortgage losses devastated balance sheets.""",

    """[Source: BIS_Quarterly_2008-06.pdf, Date: 2008-06-30, Page: 8]
    Credit rating agencies under scrutiny for downgrade delays. Moody's and S&P facing criticism for
    structured product ratings. Multiple downgrades of financial institutions. Rating methodology
    failed to capture systemic risk. Investment grade ratings proved unreliable.""",

    """[Source: JPM_Weekly_2008-09-17.pdf, Date: 2008-09-17, Page: 3]
    Reserve Primary Fund broke the buck - first money market fund to do so since 1994. NAV fell below
    $1 due to Lehman commercial paper holdings. Massive redemptions across money market industry.
    Treasury forced to guarantee money market funds to prevent systemic collapse.""",

    """[Source: BIS_Annual_2007.pdf, Date: 2007-12-31, Page: 28]
    Interbank lending markets showing signs of severe stress. LIBOR-OIS spread widening significantly.
    TED spread indicating growing counterparty concerns. Liquidity hoarding behavior emerging among
    major banks. Short-term funding markets increasingly dysfunctional.""",

    """[Source: JPM_Weekly_2007-02-12.pdf, Date: 2007-02-12, Page: 1]
    Market conditions remain favorable with steady economic growth. Credit spreads tight and
    liquidity abundant. Banking sector profitability strong. Current outlook supports maintaining
    existing positions. Normal market volatility. Stable funding conditions.""",

    """[Source: BIS_Annual_2006.pdf, Date: 2006-12-31, Page: 45]
    Global banking system resilient with strong capital ratios across major institutions.
    Credit conditions healthy with adequate lending standards. Economic indicators suggest
    continued stable growth. Normal operations. Regulatory compliance satisfactory."""
]


class RetrievalEvaluator:
    """
    Evaluator for RAG retrieval quality using IR metrics.

    Uses pattern-based relevance scoring to compare retrieved documents
    against ground truth definitions in the evaluation dataset.
    """

    def __init__(self, use_fallback: bool = False):
        """
        Initialize the evaluator.

        Args:
            use_fallback: If True, use sample documents instead of ChromaDB
        """
        self.use_fallback = use_fallback
        self.retriever = None
        self.metrics = RetrievalMetrics()

        if not use_fallback:
            try:
                from rag.retriever import RAGRetriever
                self.retriever = RAGRetriever()
                logger.info("ChromaDB retriever initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize retriever: {e}")
                logger.warning("Falling back to sample documents mode")
                self.use_fallback = True

        if self.use_fallback:
            logger.info("Using fallback mode with sample documents")

        # Load evaluation dataset
        self.eval_dataset = self._load_eval_dataset()

    def _load_eval_dataset(self) -> Dict[str, Any]:
        """Load the evaluation dataset from JSON."""
        if not os.path.exists(EVAL_DATASET_PATH):
            logger.error(f"Evaluation dataset not found at {EVAL_DATASET_PATH}")
            return {"queries": []}

        with open(EVAL_DATASET_PATH, 'r') as f:
            dataset = json.load(f)

        logger.info(f"Loaded {len(dataset.get('queries', []))} evaluation queries")
        return dataset

    def _retrieve_documents(self, query: str, k: int = 20) -> List[str]:
        """
        Retrieve documents for a query.

        Args:
            query: The search query
            k: Number of documents to retrieve

        Returns:
            List of retrieved document strings
        """
        if self.use_fallback:
            # Return sample docs (simulate retrieval by keyword matching)
            return self._fallback_retrieve(query, k)

        try:
            # Use the actual retriever
            docs = self.retriever.get_relevant_context(query, k=k)
            return docs
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    def _fallback_retrieve(self, query: str, k: int) -> List[str]:
        """
        Simple keyword-based retrieval for fallback mode.

        Args:
            query: The search query
            k: Number of documents to return

        Returns:
            List of documents sorted by keyword overlap
        """
        query_words = set(query.lower().split())

        # Score each document by keyword overlap
        scored_docs = []
        for doc in SAMPLE_DOCS:
            doc_lower = doc.lower()
            score = sum(1 for word in query_words if word in doc_lower)
            scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored_docs[:k]]

    def _score_document_relevance(
        self,
        doc: str,
        relevant_patterns: Dict[str, List[Dict]],
        negative_keywords: List[str]
    ) -> Tuple[int, str]:
        """
        Score a document's relevance based on pattern matching.

        Args:
            doc: The document text
            relevant_patterns: Dict with 'highly_relevant', 'relevant', 'marginally_relevant' patterns
            negative_keywords: Keywords that indicate non-relevance

        Returns:
            Tuple of (relevance_score, doc_id)
        """
        doc_lower = doc.lower()
        doc_id = extract_doc_id_from_context(doc) or f"doc_{hash(doc[:100])}"

        # Check for negative keywords (strong signal of non-relevance)
        negative_count = sum(1 for kw in negative_keywords if kw.lower() in doc_lower)
        if negative_count >= 2:
            return 0, doc_id

        # Check highly relevant patterns (score 3)
        for pattern_def in relevant_patterns.get('highly_relevant', []):
            pattern = pattern_def.get('pattern', '').lower()
            keywords = [kw.lower() for kw in pattern_def.get('keywords', [])]

            if pattern in doc_lower:
                keyword_matches = sum(1 for kw in keywords if kw in doc_lower)
                if keyword_matches >= 2:
                    return 3, doc_id

        # Check relevant patterns (score 2)
        for pattern_def in relevant_patterns.get('relevant', []):
            pattern = pattern_def.get('pattern', '').lower()
            keywords = [kw.lower() for kw in pattern_def.get('keywords', [])]

            if pattern in doc_lower:
                keyword_matches = sum(1 for kw in keywords if kw in doc_lower)
                if keyword_matches >= 1:
                    return 2, doc_id

        # Check marginally relevant patterns (score 1)
        for pattern_def in relevant_patterns.get('marginally_relevant', []):
            pattern = pattern_def.get('pattern', '').lower()
            keywords = [kw.lower() for kw in pattern_def.get('keywords', [])]

            if pattern in doc_lower:
                keyword_matches = sum(1 for kw in keywords if kw in doc_lower)
                if keyword_matches >= 1:
                    return 1, doc_id

        return 0, doc_id

    def evaluate_query(
        self,
        query_def: Dict[str, Any],
        k_values: List[int]
    ) -> Dict[str, Any]:
        """
        Evaluate a single query.

        Args:
            query_def: Query definition from eval dataset
            k_values: List of k values for metrics

        Returns:
            Dictionary with query results and metrics
        """
        query_id = query_def['id']
        query = query_def['query']
        relevant_patterns = query_def.get('relevant_documents', {})
        negative_keywords = query_def.get('negative_keywords', [])

        logger.info(f"Evaluating query {query_id}: {query[:50]}...")

        # Retrieve documents (get max k)
        max_k = max(k_values)
        retrieved_docs = self._retrieve_documents(query, k=max_k)

        if not retrieved_docs:
            logger.warning(f"No documents retrieved for query {query_id}")
            return {
                "query_id": query_id,
                "query": query,
                "error": "No documents retrieved",
                "metrics": {}
            }

        # Score each retrieved document
        retrieved_ids = []
        relevance_scores = {}
        relevant_ids = set()

        for doc in retrieved_docs:
            score, doc_id = self._score_document_relevance(
                doc, relevant_patterns, negative_keywords
            )
            # Make IDs unique by adding index if duplicate
            original_id = doc_id
            counter = 1
            while doc_id in retrieved_ids:
                doc_id = f"{original_id}_{counter}"
                counter += 1

            retrieved_ids.append(doc_id)
            relevance_scores[doc_id] = score

            if score > 0:
                relevant_ids.add(doc_id)

        # Calculate metrics
        query_metrics = self.metrics.evaluate_query(
            retrieved_ids=retrieved_ids,
            relevant_ids=relevant_ids,
            relevance_scores=relevance_scores,
            k_values=k_values
        )

        # Add additional context
        result = {
            "query_id": query_id,
            "query": query,
            "category": query_def.get('category', 'unknown'),
            "date_context": query_def.get('date_context', ''),
            "num_retrieved": len(retrieved_docs),
            "num_relevant_found": len(relevant_ids),
            "relevance_distribution": {
                "score_3": sum(1 for s in relevance_scores.values() if s == 3),
                "score_2": sum(1 for s in relevance_scores.values() if s == 2),
                "score_1": sum(1 for s in relevance_scores.values() if s == 1),
                "score_0": sum(1 for s in relevance_scores.values() if s == 0)
            },
            "metrics": query_metrics,
            "retrieved_doc_ids": retrieved_ids[:10],  # First 10 for review
            "retrieved_scores": [relevance_scores.get(doc_id, 0) for doc_id in retrieved_ids[:10]]
        }

        return result

    def evaluate_all(self, k_values: List[int] = None) -> Dict[str, Any]:
        """
        Evaluate all queries in the dataset.

        Args:
            k_values: List of k values for metrics (default: [1, 3, 5, 10])

        Returns:
            Complete evaluation report
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]

        queries = self.eval_dataset.get('queries', [])
        if not queries:
            return {"error": "No queries to evaluate"}

        logger.info(f"Evaluating {len(queries)} queries with k values: {k_values}")

        results = []
        for query_def in queries:
            result = self.evaluate_query(query_def, k_values)
            results.append(result)

        # Aggregate metrics
        aggregate = self._aggregate_metrics(results, k_values)

        # Generate report
        report = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "mode": "fallback" if self.use_fallback else "chromadb",
            "num_queries": len(results),
            "k_values": k_values,
            "aggregate_metrics": aggregate,
            "by_category": self._metrics_by_category(results, k_values),
            "per_query_results": results,
            "recommendations": self._generate_recommendations(aggregate, k_values)
        }

        return report

    def _aggregate_metrics(
        self,
        results: List[Dict],
        k_values: List[int]
    ) -> Dict[str, float]:
        """Aggregate metrics across all queries."""
        aggregate = {}

        # Filter out failed queries
        valid_results = [r for r in results if 'error' not in r]
        if not valid_results:
            return {"error": "All queries failed"}

        n = len(valid_results)

        # MRR
        mrr_values = [r['metrics'].get('mrr', 0) for r in valid_results]
        aggregate['mrr'] = round(sum(mrr_values) / n, 4)

        # MAP
        ap_values = [r['metrics'].get('average_precision', 0) for r in valid_results]
        aggregate['map'] = round(sum(ap_values) / n, 4)

        # Per-k metrics
        for k in k_values:
            # Precision@k
            p_values = [r['metrics'].get(f'precision@{k}', 0) for r in valid_results]
            aggregate[f'precision@{k}'] = round(sum(p_values) / n, 4)

            # Recall@k
            r_values = [r['metrics'].get(f'recall@{k}', 0) for r in valid_results]
            aggregate[f'recall@{k}'] = round(sum(r_values) / n, 4)

            # NDCG@k
            ndcg_values = [r['metrics'].get(f'ndcg@{k}', 0) for r in valid_results]
            aggregate[f'ndcg@{k}'] = round(sum(ndcg_values) / n, 4)

            # F1@k
            f1_values = [r['metrics'].get(f'f1@{k}', 0) for r in valid_results]
            aggregate[f'f1@{k}'] = round(sum(f1_values) / n, 4)

        return aggregate

    def _metrics_by_category(
        self,
        results: List[Dict],
        k_values: List[int]
    ) -> Dict[str, Dict]:
        """Group metrics by query category."""
        categories = {}

        for result in results:
            if 'error' in result:
                continue

            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        # Aggregate per category
        category_metrics = {}
        for category, cat_results in categories.items():
            category_metrics[category] = {
                'count': len(cat_results),
                'metrics': self._aggregate_metrics(cat_results, k_values)
            }

        return category_metrics

    def _generate_recommendations(
        self,
        aggregate: Dict[str, float],
        k_values: List[int]
    ) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []

        # Check MRR
        mrr = aggregate.get('mrr', 0)
        if mrr < 0.5:
            recommendations.append(
                f"MRR is {mrr:.2f} (below 0.5). Consider improving query understanding "
                "or adding query expansion to surface relevant docs earlier."
            )

        # Check Precision@1
        p1 = aggregate.get('precision@1', 0)
        if p1 < 0.6:
            recommendations.append(
                f"Precision@1 is {p1:.2f}. The top result is often not relevant. "
                "Consider improving the reranker or adding semantic similarity boosting."
            )

        # Check NDCG@5
        ndcg5 = aggregate.get('ndcg@5', 0)
        if ndcg5 < 0.5:
            recommendations.append(
                f"NDCG@5 is {ndcg5:.2f}. Ranking quality needs improvement. "
                "Consider fine-tuning the reranker on financial domain data."
            )

        # Check Recall@10
        r10 = aggregate.get('recall@10', 0)
        if r10 < 0.7:
            recommendations.append(
                f"Recall@10 is {r10:.2f}. Many relevant docs are not being retrieved. "
                "Consider query expansion, HyDE, or multi-query strategies."
            )

        # Check MAP
        map_score = aggregate.get('map', 0)
        if map_score < 0.4:
            recommendations.append(
                f"MAP is {map_score:.2f}. Overall precision across ranks is low. "
                "Review embedding model quality and consider domain-specific fine-tuning."
            )

        if not recommendations:
            recommendations.append(
                "Retrieval quality metrics are within acceptable ranges. "
                "Continue monitoring with additional test queries."
            )

        return recommendations


def print_report(report: Dict[str, Any]) -> None:
    """Print a formatted evaluation report."""
    print("\n" + "=" * 70)
    print("RAG RETRIEVAL QUALITY EVALUATION REPORT")
    print("=" * 70)

    print(f"\nTimestamp: {report.get('evaluation_timestamp', 'N/A')}")
    print(f"Mode: {report.get('mode', 'N/A')}")
    print(f"Queries Evaluated: {report.get('num_queries', 0)}")
    print(f"K Values: {report.get('k_values', [])}")

    print("\n" + "-" * 70)
    print("AGGREGATE METRICS")
    print("-" * 70)

    aggregate = report.get('aggregate_metrics', {})

    # Print MRR and MAP
    print(f"\n  MRR (Mean Reciprocal Rank):     {aggregate.get('mrr', 0):.4f}")
    print(f"  MAP (Mean Average Precision):   {aggregate.get('map', 0):.4f}")

    # Print table of per-k metrics
    k_values = report.get('k_values', [1, 3, 5, 10])

    print("\n  Metrics at different k values:")
    print(f"  {'k':>5} | {'P@k':>8} | {'R@k':>8} | {'NDCG@k':>8} | {'F1@k':>8}")
    print(f"  {'-'*5} | {'-'*8} | {'-'*8} | {'-'*8} | {'-'*8}")

    for k in k_values:
        p = aggregate.get(f'precision@{k}', 0)
        r = aggregate.get(f'recall@{k}', 0)
        ndcg = aggregate.get(f'ndcg@{k}', 0)
        f1 = aggregate.get(f'f1@{k}', 0)
        print(f"  {k:>5} | {p:>8.4f} | {r:>8.4f} | {ndcg:>8.4f} | {f1:>8.4f}")

    # Print by category
    print("\n" + "-" * 70)
    print("METRICS BY CATEGORY")
    print("-" * 70)

    by_category = report.get('by_category', {})
    for category, data in sorted(by_category.items()):
        count = data.get('count', 0)
        metrics = data.get('metrics', {})
        mrr = metrics.get('mrr', 0)
        p5 = metrics.get('precision@5', 0)
        ndcg5 = metrics.get('ndcg@5', 0)
        print(f"\n  {category} ({count} queries):")
        print(f"    MRR: {mrr:.4f} | P@5: {p5:.4f} | NDCG@5: {ndcg5:.4f}")

    # Print recommendations
    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)

    for rec in report.get('recommendations', []):
        print(f"\n  - {rec}")

    # Print sample query results
    print("\n" + "-" * 70)
    print("SAMPLE QUERY RESULTS (First 3)")
    print("-" * 70)

    per_query = report.get('per_query_results', [])[:3]
    for result in per_query:
        print(f"\n  Query: {result.get('query', 'N/A')[:60]}...")
        print(f"  Category: {result.get('category', 'N/A')}")
        metrics = result.get('metrics', {})
        print(f"  MRR: {metrics.get('mrr', 0):.4f} | P@5: {metrics.get('precision@5', 0):.4f}")
        dist = result.get('relevance_distribution', {})
        print(f"  Relevance: 3={dist.get('score_3', 0)}, 2={dist.get('score_2', 0)}, "
              f"1={dist.get('score_1', 0)}, 0={dist.get('score_0', 0)}")

    print("\n" + "=" * 70)


def main():
    """Run retrieval quality evaluation."""
    parser = argparse.ArgumentParser(
        description='Evaluate RAG retrieval quality using IR metrics'
    )
    parser.add_argument(
        '--k-values',
        type=int,
        nargs='+',
        default=[1, 3, 5, 10],
        help='K values for Precision@k, Recall@k, NDCG@k (default: 1 3 5 10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f'Output path for JSON report (default: {DEFAULT_OUTPUT_PATH})'
    )
    parser.add_argument(
        '--fallback',
        action='store_true',
        help='Use sample documents instead of ChromaDB (for testing)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only output JSON report, no console summary'
    )

    args = parser.parse_args()

    # Run evaluation
    evaluator = RetrievalEvaluator(use_fallback=args.fallback)
    report = evaluator.evaluate_all(k_values=args.k_values)

    # Save report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {args.output}")

    # Print summary
    if not args.quiet:
        print_report(report)

    # Return exit code based on quality
    aggregate = report.get('aggregate_metrics', {})
    mrr = aggregate.get('mrr', 0)
    map_score = aggregate.get('map', 0)

    if mrr < 0.3 or map_score < 0.2:
        logger.warning("Retrieval quality is below acceptable thresholds")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
