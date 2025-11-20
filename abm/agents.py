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
    def __init__(self, model, entity_data, slm=None, use_rag=False):
        super().__init__(model)
        self.name = entity_data.get('name', f'Bank_{self.unique_id}')
        self.capital = entity_data.get('capital', 100.0)  # Billions
        self.liquidity = entity_data.get('liquidity', 0.20)  # Ratio
        self.risk_score = entity_data.get('risk_score', 0.0)
        self.failed = False
        self.slm = slm  # Instance of LocalSLM
        self.use_rag = use_rag

    def step(self):
        if self.failed:
            return

        # 1. Query KG/RAG for context
        context = ""
        if self.use_rag:
            try:
                # Dynamic query based on state
                query = f"What are the risks for {self.name} in {self.model.current_year}? Market outlook?"
                # Import here to avoid circular imports if any, or just standard import at top
                from rag.retriever import get_relevant_context
                # Retrieve top 3 chunks
                chunks = get_relevant_context(query, k=3, filter_metadata={'year': self.model.current_year})
                context = "\n\n".join(chunks)
            except Exception as e:
                logger.error(f"RAG failed for {self.name}: {e}")
                context = "No external context available."
        else:
            context = "Standard market conditions apply. No specific news."

        # 2. SLM decides action
        action = self.decide_action(context)

        # 3. Execute action
        self.execute_action(action)

        # 4. Check failure condition
        if self.liquidity < 0.05 or self.capital < 0:
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
            
            prompt = template.format(
                bank_name=self.name,
                year=self.model.current_year if hasattr(self.model, 'current_year') else 2008,
                capital=self.capital,
                liquidity=self.liquidity,
                risk_score=self.risk_score,
                centrality=0.5, # Placeholder
                recent_events="Market volatility increasing.",
                similar_events=context,
                vix=45.0, # Placeholder
                ted_spread=1.5, # Placeholder
                unemployment=6.5 # Placeholder
            )

            response = self.slm.generate(prompt)
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
            self.liquidity += 0.05
            self.capital -= 1.0 # Cost of defensive measures
        elif action == 'MAINTAIN':
            pass

    def fail(self):
        self.failed = True
        logger.info(f"Bank {self.name} has FAILED")
