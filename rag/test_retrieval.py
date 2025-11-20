from rag.retriever import get_relevant_context

def test_retrieval():
    print("Testing RAG Retrieval...")
    
    # Test Query 1: General Crisis Question
    query1 = "What were the causes of the financial crisis?"
    print(f"\nQuery: {query1}")
    results1 = get_relevant_context(query1, k=2)
    for i, res in enumerate(results1):
        print(f"Result {i+1}:\n{res[:200]}...\n")

    # Test Query 2: Specific Entity (JPM)
    query2 = "What is JPM's liquidity position?"
    print(f"\nQuery: {query2}")
    results2 = get_relevant_context(query2, k=2) # Metadata filter can be added later
    for i, res in enumerate(results2):
        print(f"Result {i+1}:\n{res[:200]}...\n")

if __name__ == "__main__":
    test_retrieval()
