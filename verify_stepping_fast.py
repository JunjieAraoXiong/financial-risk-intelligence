import sys
from unittest.mock import MagicMock

# Mock rag.retriever BEFORE importing abm.model
mock_rag = MagicMock()
sys.modules['rag.retriever'] = mock_rag
sys.modules['rag'] = MagicMock()

# Mock slm.llama_client
mock_slm = MagicMock()
sys.modules['slm.llama_client'] = mock_slm
sys.modules['slm'] = MagicMock()

from abm.model import FinancialCrisisModel

def test_stepping():
    print("Initializing Model (Mocked)...")
    model = FinancialCrisisModel(n_banks=2, use_slm=False, k_chunks=1)
    
    print(f"Initial Step: {model.week_count}")
    
    for i in range(3):
        print(f"--- Loop {i+1} ---")
        model.step()
        print(f"Model Step after call: {model.week_count}")
        
    if model.week_count == 3:
        print("SUCCESS: Model stepped correctly (1, 2, 3)")
    else:
        print(f"FAILURE: Model skipped steps! Final step: {model.week_count}")

if __name__ == "__main__":
    test_stepping()
