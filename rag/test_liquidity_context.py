import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.query_generator import QueryGenerator

class TestLiquidityContext(unittest.TestCase):
    def test_generate_agent_queries_normal(self):
        queries = QueryGenerator.generate_agent_queries(
            bank_name="Bank_0",
            date="September 2008",
            capital=100.0,
            liquidity=0.30,
            risk_score=0.1,
            volatility=0.10,
            liquidity_factor=1.0
        )
        # Should NOT contain crisis keywords
        self.assertFalse(any("liquidity crisis" in q for q in queries))
        print(f"Normal queries: {queries}")

    def test_generate_agent_queries_crisis(self):
        queries = QueryGenerator.generate_agent_queries(
            bank_name="Bank_0",
            date="September 2008",
            capital=100.0,
            liquidity=0.30,
            risk_score=0.1,
            volatility=0.80,
            liquidity_factor=0.10 # Severe crisis
        )
        # Should contain crisis keywords
        self.assertTrue(any("liquidity crisis" in q for q in queries))
        self.assertTrue(any("systemic banking crisis" in q for q in queries))
        print(f"Crisis queries: {queries}")

if __name__ == '__main__':
    unittest.main()
