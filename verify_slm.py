from slm.llama_client import LocalSLM
import logging

logging.basicConfig(level=logging.INFO)

def test_slm():
    print("Initializing SLM...")
    slm = LocalSLM()
    
    print("\nTesting Chat Format...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Output only one word."},
        {"role": "user", "content": "What is the opposite of up?"}
    ]
    response = slm.generate(messages)
    print(f"Response: {response}")
    
    assert "down" in response.lower() or "Down" in response, f"Unexpected response: {response}"
    print("Test Passed!")

if __name__ == "__main__":
    test_slm()
