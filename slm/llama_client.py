import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging

logger = logging.getLogger(__name__)

class LocalSLM:
    def __init__(self, model_name="meta-llama/Llama-3.2-1B-Instruct", device_map="auto"):
        """
        Initialize the LocalSLM wrapper.
        
        Args:
            model_name (str): Hugging Face model identifier
            device_map (str): Device mapping strategy ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        logger.info(f"Loading SLM model: {model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map=device_map,
                low_cpu_mem_usage=True
            )
            
            # Set pad_token_id to eos_token_id if not set, to avoid warnings
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
            logger.info("SLM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SLM model: {e}")
            raise

    def generate(self, prompt, max_tokens=100, temperature=0.7):
        """
        Generate text based on the prompt.
        
        Args:
            prompt (str): Input text
            max_tokens (int): Maximum new tokens to generate
            temperature (float): Sampling temperature
            
        Returns:
            str: Generated text
        """
        try:
            # Use the pipeline for generation
            sequences = self.pipe(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                return_full_text=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = sequences[0]['generated_text'].strip()
            return generated_text
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return ""

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    try:
        slm = LocalSLM()
        response = slm.generate("What is the capital of France?")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Test failed: {e}")
