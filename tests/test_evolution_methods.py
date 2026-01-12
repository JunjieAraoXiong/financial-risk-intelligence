"""
Unit tests for the Event Evolution Methods module

Tests cover:
- EventEvolutionScorer class with all 6 scoring algorithms
- compute_all_evolution_links function
- Edge cases (empty inputs, same event, future dates, etc.)
"""

import pytest
import math
from datetime import datetime, timedelta

from feekg_core.evolution.methods import (
    EventEvolutionScorer,
    compute_all_evolution_links,
)


# =============================================================================
# Fixtures - Sample test data
# =============================================================================

@pytest.fixture
def sample_entities():
    """Basic entities for testing"""
    return [
        {'entityId': 'ent_company_a', 'name': 'Company A'},
        {'entityId': 'ent_company_b', 'name': 'Company B'},
        {'entityId': 'ent_regulator', 'name': 'Financial Regulator'},
        {'entityId': 'ent_rating_agency', 'name': 'Rating Agency'},
        {'entityId': 'ent_bank', 'name': 'Bank'},
    ]


@pytest.fixture
def sample_events():
    """Basic events for testing - ordered chronologically"""
    return [
        {
            'eventId': 'evt_001',
            'type': 'regulatory_pressure',
            'date': '2021-01-01',
            'actor': 'ent_regulator',
            'target': 'ent_company_a',
            'description': 'New regulations introduced for financial sector compliance'
        },
        {
            'eventId': 'evt_002',
            'type': 'liquidity_warning',
            'date': '2021-01-15',
            'actor': 'ent_company_a',
            'target': None,
            'description': 'Company warns of liquidity problems and potential cash shortage'
        },
        {
            'eventId': 'evt_003',
            'type': 'credit_downgrade',
            'date': '2021-01-20',
            'actor': 'ent_rating_agency',
            'target': 'ent_company_a',
            'description': 'Credit rating downgraded due to financial problems'
        },
        {
            'eventId': 'evt_004',
            'type': 'debt_default',
            'date': '2021-02-01',
            'actor': 'ent_company_a',
            'target': 'ent_bank',
            'description': 'Company defaults on debt obligations to bank'
        },
        {
            'eventId': 'evt_005',
            'type': 'stock_crash',
            'date': '2021-02-05',
            'actor': 'ent_company_a',
            'target': None,
            'description': 'Stock price crashes following default announcement'
        },
    ]


@pytest.fixture
def scorer(sample_events, sample_entities):
    """Pre-configured EventEvolutionScorer"""
    return EventEvolutionScorer(sample_events, sample_entities)


# =============================================================================
# Tests for Temporal Correlation (TCDI)
# =============================================================================

