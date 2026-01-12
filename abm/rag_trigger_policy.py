"""
RAG Trigger Policy for BankAgent decisions.

This module implements a multi-factor policy for determining when a bank agent
should query the RAG system for historical financial intelligence. The policy
considers multiple market and agent-specific conditions to make intelligent
decisions about when RAG queries would be most valuable.

Key trigger conditions:
- Market volatility spikes
- Liquidity stress
- Peer bank failures
- Credit rating changes
- Significant market events
- Cooldown periods to prevent excessive queries
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time

logger = logging.getLogger(__name__)


class TriggerReason(Enum):
    """Enumeration of reasons why RAG was triggered."""
    VOLATILITY_SPIKE = "volatility_spike"
    VOLATILITY_THRESHOLD = "volatility_threshold"
    LIQUIDITY_STRESS = "liquidity_stress"
    PEER_FAILURE = "peer_failure"
    PEER_STRESS = "peer_stress"
    CREDIT_DOWNGRADE = "credit_downgrade"
    MARKET_EVENT = "market_event"
    CAPITAL_STRESS = "capital_stress"
    PERIODIC_CHECK = "periodic_check"
    INITIAL_CRISIS = "initial_crisis"


@dataclass
class TriggerResult:
    """Result of a trigger policy evaluation."""
    should_trigger: bool
    reasons: List[TriggerReason] = field(default_factory=list)
    priority: int = 0  # Higher priority = more urgent query
    context_hints: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self):
        return self.should_trigger


@dataclass
class PolicyConfig:
    """Configuration for the RAG trigger policy."""

    # Volatility thresholds
    volatility_threshold: float = 0.15  # Base threshold for RAG query
    volatility_spike_delta: float = 0.10  # Trigger if volatility increases by this much
    volatility_crisis_threshold: float = 0.50  # Crisis level volatility

    # Liquidity thresholds
    liquidity_stress_threshold: float = 0.50  # Liquidity factor below this triggers RAG
    liquidity_severe_threshold: float = 0.30  # Severe liquidity stress
    agent_liquidity_threshold: float = 0.15  # Agent's own liquidity ratio threshold

    # Capital thresholds
    capital_loss_threshold: float = 0.20  # Capital loss percentage to trigger
    capital_critical_threshold: float = 20.0  # Critical capital level (billions)

    # Peer monitoring
    peer_failure_trigger: bool = True  # Trigger on any peer failure
    peer_stress_count_threshold: int = 2  # Number of stressed peers to trigger
    peer_stress_liquidity: float = 0.10  # Peer liquidity below this = stressed

    # Credit rating
    credit_downgrade_trigger: bool = True  # Trigger on credit rating changes

    # Cooldown settings
    cooldown_steps: int = 2  # Minimum steps between RAG queries
    crisis_cooldown_steps: int = 1  # Shorter cooldown during crisis
    max_queries_per_period: int = 5  # Max queries per period
    period_length_steps: int = 10  # Period length for query limiting

    # Periodic check
    periodic_check_interval: int = 8  # Query periodically even in stable conditions

    # Event-based triggers
    market_event_keywords: List[str] = field(default_factory=lambda: [
        "bankruptcy", "failure", "collapse", "crisis", "default",
        "bailout", "intervention", "emergency", "shock"
    ])


class RagTriggerPolicy:
    """
    Multi-factor policy for determining when to query RAG.

    This policy considers multiple signals including:
    - Market volatility levels and spikes
    - Liquidity conditions (market-wide and agent-specific)
    - Peer bank failures and stress
    - Credit rating changes
    - Capital levels
    - Cooldown periods to prevent excessive queries

    Usage:
        policy = RagTriggerPolicy()
        result = policy.should_query_rag(market_state, agent_state, history)
        if result:
            # Perform RAG query
            print(f"Triggered due to: {result.reasons}")
    """

    def __init__(self, config: Optional[PolicyConfig] = None):
        """
        Initialize the RAG trigger policy.

        Args:
            config: Optional PolicyConfig with custom thresholds.
                   Uses defaults if not provided.
        """
        self.config = config or PolicyConfig()
        self._query_history: Dict[str, List[int]] = {}  # agent_name -> list of steps
        self._last_volatility: Dict[str, float] = {}  # Track volatility for spike detection
        self._crisis_started: Dict[str, bool] = {}  # Track if crisis just started
        self._peer_failures_seen: Dict[str, set] = {}  # Track known peer failures

    def should_query_rag(
        self,
        market_state: Dict[str, Any],
        agent_state: Dict[str, Any],
        history: Optional[Dict[str, Any]] = None
    ) -> TriggerResult:
        """
        Determine if RAG should be queried based on multiple factors.

        Args:
            market_state: Current market conditions including:
                - volatility: float (0-1)
                - liquidity: float (liquidity factor, 0-1)
                - week: int (current simulation step)
                - news: str (current news context)
                - failed_banks: List[str] (names of failed banks)
                - stressed_banks: List[Dict] (banks under stress)

            agent_state: Agent's current state including:
                - name: str
                - capital: float
                - liquidity: float (ratio)
                - risk_score: float
                - credit_rating: Optional[str]
                - initial_capital: float (for loss calculation)

            history: Optional historical data including:
                - previous_credit_rating: Optional[str]
                - events: List[str] (recent market events)

        Returns:
            TriggerResult with decision, reasons, priority, and context hints.
        """
        agent_name = agent_state.get("name", "unknown")
        current_step = market_state.get("week", 0)

        # Initialize tracking for new agents
        if agent_name not in self._query_history:
            self._query_history[agent_name] = []
            self._last_volatility[agent_name] = 0.10  # Default normal volatility
            self._crisis_started[agent_name] = False
            self._peer_failures_seen[agent_name] = set()

        # Check cooldown first
        if not self._check_cooldown(agent_name, current_step, market_state):
            logger.debug(f"{agent_name}: RAG query blocked by cooldown")
            return TriggerResult(should_trigger=False)

        # Collect all trigger reasons
        reasons: List[TriggerReason] = []
        priority = 0
        context_hints: Dict[str, Any] = {}

        # Check each trigger condition
        volatility_result = self._check_volatility(market_state, agent_name)
        if volatility_result:
            reasons.extend(volatility_result["reasons"])
            priority = max(priority, volatility_result["priority"])
            context_hints.update(volatility_result.get("hints", {}))

        liquidity_result = self._check_liquidity(market_state, agent_state)
        if liquidity_result:
            reasons.extend(liquidity_result["reasons"])
            priority = max(priority, liquidity_result["priority"])
            context_hints.update(liquidity_result.get("hints", {}))

        capital_result = self._check_capital(agent_state)
        if capital_result:
            reasons.extend(capital_result["reasons"])
            priority = max(priority, capital_result["priority"])
            context_hints.update(capital_result.get("hints", {}))

        peer_result = self._check_peer_conditions(market_state, agent_state)
        if peer_result:
            reasons.extend(peer_result["reasons"])
            priority = max(priority, peer_result["priority"])
            context_hints.update(peer_result.get("hints", {}))

        credit_result = self._check_credit_rating(agent_state, history)
        if credit_result:
            reasons.extend(credit_result["reasons"])
            priority = max(priority, credit_result["priority"])
            context_hints.update(credit_result.get("hints", {}))

        event_result = self._check_market_events(market_state, history)
        if event_result:
            reasons.extend(event_result["reasons"])
            priority = max(priority, event_result["priority"])
            context_hints.update(event_result.get("hints", {}))

        periodic_result = self._check_periodic(agent_name, current_step)
        if periodic_result and not reasons:  # Only if no other triggers
            reasons.extend(periodic_result["reasons"])
            priority = max(priority, periodic_result["priority"])

        # Record query if triggered
        should_trigger = len(reasons) > 0
        if should_trigger:
            self._record_query(agent_name, current_step)
            logger.info(
                f"{agent_name}: RAG triggered at step {current_step} "
                f"(reasons: {[r.value for r in reasons]}, priority: {priority})"
            )

        return TriggerResult(
            should_trigger=should_trigger,
            reasons=reasons,
            priority=priority,
            context_hints=context_hints
        )

    def _check_cooldown(
        self,
        agent_name: str,
        current_step: int,
        market_state: Dict[str, Any]
    ) -> bool:
        """Check if cooldown period has passed since last query."""
        query_history = self._query_history.get(agent_name, [])

        if not query_history:
            return True  # No previous queries

        last_query_step = query_history[-1]
        volatility = market_state.get("volatility", 0.10)

        # Use shorter cooldown during crisis
        if volatility >= self.config.volatility_crisis_threshold:
            cooldown = self.config.crisis_cooldown_steps
        else:
            cooldown = self.config.cooldown_steps

        if current_step - last_query_step < cooldown:
            return False

        # Check max queries per period
        period_start = max(0, current_step - self.config.period_length_steps)
        queries_in_period = sum(1 for step in query_history if step >= period_start)

        if queries_in_period >= self.config.max_queries_per_period:
            logger.debug(
                f"{agent_name}: Max queries ({self.config.max_queries_per_period}) "
                f"reached in period"
            )
            return False

        return True

    def _check_volatility(
        self,
        market_state: Dict[str, Any],
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Check volatility-based triggers."""
        volatility = market_state.get("volatility", 0.10)
        last_volatility = self._last_volatility.get(agent_name, 0.10)

        # Update tracked volatility
        self._last_volatility[agent_name] = volatility

        result = {"reasons": [], "priority": 0, "hints": {}}

        # Check for volatility spike (sudden increase)
        volatility_change = volatility - last_volatility
        if volatility_change >= self.config.volatility_spike_delta:
            result["reasons"].append(TriggerReason.VOLATILITY_SPIKE)
            result["priority"] = max(result["priority"], 8)
            result["hints"]["volatility_spike"] = volatility_change
            logger.debug(
                f"{agent_name}: Volatility spike detected: "
                f"{last_volatility:.2f} -> {volatility:.2f}"
            )

        # Check if entering crisis for the first time
        if volatility >= self.config.volatility_crisis_threshold:
            if not self._crisis_started.get(agent_name, False):
                self._crisis_started[agent_name] = True
                result["reasons"].append(TriggerReason.INITIAL_CRISIS)
                result["priority"] = max(result["priority"], 10)
                result["hints"]["crisis_entry"] = True
                logger.info(f"{agent_name}: Initial crisis entry detected")
        else:
            self._crisis_started[agent_name] = False

        # Check volatility threshold
        if volatility >= self.config.volatility_threshold:
            if TriggerReason.VOLATILITY_SPIKE not in result["reasons"]:
                result["reasons"].append(TriggerReason.VOLATILITY_THRESHOLD)
                result["priority"] = max(result["priority"], 5)
            result["hints"]["current_volatility"] = volatility

        return result if result["reasons"] else None

    def _check_liquidity(
        self,
        market_state: Dict[str, Any],
        agent_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check liquidity-based triggers."""
        market_liquidity = market_state.get("liquidity", 1.0)
        agent_liquidity = agent_state.get("liquidity", 0.20)

        result = {"reasons": [], "priority": 0, "hints": {}}

        # Check market-wide liquidity stress
        if market_liquidity <= self.config.liquidity_severe_threshold:
            result["reasons"].append(TriggerReason.LIQUIDITY_STRESS)
            result["priority"] = max(result["priority"], 9)
            result["hints"]["market_liquidity"] = market_liquidity
            result["hints"]["liquidity_severity"] = "severe"
        elif market_liquidity <= self.config.liquidity_stress_threshold:
            result["reasons"].append(TriggerReason.LIQUIDITY_STRESS)
            result["priority"] = max(result["priority"], 6)
            result["hints"]["market_liquidity"] = market_liquidity
            result["hints"]["liquidity_severity"] = "moderate"

        # Check agent-specific liquidity
        effective_liquidity = agent_liquidity * market_liquidity
        if effective_liquidity <= self.config.agent_liquidity_threshold:
            if TriggerReason.LIQUIDITY_STRESS not in result["reasons"]:
                result["reasons"].append(TriggerReason.LIQUIDITY_STRESS)
            result["priority"] = max(result["priority"], 7)
            result["hints"]["agent_effective_liquidity"] = effective_liquidity

        return result if result["reasons"] else None

    def _check_capital(
        self,
        agent_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check capital-based triggers."""
        current_capital = agent_state.get("capital", 100.0)
        initial_capital = agent_state.get("initial_capital", 100.0)

        result = {"reasons": [], "priority": 0, "hints": {}}

        # Check capital loss percentage
        if initial_capital > 0:
            capital_loss_pct = (initial_capital - current_capital) / initial_capital
            if capital_loss_pct >= self.config.capital_loss_threshold:
                result["reasons"].append(TriggerReason.CAPITAL_STRESS)
                result["priority"] = max(result["priority"], 7)
                result["hints"]["capital_loss_pct"] = capital_loss_pct

        # Check critical capital level
        if current_capital <= self.config.capital_critical_threshold:
            if TriggerReason.CAPITAL_STRESS not in result["reasons"]:
                result["reasons"].append(TriggerReason.CAPITAL_STRESS)
            result["priority"] = max(result["priority"], 8)
            result["hints"]["current_capital"] = current_capital

        return result if result["reasons"] else None

    def _check_peer_conditions(
        self,
        market_state: Dict[str, Any],
        agent_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check peer bank failure and stress triggers."""
        agent_name = agent_state.get("name", "unknown")
        failed_banks = market_state.get("failed_banks", [])
        stressed_banks = market_state.get("stressed_banks", [])

        result = {"reasons": [], "priority": 0, "hints": {}}

        # Check for new peer failures
        if self.config.peer_failure_trigger:
            known_failures = self._peer_failures_seen.get(agent_name, set())
            new_failures = set(failed_banks) - known_failures

            if new_failures:
                # Exclude self from peer failures
                new_failures.discard(agent_name)
                if new_failures:
                    result["reasons"].append(TriggerReason.PEER_FAILURE)
                    result["priority"] = max(result["priority"], 9)
                    result["hints"]["new_failed_banks"] = list(new_failures)
                    self._peer_failures_seen[agent_name].update(new_failures)
                    logger.info(
                        f"{agent_name}: Detected peer failures: {new_failures}"
                    )

        # Check for peer stress
        if stressed_banks:
            # Filter out self and count stressed peers
            stressed_peers = [
                b for b in stressed_banks
                if b.get("name") != agent_name and
                b.get("liquidity", 1.0) <= self.config.peer_stress_liquidity
            ]

            if len(stressed_peers) >= self.config.peer_stress_count_threshold:
                result["reasons"].append(TriggerReason.PEER_STRESS)
                result["priority"] = max(result["priority"], 6)
                result["hints"]["stressed_peer_count"] = len(stressed_peers)

        return result if result["reasons"] else None

    def _check_credit_rating(
        self,
        agent_state: Dict[str, Any],
        history: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check credit rating change triggers."""
        if not self.config.credit_downgrade_trigger:
            return None

        if not history:
            return None

        current_rating = agent_state.get("credit_rating")
        previous_rating = history.get("previous_credit_rating")

        if not current_rating or not previous_rating:
            return None

        # Simple rating comparison (assumes higher letter = better)
        rating_order = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
                       "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
                       "B+", "B", "B-", "CCC+", "CCC", "CCC-", "D"]

        try:
            current_idx = rating_order.index(current_rating)
            previous_idx = rating_order.index(previous_rating)

            if current_idx > previous_idx:  # Downgrade
                result = {
                    "reasons": [TriggerReason.CREDIT_DOWNGRADE],
                    "priority": 8,
                    "hints": {
                        "rating_change": f"{previous_rating} -> {current_rating}",
                        "notches_down": current_idx - previous_idx
                    }
                }
                return result
        except ValueError:
            pass  # Unknown rating

        return None

    def _check_market_events(
        self,
        market_state: Dict[str, Any],
        history: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check for significant market events in news/context."""
        news = market_state.get("news", "")
        events = (history or {}).get("events", [])

        # Combine news and events
        all_text = f"{news} " + " ".join(events)
        all_text_lower = all_text.lower()

        # Check for event keywords
        matched_keywords = [
            kw for kw in self.config.market_event_keywords
            if kw.lower() in all_text_lower
        ]

        if matched_keywords:
            return {
                "reasons": [TriggerReason.MARKET_EVENT],
                "priority": 7,
                "hints": {"matched_keywords": matched_keywords}
            }

        return None

    def _check_periodic(
        self,
        agent_name: str,
        current_step: int
    ) -> Optional[Dict[str, Any]]:
        """Check if periodic query is due."""
        query_history = self._query_history.get(agent_name, [])

        if not query_history:
            return None

        last_query = query_history[-1]

        if current_step - last_query >= self.config.periodic_check_interval:
            return {
                "reasons": [TriggerReason.PERIODIC_CHECK],
                "priority": 1,
                "hints": {"steps_since_last": current_step - last_query}
            }

        return None

    def _record_query(self, agent_name: str, step: int):
        """Record that a query was made at the given step."""
        if agent_name not in self._query_history:
            self._query_history[agent_name] = []
        self._query_history[agent_name].append(step)

    def reset(self):
        """Reset all tracking state (useful between simulation runs)."""
        self._query_history.clear()
        self._last_volatility.clear()
        self._crisis_started.clear()
        self._peer_failures_seen.clear()
        logger.info("RagTriggerPolicy state reset")

    def get_query_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get query statistics for an agent or all agents."""
        if agent_name:
            history = self._query_history.get(agent_name, [])
            return {
                "agent": agent_name,
                "total_queries": len(history),
                "query_steps": history
            }
        else:
            return {
                agent: {
                    "total_queries": len(steps),
                    "query_steps": steps
                }
                for agent, steps in self._query_history.items()
            }
