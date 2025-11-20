"""
FE-EKG Event Evolution Module

Implements the 6 evolution methods from the paper:
1. Temporal Correlation (TCDI)
2. Entity Overlap
3. Semantic Similarity
4. Topic Relevance
5. Event Type Causality
6. Emotional Consistency
"""

from .methods import EventEvolutionScorer, compute_all_evolution_links

__all__ = ['EventEvolutionScorer', 'compute_all_evolution_links']
