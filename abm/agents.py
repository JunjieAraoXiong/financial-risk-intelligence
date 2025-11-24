from mesa import Agent
from slm.llama_client import LocalSLM
import logging
import os

logger = logging.getLogger(__name__)

class BankAgent(Agent):
    """
    Bank agent with capital, liquidity, risk metrics.
    Makes decisions via SLM based on KG context.
    """
    def __init__(self, model, entity_data, slm=None, use_rag=False, config=None):
        super().__init__(model)
        self.config = config or {}
        self.name = entity_data.get('name', f'Bank_{self.unique_id}')
        self.capital = entity_data.get('capital', 100.0)  # Billions
        self.liquidity = entity_data.get('liquidity', 0.20)  # Ratio
        self.risk_score = entity_data.get('risk_score', 0.0)
        self.failed = False
        self.slm = slm  # Instance of LocalSLM
        self.use_rag = use_rag
        self.last_action = None  # Track last decision for logging

    def step(self):
        if self.failed:
            return

        # 1. Query KG/RAG for context
        context = ""
        market_ctx = getattr(self.model, 'market_context', {})
        volatility = market_ctx.get('volatility', 0.10)
        liquidity_factor = market_ctx.get('liquidity', 1.0)
        current_date = market_ctx.get('date', 'September 2008')

        if self.use_rag:
            # Get agent-specific context tailored to this bank's situation
            get_agent_ctx = market_ctx.get('get_agent_context')
            if get_agent_ctx and volatility >= 0.15:
                # Only query RAG when market is stressed (optimization)
                try:
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
                    logger.info(f"{self.name}: Retrieved {len(chunks)} agent-specific chunks")
                except Exception as e:
                    logger.error(f"{self.name}: Agent RAG query failed: {e}")
                    context = market_ctx.get('news', "No news available.")
            else:
                # Use shared context when volatility is low
                context = market_ctx.get('news', "No news available.")
        else:
            context = "Standard market conditions apply. No specific news."

        # 2. SLM decides action
        # Optimization: Skip SLM if volatility is low (fast forward)
        if volatility < 0.15:
             action = 'MAINTAIN'
        else:
             action = self.decide_action(context)

        # 3. Execute action and track it
        self.last_action = action
        self.execute_action(action)

        # 4. Check failure condition
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
        self.failed = True
        logger.info(f"Bank {self.name} has FAILED")
