"""
Enhanced NLP methods for FE-EKG evolution scoring

Requires: pip install sentence-transformers transformers spacy
          python -m spacy download en_core_web_sm
"""

from typing import Dict, Tuple
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import spacy


class EnhancedNLPScorer:
    """Advanced NLP-based evolution scoring"""

    def __init__(self):
        # Load models (cache on first run)
        print("Loading NLP models (one-time setup)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.sentiment_model = pipeline("sentiment-analysis",
                                       model="ProsusAI/finbert")
        self.nlp = spacy.load("en_core_web_sm")
        print("✓ Models loaded")

    def compute_semantic_similarity(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Enhanced semantic similarity using sentence embeddings

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Similarity score (0.0-1.0)
        """
        desc_a = evt_a.get('description', '')
        desc_b = evt_b.get('description', '')

        if not desc_a or not desc_b:
            return 0.0

        # Generate embeddings
        emb_a = self.embedding_model.encode(desc_a)
        emb_b = self.embedding_model.encode(desc_b)

        # Cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity([emb_a], [emb_b])[0][0]

        # Normalize to 0-1 range (cosine is -1 to 1)
        normalized = (similarity + 1) / 2

        return float(normalized)

    def compute_sentiment(self, text: str) -> float:
        """
        Financial sentiment analysis using FinBERT

        Args:
            text: Event description

        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if not text:
            return 0.0

        # FinBERT prediction
        result = self.sentiment_model(text[:512])[0]  # Max 512 tokens

        # Convert to numeric score
        if result['label'] == 'positive':
            return result['score']
        elif result['label'] == 'negative':
            return -result['score']
        else:  # neutral
            return 0.0

    def compute_emotional_consistency(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Enhanced EVI using FinBERT sentiment

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Consistency score (0.0-1.0), higher = more consistent
        """
        sent_a = self.compute_sentiment(evt_a.get('description', ''))
        sent_b = self.compute_sentiment(evt_b.get('description', ''))

        # EVI = emotional difference
        evi = abs(sent_a - sent_b)

        # Convert to consistency (inverse)
        consistency = max(0.0, 1.0 - evi)

        return consistency

    def extract_entities(self, text: str) -> Dict:
        """
        Extract named entities using SpaCy

        Args:
            text: Event description

        Returns:
            Dict of entity types and values
        """
        doc = self.nlp(text)

        entities = {
            'organizations': [],
            'persons': [],
            'money': [],
            'dates': [],
            'locations': []
        }

        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(ent.text)

        return entities

    def compute_entity_overlap_enhanced(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Entity overlap using NER extraction

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Overlap score (0.0-1.0)
        """
        # Extract entities from descriptions
        ents_a = self.extract_entities(evt_a.get('description', ''))
        ents_b = self.extract_entities(evt_b.get('description', ''))

        # Combine all entities
        all_ents_a = set()
        all_ents_b = set()

        for ent_type in ents_a:
            all_ents_a.update(ents_a[ent_type])
            all_ents_b.update(ents_b[ent_type])

        if not all_ents_a or not all_ents_b:
            # Fallback to explicit actor/target
            if evt_a.get('actor') == evt_b.get('actor'):
                return 0.5
            return 0.0

        # Jaccard similarity
        intersection = all_ents_a & all_ents_b
        union = all_ents_a | all_ents_b

        overlap = len(intersection) / len(union) if union else 0.0

        return overlap


# Example usage
if __name__ == "__main__":
    import json

    # Load Evergrande data
    with open('../data/evergrande_crisis.json', 'r') as f:
        data = json.load(f)

    events = data['events'][:3]  # First 3 events

    # Initialize enhanced scorer
    scorer = EnhancedNLPScorer()

    print("\n" + "="*70)
    print("ENHANCED NLP SCORING COMPARISON")
    print("="*70)

    for i in range(len(events) - 1):
        evt_a = events[i]
        evt_b = events[i + 1]

        print(f"\n{evt_a['eventId']} → {evt_b['eventId']}")
        print(f"Event A: {evt_a['description'][:60]}...")
        print(f"Event B: {evt_b['description'][:60]}...")

        # Semantic similarity
        sem_score = scorer.compute_semantic_similarity(evt_a, evt_b)
        print(f"\n  Semantic Similarity: {sem_score:.3f}")

        # Sentiment
        sent_a = scorer.compute_sentiment(evt_a['description'])
        sent_b = scorer.compute_sentiment(evt_b['description'])
        print(f"  Sentiment A: {sent_a:.3f}, B: {sent_b:.3f}")

        # Emotional consistency
        emo_score = scorer.compute_emotional_consistency(evt_a, evt_b)
        print(f"  Emotional Consistency: {emo_score:.3f}")

        # Entity extraction
        ents_a = scorer.extract_entities(evt_a['description'])
        ents_b = scorer.extract_entities(evt_b['description'])
        print(f"  Entities A: {ents_a}")
        print(f"  Entities B: {ents_b}")

        # Entity overlap
        ent_overlap = scorer.compute_entity_overlap_enhanced(evt_a, evt_b)
        print(f"  Entity Overlap: {ent_overlap:.3f}")

    print("\n" + "="*70)
