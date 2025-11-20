from transformers import pipeline

print("Testing connection with gpt2...")
try:
    generator = pipeline('text-generation', model='gpt2')
    print("Success! Loaded gpt2.")
except Exception as e:
    print(f"Failed: {e}")
