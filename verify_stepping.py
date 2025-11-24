from abm.model import FinancialCrisisModel
import logging

# Disable RAG logging to keep output clean
logging.getLogger('rag.retriever').setLevel(logging.WARNING)
logging.getLogger('abm.model').setLevel(logging.WARNING)

def test_stepping():
    print("Initializing Model...")
    model = FinancialCrisisModel(n_banks=2, use_slm=False, k_chunks=1)
    
    print(f"Initial Step: {model.steps}")
    
    for i in range(3):
        print(f"--- Loop {i+1} ---")
        model.step()
        print(f"Model Step after call: {model.steps}")
        
    if model.steps == 3:
        print("SUCCESS: Model stepped correctly (1, 2, 3)")
    else:
        print(f"FAILURE: Model skipped steps! Final step: {model.steps}")

if __name__ == "__main__":
    test_stepping()
