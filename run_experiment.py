from abm.model import FinancialCrisisModel
import matplotlib.pyplot as plt
import pandas as pd
import logging

# Configure logging to show agent decisions
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_experiment():
    print("Starting Information Asymmetry Experiment...")
    print("Group A (Agents 0-4): Insiders (RAG=True)")
    print("Group B (Agents 5-9): Noise Traders (RAG=False)")
    
    # Initialize model with 10 banks
    model = FinancialCrisisModel(n_banks=10, use_slm=True)
    
    # Track survival
    history = []
    
    # Run for 52 weeks (1 year)
    for step in range(52):
        print(f"\n--- Week {step + 1} ---")
        model.step()
        
        # Collect stats
        alive_insiders = sum(1 for a in model.agents if a.use_rag and not a.failed)
        alive_noise = sum(1 for a in model.agents if not a.use_rag and not a.failed)
        
        history.append({
            'Week': step + 1,
            'Insiders_Alive': alive_insiders,
            'Noise_Alive': alive_noise,
            'Systemic_Risk': 0.0 # Placeholder if model has it
        })
        
        if alive_insiders == 0 and alive_noise == 0:
            print("All banks failed!")
            break

    # Results
    df = pd.DataFrame(history)
    print("\n--- Experiment Results ---")
    print(df.tail())
    
    # Save results
    df.to_csv("results/experiment_asymmetry.csv", index=False)
    print("Results saved to results/experiment_asymmetry.csv")

if __name__ == "__main__":
    run_experiment()