class TestTemporalCorrelation:
    """Tests for compute_temporal_correlation method"""

    def test_normal_case_within_window(self, scorer):
        """Events within temporal window should have positive score"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-15', 'eventId': 'evt_b'}  # 14 days later

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        # TCDI = K * e^(-alpha * delta) = 1.0 * e^(-0.1 * 14) = ~0.247
        assert score > 0
        assert score <= 1.0
        expected = math.exp(-0.1 * 14)
        assert abs(score - expected) < 0.01

    def test_same_day_events_returns_zero(self, scorer):
        """Events on same day (delta=0) should return 0"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-01', 'eventId': 'evt_b'}

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        assert score == 0.0

    def test_future_date_returns_zero(self, scorer):
        """If evt_b is before evt_a (negative delta), should return 0"""
        evt_a = {'date': '2021-01-15', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-01', 'eventId': 'evt_b'}  # 14 days BEFORE

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        assert score == 0.0

    def test_beyond_max_window_returns_zero(self, scorer):
        """Events beyond max_days window should return 0"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-03-01', 'eventId': 'evt_b'}  # 59 days later

        score = scorer.compute_temporal_correlation(evt_a, evt_b, max_days=30)

        assert score == 0.0

    def test_exactly_at_max_window(self, scorer):
        """Events exactly at max_days should return 0 (> comparison)"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-31', 'eventId': 'evt_b'}  # Exactly 30 days

        score = scorer.compute_temporal_correlation(evt_a, evt_b, max_days=30)

        # 30 days is not > 30, so should calculate TCDI
        # But TCDI at 30 days = e^(-0.1 * 30) = ~0.05 < 0.1 threshold
        assert score == 0.0

    def test_score_below_threshold_returns_zero(self, scorer):
        """TCDI below 0.1 threshold should return 0"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-25', 'eventId': 'evt_b'}  # 24 days

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        # TCDI = e^(-0.1 * 24) = ~0.09 < 0.1
        assert score == 0.0

    def test_very_close_events_high_score(self, scorer):
        """Events 1 day apart should have high score"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-02', 'eventId': 'evt_b'}  # 1 day later

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        # TCDI = e^(-0.1 * 1) = ~0.905
        assert score > 0.9

    def test_custom_k_and_alpha_parameters(self, scorer):
        """Test with custom K and alpha values"""
        evt_a = {'date': '2021-01-01', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-10', 'eventId': 'evt_b'}  # 9 days

        # With k=0.5, alpha=0.2
        score = scorer.compute_temporal_correlation(evt_a, evt_b, k=0.5, alpha=0.2)

        # TCDI = 0.5 * e^(-0.2 * 9) = 0.5 * ~0.165 = ~0.083 < 0.1 threshold
        assert score == 0.0

        # With k=1.0, alpha=0.05 (slower decay)
        score2 = scorer.compute_temporal_correlation(evt_a, evt_b, k=1.0, alpha=0.05)
        # TCDI = 1.0 * e^(-0.05 * 9) = ~0.638
        assert score2 > 0.6


# =============================================================================
# Tests for Entity Overlap
# =============================================================================

class TestEntityOverlap:
    """Tests for compute_entity_overlap method"""

    def test_full_overlap_same_entities(self, scorer):
        """Events with identical entities should have high overlap"""
        evt_a = {
            'eventId': 'evt_a',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }
        evt_b = {
            'eventId': 'evt_b',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        # Jaccard = 2/2 = 1.0, plus actor match bonus = min(1.0, 1.2) = 1.0
        assert score == 1.0

    def test_partial_overlap(self, scorer):
        """Events with some shared entities should have partial score"""
        evt_a = {
            'eventId': 'evt_a',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }
        evt_b = {
            'eventId': 'evt_b',
            'actor': 'ent_company_b',
            'target': 'ent_bank'
        }

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        # Jaccard = 1/3 = ~0.333, no actor match bonus
        assert 0.3 <= score <= 0.4

    def test_no_overlap(self, scorer):
        """Events with no shared entities should return 0"""
        evt_a = {
            'eventId': 'evt_a',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }
        evt_b = {
            'eventId': 'evt_b',
            'actor': 'ent_company_b',
            'target': 'ent_regulator'
        }

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        assert score == 0.0

    def test_empty_entities_first_event(self, scorer):
        """Event A with no entities should return 0"""
        evt_a = {'eventId': 'evt_a', 'actor': None, 'target': None}
        evt_b = {
            'eventId': 'evt_b',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        assert score == 0.0

    def test_empty_entities_second_event(self, scorer):
        """Event B with no entities should return 0"""
        evt_a = {
            'eventId': 'evt_a',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }
        evt_b = {'eventId': 'evt_b', 'actor': None, 'target': None}

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        assert score == 0.0

    def test_both_empty_entities(self, scorer):
        """Both events with no entities should return 0"""
        evt_a = {'eventId': 'evt_a', 'actor': None, 'target': None}
        evt_b = {'eventId': 'evt_b', 'actor': None, 'target': None}

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        assert score == 0.0

    def test_actor_match_bonus(self, scorer):
        """Same actor should give 0.2 bonus"""
        evt_a = {
            'eventId': 'evt_a',
            'actor': 'ent_company_a',
            'target': 'ent_bank'
        }
        evt_b = {
            'eventId': 'evt_b',
            'actor': 'ent_company_a',
            'target': 'ent_regulator'
        }

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        # Jaccard = 1/3 = ~0.333, plus actor bonus 0.2 = ~0.533
        assert score > 0.5

    def test_only_actor_no_target(self, scorer):
        """Events with only actor should still work"""
        evt_a = {'eventId': 'evt_a', 'actor': 'ent_company_a', 'target': None}
        evt_b = {'eventId': 'evt_b', 'actor': 'ent_company_a', 'target': None}

        score = scorer.compute_entity_overlap(evt_a, evt_b)

        # Jaccard = 1/1 = 1.0, plus actor bonus = min(1.2, 1.0) = 1.0
        assert score == 1.0


# =============================================================================
# Tests for Semantic Similarity
# =============================================================================

class TestSemanticSimilarity:
    """Tests for compute_semantic_similarity method"""

    def test_same_event_type_bonus(self, scorer):
        """Events with same type should get type similarity bonus"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'description': 'Rating agency downgraded credit'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'credit_downgrade',
            'description': 'Another credit downgrade occurred'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        # Should have type_sim = 1.0 (0.3 weight)
        assert score > 0.3

    def test_different_event_types(self, scorer):
        """Events with different types should only get keyword similarity"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'description': 'Rating agency downgraded credit'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'stock_crash',
            'description': 'Stock price crashed significantly'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        # type_sim = 0.0, only keyword overlap
        assert score < 0.3

    def test_high_keyword_overlap(self, scorer):
        """Events with many shared keywords should have high score"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'liquidity_warning',
            'description': 'Company faces severe liquidity problems with debt obligations'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'description': 'Company defaults on debt obligations due to liquidity problems'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        # High keyword overlap (liquidity, problems, debt, obligations, company)
        assert score > 0.3

    def test_empty_description_first_event(self, scorer):
        """Event A with empty description should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade', 'description': ''}
        evt_b = {
            'eventId': 'evt_b',
            'type': 'credit_downgrade',
            'description': 'Credit rating was downgraded'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert score == 0.0

    def test_empty_description_both_events(self, scorer):
        """Both events with empty descriptions should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade', 'description': ''}
        evt_b = {'eventId': 'evt_b', 'type': 'credit_downgrade', 'description': ''}

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert score == 0.0

    def test_no_description_field(self, scorer):
        """Events without description field should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}
        evt_b = {'eventId': 'evt_b', 'type': 'credit_downgrade'}

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert score == 0.0

    def test_stopwords_filtered(self, scorer):
        """Stopwords should be filtered from keyword extraction"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'debt_default',
            'description': 'This company will have been said to default'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'description': 'That company would have their default announced'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        # Shared: 'company', 'default' (stopwords filtered)
        # type_sim = 1.0 (0.3 weight)
        assert score > 0.3

    def test_short_words_filtered(self, scorer):
        """Words < 4 chars should be filtered"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'other',
            'description': 'The big bad dog ate a cat'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'other',
            'description': 'A new dog ran by the cat'
        }

        # Only 'dog' >= 4 chars that's not a stopword? Actually 'dog' is 3 chars
        # So very few keywords if any
        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        # Should be 0 since no keywords >= 4 chars
        assert score == 0.0


# =============================================================================
# Tests for Topic Relevance
# =============================================================================

class TestTopicRelevance:
    """Tests for compute_topic_relevance method"""

    def test_same_topic_credit(self, scorer):
        """Events in same topic (credit) should return 1.0"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}
        evt_b = {'eventId': 'evt_b', 'type': 'debt_default'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 1.0

    def test_same_topic_market(self, scorer):
        """Events in same topic (market) should return 1.0"""
        evt_a = {'eventId': 'evt_a', 'type': 'stock_decline'}
        evt_b = {'eventId': 'evt_b', 'type': 'stock_crash'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 1.0

    def test_related_topics_credit_market(self, scorer):
        """Credit and market are related topics, should return 0.7"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}
        evt_b = {'eventId': 'evt_b', 'type': 'stock_decline'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.7

    def test_related_topics_credit_corporate(self, scorer):
        """Credit and corporate are related topics"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}
        evt_b = {'eventId': 'evt_b', 'type': 'restructuring_announcement'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.7

    def test_related_topics_regulatory_credit(self, scorer):
        """Regulatory and credit are related topics"""
        evt_a = {'eventId': 'evt_a', 'type': 'regulatory_pressure'}
        evt_b = {'eventId': 'evt_b', 'type': 'credit_downgrade'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.7

    def test_unrelated_topics(self, scorer):
        """Unrelated topics in financial domain should return 0.3"""
        evt_a = {'eventId': 'evt_a', 'type': 'regulatory_pressure'}
        evt_b = {'eventId': 'evt_b', 'type': 'restructuring_announcement'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.3

    def test_unknown_event_type(self, scorer):
        """Unknown event type should return default 0.3"""
        evt_a = {'eventId': 'evt_a', 'type': 'unknown_type'}
        evt_b = {'eventId': 'evt_b', 'type': 'credit_downgrade'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.3

    def test_both_unknown_types(self, scorer):
        """Both unknown event types should return default 0.3"""
        evt_a = {'eventId': 'evt_a', 'type': 'foo_event'}
        evt_b = {'eventId': 'evt_b', 'type': 'bar_event'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.3

    def test_missing_type_field(self, scorer):
        """Events without type field should return 0.3"""
        evt_a = {'eventId': 'evt_a'}
        evt_b = {'eventId': 'evt_b'}

        score = scorer.compute_topic_relevance(evt_a, evt_b)

        assert score == 0.3


# =============================================================================
# Tests for Event Type Causality
# =============================================================================

class TestEventTypeCausality:
    """Tests for compute_event_type_causality method"""

    def test_direct_causal_link(self, scorer):
        """Direct causal link should return 0.9"""
        evt_a = {'eventId': 'evt_a', 'type': 'regulatory_pressure'}
        evt_b = {'eventId': 'evt_b', 'type': 'liquidity_warning'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.9

    def test_direct_causal_link_credit_to_default(self, scorer):
        """credit_downgrade -> debt_default is direct causal"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}
        evt_b = {'eventId': 'evt_b', 'type': 'debt_default'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.9

    def test_indirect_causal_link(self, scorer):
        """Indirect (2-hop) causal link should return 0.6"""
        # regulatory_pressure -> liquidity_warning -> missed_payment
        evt_a = {'eventId': 'evt_a', 'type': 'regulatory_pressure'}
        evt_b = {'eventId': 'evt_b', 'type': 'missed_payment'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.6

    def test_no_causal_link(self, scorer):
        """No causal pattern should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'restructuring_announcement'}
        evt_b = {'eventId': 'evt_b', 'type': 'regulatory_pressure'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.0

    def test_reverse_causal_link(self, scorer):
        """Reverse causal direction should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}
        evt_b = {'eventId': 'evt_b', 'type': 'regulatory_pressure'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.0

    def test_unknown_event_types(self, scorer):
        """Unknown event types should return 0"""
        evt_a = {'eventId': 'evt_a', 'type': 'unknown_type'}
        evt_b = {'eventId': 'evt_b', 'type': 'another_unknown'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.0

    def test_missing_type_field(self, scorer):
        """Events without type field should return 0"""
        evt_a = {'eventId': 'evt_a'}
        evt_b = {'eventId': 'evt_b'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.0

    def test_same_event_type_no_self_causality(self, scorer):
        """Same event type without causal path should return 0"""
        # restructuring_announcement is not a key in causal_patterns
        evt_a = {'eventId': 'evt_a', 'type': 'restructuring_announcement'}
        evt_b = {'eventId': 'evt_b', 'type': 'restructuring_announcement'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        assert score == 0.0

    def test_same_event_type_with_indirect_path(self, scorer):
        """Same event type with 2-hop causal path should return 0.6"""
        # credit_downgrade -> debt_default -> credit_downgrade (2-hop)
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}
        evt_b = {'eventId': 'evt_b', 'type': 'credit_downgrade'}

        score = scorer.compute_event_type_causality(evt_a, evt_b)

        # Has indirect path via debt_default
        assert score == 0.6


# =============================================================================
# Tests for Emotional Consistency (EVI)
# =============================================================================

class TestEmotionalConsistency:
    """Tests for compute_emotional_consistency method"""

    def test_same_sentiment_high_consistency(self, scorer):
        """Events with same sentiment should have high consistency"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}  # -0.9
        evt_b = {'eventId': 'evt_b', 'type': 'stock_crash'}  # -0.9

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # EVI = |(-0.9) - (-0.9)| = 0, consistency = 1.0 - 0 = 1.0
        assert score == 1.0

    def test_similar_sentiment(self, scorer):
        """Events with similar sentiment should have moderate consistency"""
        evt_a = {'eventId': 'evt_a', 'type': 'credit_downgrade'}  # -0.8
        evt_b = {'eventId': 'evt_b', 'type': 'stock_decline'}  # -0.7

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # EVI = |(-0.8) - (-0.7)| = 0.1, consistency = 1.0 - 0.1 = 0.9
        assert abs(score - 0.9) < 0.01

    def test_different_sentiment(self, scorer):
        """Events with different sentiment should have low consistency"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}  # -0.9
        evt_b = {'eventId': 'evt_b', 'type': 'restructuring_announcement'}  # 0.2

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # EVI = |(-0.9) - 0.2| = 1.1, consistency = max(0, 1.0 - 1.1) = 0.0
        assert score == 0.0

    def test_unknown_event_types_default_sentiment(self, scorer):
        """Unknown event types should use default sentiment (-0.5)"""
        evt_a = {'eventId': 'evt_a', 'type': 'unknown_type'}
        evt_b = {'eventId': 'evt_b', 'type': 'another_unknown'}

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # Both default to -0.5, EVI = 0, consistency = 1.0
        assert score == 1.0

    def test_mixed_known_unknown_types(self, scorer):
        """Mix of known and unknown types should work"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}  # -0.9
        evt_b = {'eventId': 'evt_b', 'type': 'unknown_type'}  # -0.5 default

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # EVI = |(-0.9) - (-0.5)| = 0.4, consistency = 1.0 - 0.4 = 0.6
        assert abs(score - 0.6) < 0.01

    def test_missing_type_field(self, scorer):
        """Events without type field should use default sentiment"""
        evt_a = {'eventId': 'evt_a'}
        evt_b = {'eventId': 'evt_b'}

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # Both default to -0.5, consistency = 1.0
        assert score == 1.0

    def test_regulatory_intervention_mixed_sentiment(self, scorer):
        """Regulatory intervention has mixed sentiment (-0.3)"""
        evt_a = {'eventId': 'evt_a', 'type': 'debt_default'}  # -0.9
        evt_b = {'eventId': 'evt_b', 'type': 'regulatory_intervention'}  # -0.3

        score = scorer.compute_emotional_consistency(evt_a, evt_b)

        # EVI = |(-0.9) - (-0.3)| = 0.6, consistency = 1.0 - 0.6 = 0.4
        assert abs(score - 0.4) < 0.01


# =============================================================================
# Tests for compute_evolution_score (combined scoring)
# =============================================================================

class TestComputeEvolutionScore:
    """Tests for compute_evolution_score method"""

    def test_basic_combined_score(self, scorer, sample_events):
        """Test combined score with sample events"""
        evt_a = sample_events[0]  # regulatory_pressure, 2021-01-01
        evt_b = sample_events[1]  # liquidity_warning, 2021-01-15

        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        assert isinstance(score, float)
        assert isinstance(components, dict)
        assert all(k in components for k in [
            'temporal', 'entity_overlap', 'semantic',
            'topic', 'causality', 'emotional'
        ])

    def test_score_below_threshold_returns_zero(self, scorer):
        """Score below 0.2 threshold should return 0"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'unknown_type',
            'date': '2021-01-01',
            'actor': 'ent_x',
            'target': None,
            'description': 'foo'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'another_unknown',
            'date': '2021-03-01',  # Far apart (60 days)
            'actor': 'ent_y',
            'target': None,
            'description': 'bar'
        }

        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        # All components should be low
        assert score == 0.0

    def test_high_score_related_events(self, scorer, sample_events):
        """Closely related events should have high score"""
        evt_a = sample_events[2]  # credit_downgrade, 2021-01-20, target=ent_company_a
        evt_b = sample_events[3]  # debt_default, 2021-02-01, actor=ent_company_a

        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        # Should have: temporal (12 days), entity overlap (company_a),
        # topic (credit), causality (credit_downgrade -> debt_default)
        assert score > 0.3
        assert components['causality'] == 0.9  # Direct causal link

    def test_custom_weights(self, scorer, sample_events):
        """Test with custom weights"""
        evt_a = sample_events[0]
        evt_b = sample_events[1]

        custom_weights = {
            'temporal': 0.5,
            'entity_overlap': 0.1,
            'semantic': 0.1,
            'topic': 0.1,
            'causality': 0.1,
            'emotional': 0.1,
        }

        score, components = scorer.compute_evolution_score(
            evt_a, evt_b, weights=custom_weights
        )

        # Verify weighted sum (if above threshold)
        expected = sum(custom_weights[k] * components[k] for k in custom_weights)
        if expected >= 0.2:
            assert abs(score - expected) < 0.01
        else:
            assert score == 0.0

    def test_all_components_returned(self, scorer, sample_events):
        """All 6 components should be returned"""
        evt_a = sample_events[0]
        evt_b = sample_events[1]

        _, components = scorer.compute_evolution_score(evt_a, evt_b)

        assert len(components) == 6
        for key in ['temporal', 'entity_overlap', 'semantic',
                    'topic', 'causality', 'emotional']:
            assert key in components
            assert isinstance(components[key], float)
            assert 0.0 <= components[key] <= 1.0


# =============================================================================
# Tests for compute_all_evolution_links function
# =============================================================================

class TestComputeAllEvolutionLinks:
    """Tests for compute_all_evolution_links function"""

    def test_basic_functionality(self, sample_events, sample_entities):
        """Test basic link computation"""
        links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.2, use_parallel=False
        )

        assert isinstance(links, list)
        # Should have some links given related events
        assert len(links) > 0

    def test_link_structure(self, sample_events, sample_entities):
        """Test that links have correct structure"""
        links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.0,  # Get all links
            use_parallel=False
        )

        if links:
            link = links[0]
            assert 'from' in link
            assert 'to' in link
            assert 'score' in link
            assert 'components' in link
            assert 'from_date' in link
            assert 'to_date' in link
            assert 'from_type' in link
            assert 'to_type' in link

    def test_empty_events_list(self, sample_entities):
        """Empty events list should return empty links"""
        links = compute_all_evolution_links(
            [], sample_entities, use_parallel=False
        )

        assert links == []

    def test_single_event(self, sample_entities):
        """Single event should return empty links (no pairs)"""
        single_event = [{
            'eventId': 'evt_001',
            'type': 'credit_downgrade',
            'date': '2021-01-01',
            'actor': 'ent_a',
            'target': 'ent_b',
            'description': 'Test event'
        }]

        links = compute_all_evolution_links(
            single_event, sample_entities, use_parallel=False
        )

        assert links == []

    def test_high_threshold_filters_links(self, sample_events, sample_entities):
        """High threshold should filter out weak links"""
        low_threshold_links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.1,
            use_parallel=False
        )

        high_threshold_links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.5,
            use_parallel=False
        )

        assert len(high_threshold_links) <= len(low_threshold_links)

    def test_links_are_forward_only(self, sample_events, sample_entities):
        """Links should only go forward in time (from_date <= to_date)"""
        links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.0,
            use_parallel=False
        )

        for link in links:
            assert link['from_date'] <= link['to_date']

    def test_no_self_links(self, sample_events, sample_entities):
        """Events should not link to themselves"""
        links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.0,
            use_parallel=False
        )

        for link in links:
            assert link['from'] != link['to']

    def test_scores_within_bounds(self, sample_events, sample_entities):
        """All scores should be between 0 and 1"""
        links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.0,
            use_parallel=False
        )

        for link in links:
            assert 0.0 <= link['score'] <= 1.0
            for component, value in link['components'].items():
                assert 0.0 <= value <= 1.0

    def test_parallel_vs_serial_consistency(self, sample_events, sample_entities):
        """Parallel and serial processing should give same results"""
        serial_links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.2,
            use_parallel=False
        )

        parallel_links = compute_all_evolution_links(
            sample_events, sample_entities,
            threshold=0.2,
            use_parallel=True,
            max_workers=2
        )

        # Sort for comparison
        serial_sorted = sorted(serial_links, key=lambda x: (x['from'], x['to']))
        parallel_sorted = sorted(parallel_links, key=lambda x: (x['from'], x['to']))

        assert len(serial_sorted) == len(parallel_sorted)

        for s, p in zip(serial_sorted, parallel_sorted):
            assert s['from'] == p['from']
            assert s['to'] == p['to']
            assert abs(s['score'] - p['score']) < 0.001


