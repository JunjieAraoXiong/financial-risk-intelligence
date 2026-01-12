from mesa import Agent
from slm.llama_client import LocalSLM
from abm.rag_trigger_policy import RagTriggerPolicy, PolicyConfig, TriggerReason
import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class BankAgent(Agent):
    """
    Bank agent with capital, liquidity, risk metrics.
    Makes decisions via SLM based on KG context.

    The agent uses a RagTriggerPolicy to determine when to query the RAG system
    for historical financial intelligence. The policy considers multiple factors:
    - Market volatility levels and spikes
    - Liquidity stress (market-wide and agent-specific)
    - Peer bank failures and stress
    - Credit rating changes
    - Capital levels and losses
    """

    def __init__(
        self,
        model,
        entity_data: Dict[str, Any],
        slm=None,
        use_rag: bool = False,
        config: Optional[Dict[str, Any]] = None,
        rag_policy: Optional[RagTriggerPolicy] = None,
        policy_config: Optional[PolicyConfig] = None
    ):
        """
        Initialize a BankAgent.

        Args:
            model: The Mesa model this agent belongs to.
            entity_data: Dictionary with agent initialization data:
                - name: str (optional, defaults to Bank_{id})
                - capital: float (billions, default 100.0)
                - liquidity: float (ratio, default 0.20)
                - risk_score: float (default 0.0)
            slm: Optional LocalSLM instance for decision making.
            use_rag: Whether this agent can use RAG for context.
            config: Optional configuration dictionary.
            rag_policy: Optional RagTriggerPolicy instance.
                       If not provided and use_rag is True, creates a default policy.
            policy_config: Optional PolicyConfig for creating a new policy.
        """
        super().__init__(model)
        self.config = config or {}
        self.name = entity_data.get('name', f'Bank_{self.unique_id}')
        self.capital = entity_data.get('capital', 100.0)  # Billions
        self.initial_capital = self.capital  # Track for loss calculations
        self.liquidity = entity_data.get('liquidity', 0.20)  # Ratio
        self.risk_score = entity_data.get('risk_score', 0.0)
        self.credit_rating = entity_data.get('credit_rating', 'A')  # Default rating
        self.previous_credit_rating = self.credit_rating
        self.failed = False
        self.slm = slm  # Instance of LocalSLM
        self.use_rag = use_rag
        self.last_action = None  # Track last decision for logging
        self.last_rag_trigger = None  # Track last RAG trigger result
        self.rag_query_count = 0  # Track total RAG queries

        # Initialize RAG trigger policy
        if rag_policy:
            self.rag_policy = rag_policy
        elif use_rag:
            self.rag_policy = RagTriggerPolicy(policy_config)
        else:
            self.rag_policy = None

    def step(self):
        if self.failed:
            return

        # 1. Build state for RAG trigger policy
        market_ctx = getattr(self.model, 'market_context', {})
        volatility = market_ctx.get('volatility', 0.10)
        liquidity_factor = market_ctx.get('liquidity', 1.0)
        current_date = market_ctx.get('date', 'September 2008')

        # Build market state for policy
        market_state = self._build_market_state(market_ctx)

        # Build agent state for policy
        agent_state = self._build_agent_state()

        # Build history for policy
        history = self._build_history()

        # 2. Query KG/RAG for context using smart trigger policy
        context = self._get_rag_context(market_state, agent_state, history, market_ctx)

        # 3. SLM decides action
        # Optimization: Skip SLM if volatility is low (fast forward)
        if volatility < 0.15:
            action = 'MAINTAIN'
        else:
            action = self.decide_action(context)

        # 4. Execute action and track it
        self.last_action = action
        self.execute_action(action)

        # 5. Check failure condition
        # Apply global liquidity factor to actual available liquidity
        market_ctx = getattr(self.model, 'market_context', {})
        liquidity_factor = market_ctx.get('liquidity', 1.0)
        effective_liquidity = self.liquidity * liquidity_factor

        # Log liquidity status for debugging
        if volatility >= 0.15:
            logger.debug(f"{self.name}: liquidity={self.liquidity:.2f}, factor={liquidity_factor:.2f}, effective={effective_liquidity:.3f}, capital={self.capital:.1f}B")

        # Failure threshold - need effective liquidity > threshold or positive capital
        failure_threshold = self.config.get('failure_threshold', 0.03)
        if effective_liquidity < failure_threshold or self.capital < 0:
            logger.info(f"{self.name} FAILING: effective_liquidity={effective_liquidity:.3f}, capital={self.capital:.1f}B")
            self.fail()

    def decide_action(self, context):
        if not self.slm:
            # Fallback to rule-based if SLM not available
            if self.liquidity < 0.15:
                return 'DEFENSIVE'
            else:
                return 'MAINTAIN'

        # Construct prompt
        try:
            # Load prompt template (ensure this file exists)
            prompt_path = 'slm/prompts/bank_decision.txt'
            if not os.path.exists(prompt_path):
                 # Fallback prompt if file doesn't exist
                 template = """
                 You are {bank_name}. 
                 Year: {year}. 
                 Capital: {capital}. Liquidity: {liquidity}.
                 Context: {similar_events}
                 
                 Decide action (DEFENSIVE or MAINTAIN).
                 """
            else:
                with open(prompt_path, 'r') as f:
                    template = f.read()
            

            # Get market context from model
            market_ctx = getattr(self.model, 'market_context', {})
            volatility = market_ctx.get('volatility', 0.15) # Default 15%
            liquidity_factor = market_ctx.get('liquidity', 1.0)

            # Determine status labels for clarity
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

            # Construct chat messages
            system_prompt = """You are a bank executive making risk decisions.

DECISION FRAMEWORK:
- MAINTAIN: volatility < 30% AND liquidity factor > 0.50 (normal conditions)
- DEFENSIVE: volatility > 50% OR liquidity factor < 0.30 (crisis/severe stress)

Both decisions are valid. Choose based on actual market conditions.
Output exactly one word: DEFENSIVE or MAINTAIN."""

            user_prompt = template.format(
                bank_name=self.name,
                year=self.model.current_year if hasattr(self.model, 'current_year') else 2008,
                capital=self.capital,
                liquidity=self.liquidity * liquidity_factor, # Effective liquidity
                risk_score=self.risk_score,
                centrality=0.5, # Placeholder
                similar_events=context,
                vix=volatility * 100, # Approximation
                ted_spread=1.5 + (volatility * 10), # Approximation
                volatility_status=volatility_status,
                liquidity_factor_value=liquidity_factor,
                liquidity_status=liquidity_status,
                unemployment=6.5 # Placeholder
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.slm.generate(messages)
            logger.info(f"SLM Response for {self.name} (RAG={self.use_rag}): {response}")
            
            # Parse response
            if "DEFENSIVE" in response.upper():
                return "DEFENSIVE"
            elif "MAINTAIN" in response.upper():
                return "MAINTAIN"
            else:
                return "MAINTAIN" # Default

        except Exception as e:
            logger.error(f"Error in decide_action: {e}")
            return "MAINTAIN"

    def execute_action(self, action):
        if action == 'DEFENSIVE':
            # Defensive action: increase liquidity buffer at cost of capital
            self.liquidity += 0.08  # More significant liquidity boost
            self.capital -= 2.0  # Higher cost reflects emergency measures
            logger.debug(f"{self.name}: DEFENSIVE - liquidity now {self.liquidity:.2f}, capital now {self.capital:.1f}B")
        elif action == 'MAINTAIN':
            # Maintaining strategy - no changes but slight liquidity drain during crisis
            market_ctx = getattr(self.model, 'market_context', {})
            volatility = market_ctx.get('volatility', 0.10)
            if volatility > 0.50:  # During crisis, maintaining costs liquidity
                self.liquidity -= 0.02
                logger.debug(f"{self.name}: MAINTAIN during crisis - liquidity drained to {self.liquidity:.2f}")

    def fail(self):
        """
        Mark this bank as failed and notify the model.

        When a bank fails, it triggers contagion propagation if the model
        has a contagion network configured. The model handles the cascade
        effects through its contagion mechanism.
        """
        if self.failed:
            return  # Already failed, prevent double-counting

        self.failed = True
        logger.info(f"Bank {self.name} has FAILED")

        # Notify model to propagate contagion
        if hasattr(self.model, 'on_bank_failure'):
            self.model.on_bank_failure(self)

    def _build_market_state(self, market_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the market state dictionary for the RAG trigger policy.

        Args:
            market_ctx: The market context from the model.

        Returns:
            Dictionary with market state information.
        """
        # Get list of failed banks from model
        failed_banks = []
        stressed_banks = []

        if hasattr(self.model, 'agents'):
            for agent in self.model.agents:
                if isinstance(agent, BankAgent) and agent.name != self.name:
                    if agent.failed:
                        failed_banks.append(agent.name)
                    elif agent.liquidity < 0.10:  # Stressed
                        stressed_banks.append({
                            "name": agent.name,
                            "liquidity": agent.liquidity,
                            "capital": agent.capital
                        })

        return {
            "volatility": market_ctx.get('volatility', 0.10),
            "liquidity": market_ctx.get('liquidity', 1.0),
            "week": market_ctx.get('week', 0),
            "news": market_ctx.get('news', ''),
            "date": market_ctx.get('date', 'September 2008'),
            "failed_banks": failed_banks,
            "stressed_banks": stressed_banks
        }

    def _build_agent_state(self) -> Dict[str, Any]:
        """
        Build the agent state dictionary for the RAG trigger policy.

        Returns:
            Dictionary with agent state information.
        """
        return {
            "name": self.name,
            "capital": self.capital,
            "initial_capital": self.initial_capital,
            "liquidity": self.liquidity,
            "risk_score": self.risk_score,
            "credit_rating": self.credit_rating
        }

    def _build_history(self) -> Dict[str, Any]:
        """
        Build the history dictionary for the RAG trigger policy.

        Returns:
            Dictionary with historical information for trigger decisions.
        """
        # Track recent events (could be expanded)
        events = []

        # Include any market events from the news context
        market_ctx = getattr(self.model, 'market_context', {})
        news = market_ctx.get('news', '')

        # Simple event extraction from news (could be more sophisticated)
        event_keywords = [
            'bankruptcy', 'failure', 'collapse', 'crisis', 'default',
            'bailout', 'intervention', 'downgrade', 'layoff', 'merger'
        ]
        for keyword in event_keywords:
            if keyword.lower() in news.lower():
                events.append(f"Market event: {keyword}")

        return {
            "previous_credit_rating": self.previous_credit_rating,
            "events": events
        }

    def _get_rag_context(
        self,
        market_state: Dict[str, Any],
        agent_state: Dict[str, Any],
        history: Dict[str, Any],
        market_ctx: Dict[str, Any]
    ) -> str:
        """
        Get RAG context based on the smart trigger policy.

        Uses the RagTriggerPolicy to determine whether to query RAG,
        and if so, retrieves agent-specific context.

        Args:
            market_state: Current market conditions.
            agent_state: Agent's current state.
            history: Historical data.
            market_ctx: Original market context from model.

        Returns:
            Context string for decision making.
        """
        if not self.use_rag:
            return "Standard market conditions apply. No specific news."

        # Use the RAG trigger policy to decide if we should query
        if self.rag_policy:
            trigger_result = self.rag_policy.should_query_rag(
                market_state, agent_state, history
            )
            self.last_rag_trigger = trigger_result

            if not trigger_result.should_trigger:
                # Policy says don't query - use shared context
                logger.debug(f"{self.name}: RAG not triggered - using shared context")
                return market_ctx.get('news', "No news available.")

            # Log trigger reasons
            reason_names = [r.value for r in trigger_result.reasons]
            logger.info(
                f"{self.name}: RAG triggered (reasons: {reason_names}, "
                f"priority: {trigger_result.priority})"
            )
        else:
            # Fallback to old behavior if no policy
            volatility = market_state.get('volatility', 0.10)
            if volatility < 0.15:
                return market_ctx.get('news', "No news available.")

        # Query RAG for agent-specific context
        get_agent_ctx = market_ctx.get('get_agent_context')
        if not get_agent_ctx:
            return market_ctx.get('news', "No news available.")

        try:
            current_date = market_state.get('date', 'September 2008')
            volatility = market_state.get('volatility', 0.10)

            # Add context hints from trigger policy to influence retrieval
            context_hints = {}
            if self.last_rag_trigger and self.last_rag_trigger.context_hints:
                context_hints = self.last_rag_trigger.context_hints

            chunks = get_agent_ctx(
                bank_name=self.name,
                date=current_date,
                capital=self.capital,
                liquidity=self.liquidity,
                risk_score=self.risk_score,
                volatility=volatility,
                k=3
            )
            context = "\n\n".join(chunks)
            self.rag_query_count += 1
            logger.info(
                f"{self.name}: Retrieved {len(chunks)} agent-specific chunks "
                f"(total queries: {self.rag_query_count})"
            )
            return context

        except Exception as e:
            logger.error(f"{self.name}: Agent RAG query failed: {e}")
            return market_ctx.get('news', "No news available.")

    def get_rag_stats(self) -> Dict[str, Any]:
        """
        Get RAG query statistics for this agent.

        Returns:
            Dictionary with RAG usage statistics.
        """
        stats = {
            "name": self.name,
            "use_rag": self.use_rag,
            "total_queries": self.rag_query_count,
            "last_trigger": None
        }

        if self.last_rag_trigger:
            stats["last_trigger"] = {
                "triggered": self.last_rag_trigger.should_trigger,
                "reasons": [r.value for r in self.last_rag_trigger.reasons],
                "priority": self.last_rag_trigger.priority
            }

        if self.rag_policy:
            stats["policy_stats"] = self.rag_policy.get_query_stats(self.name)

        return stats
