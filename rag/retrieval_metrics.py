"""
Retrieval Quality Evaluation Metrics for RAG Pipeline

Implements standard Information Retrieval metrics:
- Precision@k (k=1, 3, 5, 10)
- Recall@k
- NDCG@k (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)

These metrics require ground truth relevance labels to evaluate retrieval quality.

Usage:
    from rag.retrieval_metrics import RetrievalMetrics

    metrics = RetrievalMetrics()
    results = metrics.evaluate_query(retrieved_docs, relevant_doc_ids, k=10)
"""

import math
from typing import List, Dict, Any, Optional, Set, Union
import logging

logger = logging.getLogger(__name__)


class RetrievalMetrics:
    """
    Standard Information Retrieval metrics for evaluating retrieval quality.

    All metrics expect:
    - retrieved_ids: List of document IDs in ranked order (position 0 = rank 1)
    - relevant_ids: Set of document IDs that are relevant to the query
    - relevance_scores: Optional dict mapping doc_id -> graded relevance (for NDCG)
    """

    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Calculate Precision@k: fraction of retrieved documents that are relevant.

        Precision@k = |{relevant documents in top-k}| / k

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)
            k: Number of top results to consider

        Returns:
            Precision@k score in range [0, 1]
        """
        if k <= 0:
            return 0.0

        top_k = retrieved_ids[:k]
        relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_in_top_k / k

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Calculate Recall@k: fraction of relevant documents that are retrieved.

        Recall@k = |{relevant documents in top-k}| / |{all relevant documents}|

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)
            k: Number of top results to consider

        Returns:
            Recall@k score in range [0, 1]
        """
        if not relevant_ids:
            return 1.0  # If no relevant docs exist, recall is trivially 1

        top_k = retrieved_ids[:k]
        relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_in_top_k / len(relevant_ids)

    @staticmethod
    def mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR) for a single query.

        MRR = 1 / rank_of_first_relevant_document

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)

        Returns:
            Reciprocal rank in range [0, 1], or 0 if no relevant doc found
        """
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def dcg_at_k(
        retrieved_ids: List[str],
        relevance_scores: Dict[str, float],
        k: int
    ) -> float:
        """
        Calculate Discounted Cumulative Gain at k.

        DCG@k = sum_{i=1}^{k} (2^{rel_i} - 1) / log_2(i + 1)

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevance_scores: Dict mapping doc_id -> relevance score (0-3 typically)
            k: Number of top results to consider

        Returns:
            DCG@k score (unbounded, higher is better)
        """
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k], start=1):
            rel = relevance_scores.get(doc_id, 0)
            # Using the alternative DCG formula: (2^rel - 1) / log2(i + 1)
            dcg += (2 ** rel - 1) / math.log2(i + 1)
        return dcg

    @staticmethod
    def ndcg_at_k(
        retrieved_ids: List[str],
        relevance_scores: Dict[str, float],
        k: int
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at k.

        NDCG@k = DCG@k / IDCG@k

        Where IDCG is the DCG of the ideal ranking (sorted by relevance).

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevance_scores: Dict mapping doc_id -> relevance score
            k: Number of top results to consider

        Returns:
            NDCG@k score in range [0, 1]
        """
        # Calculate DCG
        dcg = RetrievalMetrics.dcg_at_k(retrieved_ids, relevance_scores, k)

        # Calculate IDCG (ideal DCG)
        # Sort all docs by relevance to get ideal ranking
        ideal_ranking = sorted(
            relevance_scores.keys(),
            key=lambda x: relevance_scores[x],
            reverse=True
        )
        idcg = RetrievalMetrics.dcg_at_k(ideal_ranking, relevance_scores, k)

        if idcg == 0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def average_precision(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
        """
        Calculate Average Precision (AP) for a single query.

        AP = (1/R) * sum_{k=1}^{n} (P@k * rel_k)

        Where R is the total number of relevant documents.

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)

        Returns:
            Average Precision score in range [0, 1]
        """
        if not relevant_ids:
            return 1.0

        relevant_count = 0
        precision_sum = 0.0

        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                relevant_count += 1
                precision_at_rank = relevant_count / rank
                precision_sum += precision_at_rank

        if relevant_count == 0:
            return 0.0

        return precision_sum / len(relevant_ids)

    @staticmethod
    def f1_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
        """
        Calculate F1 score at k (harmonic mean of precision and recall).

        F1@k = 2 * (P@k * R@k) / (P@k + R@k)

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)
            k: Number of top results to consider

        Returns:
            F1@k score in range [0, 1]
        """
        precision = RetrievalMetrics.precision_at_k(retrieved_ids, relevant_ids, k)
        recall = RetrievalMetrics.recall_at_k(retrieved_ids, relevant_ids, k)

        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def evaluate_query(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        relevance_scores: Optional[Dict[str, float]] = None,
        k_values: List[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single query across all metrics.

        Args:
            retrieved_ids: List of retrieved document IDs in ranked order
            relevant_ids: Set of relevant document IDs (ground truth)
            relevance_scores: Optional graded relevance scores for NDCG
            k_values: List of k values to evaluate (default: [1, 3, 5, 10])

        Returns:
            Dictionary with all metric scores
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]

        # Convert relevant_ids to set if needed
        if not isinstance(relevant_ids, set):
            relevant_ids = set(relevant_ids)

        # Create binary relevance scores if not provided
        if relevance_scores is None:
            relevance_scores = {doc_id: 1 for doc_id in relevant_ids}

        results = {
            "mrr": self.mrr(retrieved_ids, relevant_ids),
            "average_precision": self.average_precision(retrieved_ids, relevant_ids),
            "num_retrieved": len(retrieved_ids),
            "num_relevant": len(relevant_ids)
        }

        # Calculate metrics at each k
        for k in k_values:
            results[f"precision@{k}"] = self.precision_at_k(retrieved_ids, relevant_ids, k)
            results[f"recall@{k}"] = self.recall_at_k(retrieved_ids, relevant_ids, k)
            results[f"ndcg@{k}"] = self.ndcg_at_k(retrieved_ids, relevance_scores, k)
            results[f"f1@{k}"] = self.f1_at_k(retrieved_ids, relevant_ids, k)

        return results

    def evaluate_queries(
        self,
        query_results: List[Dict[str, Any]],
        k_values: List[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate multiple queries and compute aggregate metrics.

        Args:
            query_results: List of dicts, each containing:
                - 'retrieved_ids': List of retrieved doc IDs
                - 'relevant_ids': Set of relevant doc IDs
                - 'relevance_scores': Optional graded relevance
            k_values: List of k values to evaluate

        Returns:
            Dictionary with per-query results and aggregate metrics
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]

        all_results = []

        for query_data in query_results:
            result = self.evaluate_query(
                retrieved_ids=query_data['retrieved_ids'],
                relevant_ids=query_data['relevant_ids'],
                relevance_scores=query_data.get('relevance_scores'),
                k_values=k_values
            )
            all_results.append(result)

        # Aggregate metrics (mean across queries)
        aggregate = {}
        if all_results:
            metric_keys = all_results[0].keys()
            for key in metric_keys:
                if key not in ['num_retrieved', 'num_relevant']:
                    values = [r[key] for r in all_results]
                    aggregate[f"mean_{key}"] = sum(values) / len(values)

        # Calculate MAP (Mean Average Precision)
        aggregate["map"] = aggregate.get("mean_average_precision", 0.0)

        return {
            "per_query": all_results,
            "aggregate": aggregate,
            "num_queries": len(all_results)
        }


def extract_doc_id_from_context(context: str) -> Optional[str]:
    """
    Extract document ID from formatted context string.

    The context format is:
    [Source: filename.pdf, Date: YYYY-MM-DD, Page: N]
    content...

    Args:
        context: Formatted context string from retriever

    Returns:
        Document ID (source filename) or None if not found
    """
    import re
    match = re.search(r'\[Source:\s*([^,\]]+)', context)
    if match:
        return match.group(1).strip()
    return None


def create_doc_id(source: str, page: int = 0) -> str:
    """
    Create a unique document ID from source and page.

    Args:
        source: Source filename
        page: Page number (default 0)

    Returns:
        Unique document identifier
    """
    import os
    basename = os.path.basename(source)
    return f"{basename}:p{page}"
