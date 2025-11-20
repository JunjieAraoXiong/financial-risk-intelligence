"""
Nemotron-powered evolution scoring for FE-EKG

Uses NVIDIA Nemotron LLM for:
1. Event classification
2. Causal relationship detection
3. Sentiment analysis
4. Risk assessment
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root (override shell env)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)


class NemotronScorer:
    """Evolution scoring using NVIDIA LLM API"""

    # Available models with their strengths
    MODELS = {
        'fast': 'nvidia/nvidia-nemotron-nano-9b-v2',      # Fastest, cheapest
        'smart': 'deepseek-ai/deepseek-v3.1',             # Best reasoning
        'multilingual': 'qwen/qwen3-next-80b-a3b-instruct',  # 119 languages
        'structured': 'qwen/qwen3-coder-480b-a35b-instruct', # Best for JSON/code
    }

    def __init__(self, model_preset='fast'):
        """
        Initialize NVIDIA API client

        Args:
            model_preset: 'fast', 'smart', 'multilingual', or 'structured'
                         Or provide full model name
        """
        api_key = os.getenv('NVIDIA_API_KEY')
        base_url = os.getenv('NVIDIA_NIM_URL', 'https://integrate.api.nvidia.com/v1')

        if not api_key or api_key == 'your_api_key_here':
            raise ValueError(
                "NVIDIA_API_KEY not set. Get your key from https://build.nvidia.com/"
            )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        # Set model based on preset or custom name
        if model_preset in self.MODELS:
            self.model = self.MODELS[model_preset]
            print(f"Using {model_preset} model: {self.model}")
        else:
            self.model = model_preset  # Assume it's a full model name
            print(f"Using custom model: {self.model}")

    def classify_event_type(self, description: str) -> Dict:
        """
        Classify financial event type using Nemotron

        Args:
            description: Event description text

        Returns:
            Dict with type, confidence, and reasoning
        """
        prompt = f"""You are a financial risk analyst. Classify this event into ONE of these types:

Event Types:
- regulatory_pressure: Government/regulatory actions
- liquidity_warning: Cash flow problems
- credit_downgrade: Rating agency downgrades
- debt_default: Missed payments, defaults
- missed_payment: Payment delays
- stock_decline: Stock price drops (5-20%)
- stock_crash: Severe stock drops (>20%)
- trading_halt: Trading suspension
- contagion: Risk spreading to other entities
- regulatory_intervention: Government rescue/support
- restructuring_announcement: Debt restructuring plans
- asset_seizure: Asset confiscation

Event Description:
{description}

