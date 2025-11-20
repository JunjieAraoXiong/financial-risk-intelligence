import unittest
from slm.llama_client import LocalSLM
import logging

logging.basicConfig(level=logging.INFO)

class TestLocalSLM(unittest.TestCase):
    def test_generation(self):
        try:
            slm = LocalSLM()
            response = slm.generate("Hello, how are you?")
            print(f"Response: {response}")
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
        except Exception as e:
            self.fail(f"SLM generation failed: {e}")

if __name__ == '__main__':
    unittest.main()
