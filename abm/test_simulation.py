import logging
from abm.model import FinancialCrisisModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simulation():
    logger.info("Starting test simulation with SLM...")
    
    # Initialize model with SLM enabled
    # Note: This might take a while to load the model
    model = FinancialCrisisModel(n_banks=2, use_slm=True)
    
    # Run for a few steps
    for i in range(3):
        logger.info(f"--- Step {i} ---")
        model.step()
        
    logger.info("Simulation completed.")

if __name__ == "__main__":
    test_simulation()