Return ONLY a JSON object with this format:
{{"type": "event_type", "confidence": 0.95, "reasoning": "brief explanation"}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Extract JSON from markdown if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result
        except:
            # Fallback if parsing fails
            return {
                "type": "unknown",
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }

    def compute_causal_score(self, evt_a: Dict, evt_b: Dict) -> Tuple[float, str]:
        """
        Determine if event A caused event B using Nemotron

        Args:
            evt_a: Earlier event
            evt_b: Later event

        Returns:
            Tuple of (causality_score, explanation)
        """
        prompt = f"""You are a financial risk analyst. Determine if Event A likely CAUSED Event B.

Event A ({evt_a['date']}):
Type: {evt_a['type']}
Description: {evt_a['description']}

Event B ({evt_b['date']}):
Type: {evt_b['type']}
Description: {evt_b['description']}

Time gap: {(self._parse_date(evt_b['date']) - self._parse_date(evt_a['date'])).days} days

Assess the causal relationship on a scale of 0.0 to 1.0:
- 1.0: Event A directly caused Event B
- 0.7-0.9: Event A likely contributed to Event B
- 0.4-0.6: Possible indirect relationship
- 0.1-0.3: Weak or coincidental relationship
- 0.0: No causal relationship

Return ONLY a JSON object:
{{"causality_score": 0.85, "explanation": "Brief reasoning (max 50 words)"}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()

        try:
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            return result['causality_score'], result['explanation']
        except:
            return 0.0, "Failed to parse response"

    def compute_semantic_similarity(self, evt_a: Dict, evt_b: Dict) -> float:
        """
        Compute semantic similarity using Nemotron's understanding

        Args:
            evt_a: First event
            evt_b: Second event

        Returns:
            Similarity score (0.0-1.0)
        """
        prompt = f"""Rate the semantic similarity between these two financial events on a scale of 0.0 to 1.0:

Event 1: {evt_a['description']}
Event 2: {evt_b['description']}

Similarity Scale:
- 1.0: Nearly identical meaning
- 0.7-0.9: Highly related (same topic/impact)
- 0.4-0.6: Moderately related (same domain)
- 0.1-0.3: Weakly related
- 0.0: Completely unrelated

Return ONLY a number between 0.0 and 1.0 (e.g., 0.75)"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )

        result_text = response.choices[0].message.content.strip()

        try:
            score = float(result_text)
            return max(0.0, min(1.0, score))  # Clamp to 0-1
        except:
            return 0.0

    def assess_risk_level(self, event: Dict) -> Dict:
        """
        Assess risk level of an event using Nemotron

        Args:
            event: Event dict

        Returns:
            Dict with risk assessment
        """
        prompt = f"""Assess the financial risk level of this event:

Event Type: {event['type']}
Date: {event['date']}
Description: {event['description']}

Provide a risk assessment as JSON:
{{
  "severity": "low|medium|high|critical",
  "probability_of_contagion": 0.0-1.0,
  "systemic_risk": 0.0-1.0,
  "key_risks": ["risk1", "risk2", "risk3"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            return json.loads(result_text)
        except:
            return {
                "severity": "unknown",
                "probability_of_contagion": 0.0,
                "systemic_risk": 0.0,
                "key_risks": []
            }

    def _parse_date(self, date_str: str):
        """Helper to parse date strings"""
        from datetime import datetime
        return datetime.strptime(date_str, '%Y-%m-%d')


# Example usage
if __name__ == "__main__":
    import sys

    print("="*70)
    print("NEMOTRON-POWERED EVOLUTION SCORING")
    print("="*70 + "\n")

    # Load Evergrande data
    try:
        with open('../data/evergrande_crisis.json', 'r') as f:
            data = json.load(f)
    except:
        with open('data/evergrande_crisis.json', 'r') as f:
            data = json.load(f)

    events = data['events'][:3]  # First 3 events

    # Initialize with different model presets
    print("Available presets: 'fast', 'smart', 'multilingual', 'structured'\n")

    try:
        # Use 'smart' for best reasoning (you can change to 'fast' for speed)
        scorer = NemotronScorer(model_preset='smart')
        print("✅ Connected successfully!\n")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Demo 1: Event classification
    print("Demo 1: Event Type Classification")
    print("-" * 70)
    evt = events[1]
    print(f"Description: {evt['description']}")
    print(f"Actual type: {evt['type']}")

    result = scorer.classify_event_type(evt['description'])
    print(f"Nemotron classification: {result['type']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}\n")

    # Demo 2: Causal analysis
    print("Demo 2: Causal Relationship Detection")
    print("-" * 70)
    evt_a = events[0]
    evt_b = events[1]

    print(f"Event A: {evt_a['description'][:60]}...")
    print(f"Event B: {evt_b['description'][:60]}...")

    score, explanation = scorer.compute_causal_score(evt_a, evt_b)
    print(f"\nCausality Score: {score:.2f}")
    print(f"Explanation: {explanation}\n")

    # Demo 3: Semantic similarity
    print("Demo 3: Semantic Similarity")
    print("-" * 70)
    similarity = scorer.compute_semantic_similarity(evt_a, evt_b)
    print(f"Similarity: {similarity:.2f}\n")

    # Demo 4: Risk assessment
    print("Demo 4: Risk Assessment")
    print("-" * 70)
    risk = scorer.assess_risk_level(events[2])
    print(f"Event: {events[2]['description'][:60]}...")
    print(f"Severity: {risk['severity']}")
    print(f"Contagion Probability: {risk['probability_of_contagion']:.2f}")
    print(f"Systemic Risk: {risk['systemic_risk']:.2f}")
    print(f"Key Risks: {', '.join(risk['key_risks'])}")

    print("\n" + "="*70)
    print("✅ All demos completed!")
    print("="*70)
