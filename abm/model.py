from mesa import Model
from abm.agents import BankAgent
from slm.llama_client import LocalSLM
import logging

logger = logging.getLogger(__name__)

class FinancialCrisisModel(Model):
    """
    A model with some number of agents.
    """
    def __init__(self, n_banks=10, use_slm=False):
        super().__init__()
        self.num_agents = n_banks
        self.current_year = 2008
        
        # Initialize SLM if requested
        self.slm = None
        if use_slm:
            try:
                self.slm = LocalSLM()
                logger.info("SLM initialized for model")
            except Exception as e:
                logger.error(f"Failed to initialize SLM: {e}")

        # Create agents
        for i in range(self.num_agents):
            # Random initialization data
            entity_data = {
                'name': f'Bank_{i}',
                'capital': 100.0,
                'liquidity': 0.20,
                'risk_score': 0.1 * i
            }
            # Note: In Mesa 3.x, Agent adds itself to model.agents automatically via super().__init__ if model is passed
            # But we need to instantiate it.
            # Assign Group A (Insider) vs Group B (Noise)
            # First 50% are Insiders (RAG=True)
            is_insider = i < (self.num_agents // 2)
            
            a = BankAgent(self, entity_data, slm=self.slm, use_rag=is_insider)
            # self.agents.add(a) # Not needed if Agent.__init__ does it? 
            # Wait, Agent.__init__(unique_id, model) calls model.register_agent(self)
            
    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle().do("step")
