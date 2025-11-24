from mesa import Model
# from mesa.time import RandomActivation # REMOVED: Deprecated in Mesa 3.0+
from abm.agents import BankAgent
from slm.llama_client import LocalSLM
from rag.retriever import get_context_multi_query, get_agent_context
import logging

logger = logging.getLogger(__name__)

class FinancialCrisisModel(Model):
    """
    A model with some number of agents.
    """
    def __init__(self, n_banks=10, use_slm=False, liquidity_factor=0.30, shock_week=5, k_chunks=5, crisis_volatility=0.80,
                 start_year=2008, initial_capital=100.0, initial_liquidity=0.30, failure_threshold=0.03):
        super().__init__()
        self.num_agents = n_banks
        self.start_year = start_year
        self.current_year = start_year
        self.week_count = 0 # Manual step counter
        self.crisis_liquidity_factor = liquidity_factor  # Configurable shock severity
        self.shock_week = shock_week  # Configurable shock timing
        self.k_chunks = k_chunks  # Configurable RAG retrieval
        self.crisis_volatility = crisis_volatility  # Configurable crisis volatility (0-1)
        
        # Configuration for agents
        self.agent_config = {
            'initial_capital': initial_capital,
            'initial_liquidity': initial_liquidity,
            'failure_threshold': failure_threshold
        }
        # self.schedule = RandomActivation(self) # REMOVED

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
            # Start with higher liquidity (0.30) to give agents room to maneuver
            # This allows survival even with liquidity_factor = 0.10 (effective = 0.03)
            entity_data = {
                'name': f'Bank_{i}',
                'capital': initial_capital,
                'liquidity': initial_liquidity,
                'risk_score': 0.1 * i
            }
            # Note: In Mesa 3.x, Agent adds itself to model.agents automatically via super().__init__ if model is passed
            # But we need to instantiate it.
            # Assign Group A (Insider) vs Group B (Noise)
            # First 50% are Insiders (RAG=True)
            is_insider = i < (self.num_agents // 2)
            
            a = BankAgent(self, entity_data, slm=self.slm, use_rag=is_insider, config=self.agent_config)
            # self.schedule.add(a) # REMOVED: Agents are automatically added to self.agents
            
    def get_date_string(self, step):
        """Map step to a month in 2008."""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        # Clamp to 0-11
        month_idx = (step - 1) % 12
        year_offset = (step - 1) // 12
        current_year = self.start_year + year_offset
        return f"{months[month_idx]} {current_year}"

    def step(self):
        """Advance the model by one step."""
        # self.current_year += 1 # REMOVED: This was incrementing year every week
        
        # Advance week
        # self.schedule.step() # REMOVED
        self.week_count += 1
        current_step = self.week_count
        
        # Map step to date
        self.current_week = current_step

        # Normal market conditions
        market_volatility = 0.10
        liquidity_factor = 1.0

        # "Lehman Shock" Scenario - triggers at shock_week
        # Each model.step() = 1 week in run_experiment.py
        if current_step >= self.shock_week:
            if current_step == self.shock_week:
                logger.warning(f"!!! LEHMAN SHOCK TRIGGERED at Week {self.shock_week} !!!")
                logger.warning(f"    Volatility: {self.crisis_volatility:.0%}, Liquidity Factor: {self.crisis_liquidity_factor}")
            market_volatility = self.crisis_volatility  # Configurable
            liquidity_factor = self.crisis_liquidity_factor  # Configurable
            
        # Centralized RAG Query using SOTA multi-query retrieval
        current_date = self.get_date_string(current_step)

        try:
            print(f"--- Model Querying RAG (SOTA Multi-Query + HyDE) for {current_date} ---")
            # Use new multi-query retrieval with dynamic queries based on market state
            chunks = get_context_multi_query(
                date=current_date,
                volatility=market_volatility,
                liquidity_factor=liquidity_factor,
                k=self.k_chunks,  # Configurable chunk count
                use_hyde=True
            )
            news_context = "\n\n".join(chunks)
            logger.info(f"Retrieved {len(chunks)} chunks via multi-query retrieval")
        except Exception as e:
            logger.error(f"Model RAG failed: {e}")
            news_context = "No external news available."

        # Update global context for agents
        self.market_context = {
            "volatility": market_volatility,
            "liquidity": liquidity_factor,
            "week": self.week_count,
            "news": news_context,
            "date": current_date,
            "get_agent_context": get_agent_context  # Pass function for agent-specific queries
        }

        self.agents.shuffle().do("step")
