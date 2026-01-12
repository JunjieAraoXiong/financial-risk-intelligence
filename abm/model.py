from mesa import Model
# from mesa.time import RandomActivation # REMOVED: Deprecated in Mesa 3.0+
from abm.agents import BankAgent
from abm.rag_trigger_policy import RagTriggerPolicy, PolicyConfig
from slm.llama_client import LocalSLM
from rag.retriever import get_context_multi_query, get_agent_context
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class FinancialCrisisModel(Model):
    """
    A model simulating a financial crisis with bank agents.

    This model creates bank agents that make decisions based on market conditions.
    Some agents (insiders) have access to RAG for historical financial intelligence,
    while others (noise traders) do not.

    The model includes configurable crisis parameters (shock timing, volatility,
    liquidity) and a smart RAG trigger policy that determines when agents should
    query the RAG system.
    """

    def __init__(
        self,
        n_banks: int = 10,
        use_slm: bool = False,
        liquidity_factor: float = 0.30,
        shock_week: int = 5,
        k_chunks: int = 5,
        crisis_volatility: float = 0.80,
        start_year: int = 2008,
        initial_capital: float = 100.0,
        initial_liquidity: float = 0.30,
        failure_threshold: float = 0.03,
        rag_policy_config: Optional[PolicyConfig] = None
    ):
        """
        Initialize the financial crisis model.

        Args:
            n_banks: Number of bank agents (default 10).
            use_slm: Whether to use the local SLM for decisions (default False).
            liquidity_factor: Liquidity multiplier during crisis (default 0.30).
            shock_week: Week when the crisis shock triggers (default 5).
            k_chunks: Number of RAG chunks to retrieve (default 5).
            crisis_volatility: Market volatility during crisis (default 0.80).
            start_year: Starting year for simulation (default 2008).
            initial_capital: Initial capital for each bank in billions (default 100.0).
            initial_liquidity: Initial liquidity ratio for each bank (default 0.30).
            failure_threshold: Effective liquidity below which banks fail (default 0.03).
            rag_policy_config: Optional PolicyConfig for RAG trigger policy.
                              If None, uses default policy configuration.
        """
        super().__init__()
        self.num_agents = n_banks
        self.start_year = start_year
        self.current_year = start_year
        self.week_count = 0  # Manual step counter
        self.crisis_liquidity_factor = liquidity_factor  # Configurable shock severity
        self.shock_week = shock_week  # Configurable shock timing
        self.k_chunks = k_chunks  # Configurable RAG retrieval
        self.crisis_volatility = crisis_volatility  # Configurable crisis volatility (0-1)

        # RAG trigger policy configuration
        self.rag_policy_config = rag_policy_config

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
            # Start with higher liquidity (0.30) to give agents room to maneuver
            # This allows survival even with liquidity_factor = 0.10 (effective = 0.03)
            entity_data = {
                'name': f'Bank_{i}',
                'capital': initial_capital,
                'liquidity': initial_liquidity,
                'risk_score': 0.1 * i
            }
            # Note: In Mesa 3.x, Agent adds itself to model.agents automatically
            # via super().__init__ if model is passed.

            # Assign Group A (Insider) vs Group B (Noise)
            # First 50% are Insiders (RAG=True)
            is_insider = i < (self.num_agents // 2)

            a = BankAgent(
                self,
                entity_data,
                slm=self.slm,
                use_rag=is_insider,
                config=self.agent_config,
                policy_config=self.rag_policy_config if is_insider else None
            )
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

    def get_failed_banks(self) -> List[str]:
        """
        Get list of failed bank names.

        Returns:
            List of names of banks that have failed.
        """
        return [
            agent.name for agent in self.agents
            if isinstance(agent, BankAgent) and agent.failed
        ]

    def get_stressed_banks(self, liquidity_threshold: float = 0.10) -> List[Dict[str, Any]]:
        """
        Get list of stressed banks (low liquidity but not failed).

        Args:
            liquidity_threshold: Liquidity ratio below which a bank is stressed.

        Returns:
            List of dictionaries with stressed bank information.
        """
        stressed = []
        for agent in self.agents:
            if isinstance(agent, BankAgent) and not agent.failed:
                if agent.liquidity < liquidity_threshold:
                    stressed.append({
                        "name": agent.name,
                        "liquidity": agent.liquidity,
                        "capital": agent.capital
                    })
        return stressed

    def get_rag_stats(self) -> Dict[str, Any]:
        """
        Get RAG query statistics for all agents.

        Returns:
            Dictionary with aggregate and per-agent RAG statistics.
        """
        insider_stats = []
        total_queries = 0

        for agent in self.agents:
            if isinstance(agent, BankAgent) and agent.use_rag:
                stats = agent.get_rag_stats()
                insider_stats.append(stats)
                total_queries += stats.get("total_queries", 0)

        return {
            "total_queries": total_queries,
            "num_insider_agents": len(insider_stats),
            "avg_queries_per_insider": (
                total_queries / len(insider_stats) if insider_stats else 0
            ),
            "agent_stats": insider_stats
        }

    def get_survival_stats(self) -> Dict[str, Any]:
        """
        Get survival statistics by agent group.

        Returns:
            Dictionary with survival counts for insiders and noise traders.
        """
        insiders_alive = 0
        insiders_total = 0
        noise_alive = 0
        noise_total = 0

        for agent in self.agents:
            if isinstance(agent, BankAgent):
                if agent.use_rag:
                    insiders_total += 1
                    if not agent.failed:
                        insiders_alive += 1
                else:
                    noise_total += 1
                    if not agent.failed:
                        noise_alive += 1

        return {
            "insiders": {
                "alive": insiders_alive,
                "total": insiders_total,
                "survival_rate": insiders_alive / insiders_total if insiders_total > 0 else 0
            },
            "noise_traders": {
                "alive": noise_alive,
                "total": noise_total,
                "survival_rate": noise_alive / noise_total if noise_total > 0 else 0
            },
            "overall": {
                "alive": insiders_alive + noise_alive,
                "total": insiders_total + noise_total,
                "survival_rate": (
                    (insiders_alive + noise_alive) / (insiders_total + noise_total)
                    if (insiders_total + noise_total) > 0 else 0
                )
            }
        }