# =============================================================================
# Tests for EventEvolutionScorer initialization
# =============================================================================

class TestEventEvolutionScorerInit:
    """Tests for EventEvolutionScorer class initialization"""

    def test_basic_initialization(self, sample_events, sample_entities):
        """Test basic scorer initialization"""
        scorer = EventEvolutionScorer(sample_events, sample_entities)

        assert scorer.events == sample_events
        assert scorer.entities == sample_entities
        assert len(scorer.entity_map) == len(sample_entities)

    def test_entity_map_creation(self, sample_events, sample_entities):
        """Test entity map is correctly created"""
        scorer = EventEvolutionScorer(sample_events, sample_entities)

        for entity in sample_entities:
            assert entity['entityId'] in scorer.entity_map
            assert scorer.entity_map[entity['entityId']] == entity

    def test_empty_events(self, sample_entities):
        """Test with empty events list"""
        scorer = EventEvolutionScorer([], sample_entities)

        assert scorer.events == []
        assert len(scorer.entity_map) == len(sample_entities)

    def test_empty_entities(self, sample_events):
        """Test with empty entities list"""
        scorer = EventEvolutionScorer(sample_events, [])

        assert scorer.entities == []
        assert len(scorer.entity_map) == 0

    def test_causal_patterns_initialized(self, sample_events, sample_entities):
        """Test causal patterns are properly initialized"""
        scorer = EventEvolutionScorer(sample_events, sample_entities)

        assert 'regulatory_pressure' in scorer.causal_patterns
        assert 'credit_downgrade' in scorer.causal_patterns
        assert 'liquidity_warning' in scorer.causal_patterns['regulatory_pressure']


