from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_DIR = "rag/data/chroma_db"

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# Get collection stats
collection = vector_store._collection
print(f"Total documents in database: {collection.count()}")
print(f"\nSample query test:")
results = vector_store.similarity_search("financial crisis", k=3)
for i, doc in enumerate(results):
    print(f"\n--- Result {i+1} ---")
    print(f"Source: {doc.metadata.get('source', 'Unknown')}")
    print(f"Preview: {doc.page_content[:150]}...")