# =============================================================================
# Edge case tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_none_values_except_description(self, scorer):
        """Events with None values (except description) should be handled"""
        evt_a = {
            'eventId': 'evt_a',
            'type': None,
            'date': '2021-01-01',
            'actor': None,
            'target': None,
            'description': ''  # Empty string, not None
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': None,
            'date': '2021-01-15',
            'actor': None,
            'target': None,
            'description': ''  # Empty string, not None
        }

        # Should not raise exceptions
        score, components = scorer.compute_evolution_score(evt_a, evt_b)

        assert isinstance(score, float)
        assert isinstance(components, dict)

    def test_none_description_raises_error(self, scorer):
        """None description raises AttributeError (documents current behavior)"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'date': '2021-01-01',
            'description': None
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'date': '2021-01-15',
            'description': 'Some description'
        }

        # Current implementation does not handle None description
        with pytest.raises(AttributeError):
            scorer.compute_semantic_similarity(evt_a, evt_b)

    def test_special_characters_in_description(self, scorer):
        """Descriptions with special characters should be handled"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'date': '2021-01-01',
            'description': 'Company $ABC @downgraded! #crisis 100%'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'date': '2021-01-15',
            'description': 'Default rate: 25.5% for company!'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert isinstance(score, float)

    def test_unicode_in_description(self, scorer):
        """Descriptions with unicode should be handled"""
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'date': '2021-01-01',
            'description': 'Company downgrade announced'
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'date': '2021-01-15',
            'description': 'Default occurred'
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert isinstance(score, float)

    def test_very_long_description(self, scorer):
        """Very long descriptions should be handled"""
        long_text = ' '.join(['financial crisis problems'] * 1000)
        evt_a = {
            'eventId': 'evt_a',
            'type': 'credit_downgrade',
            'date': '2021-01-01',
            'description': long_text
        }
        evt_b = {
            'eventId': 'evt_b',
            'type': 'debt_default',
            'date': '2021-01-15',
            'description': long_text
        }

        score = scorer.compute_semantic_similarity(evt_a, evt_b)

        assert isinstance(score, float)
        assert score > 0.5  # Same text = high overlap

    def test_date_at_year_boundary(self, scorer):
        """Dates crossing year boundary should work"""
        evt_a = {'date': '2020-12-25', 'eventId': 'evt_a'}
        evt_b = {'date': '2021-01-05', 'eventId': 'evt_b'}  # 11 days

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        # Should correctly calculate 11 days
        expected = math.exp(-0.1 * 11)
        assert abs(score - expected) < 0.01

    def test_leap_year_dates(self, scorer):
        """Leap year dates should be handled correctly"""
        evt_a = {'date': '2020-02-28', 'eventId': 'evt_a'}
        evt_b = {'date': '2020-03-01', 'eventId': 'evt_b'}  # 2 days in leap year

        score = scorer.compute_temporal_correlation(evt_a, evt_b)

        # 2020 is leap year, Feb 28 to Mar 1 = 2 days
        expected = math.exp(-0.1 * 2)
        assert abs(score - expected) < 0.01
