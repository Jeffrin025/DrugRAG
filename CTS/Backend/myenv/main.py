from rag_orchestrator import RAGOrchestrator
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    # Initialize the system for querying only
    pdf_folder = "./pdf"
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    print("Initializing RAG system for querying...")
    rag_system = RAGOrchestrator(pdf_folder, gemini_api_key)
    
    # Check database status and content
    print("Checking database status...")
    doc_count = rag_system.vector_db.get_document_count()
    print(f"Documents in database: {doc_count}")
    
    # List all PDFs in database for debugging
    # pdfs_in_db = rag_system.vector_db.list_all_documents()
    # print(f"PDFs in database: {pdfs_in_db}")
    
    # Example queries
    queries = [
        "Which adverse reaction showed the largest increase in incidence compared with placebo?"
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")
        
        response = rag_system.query(query)
        print(f"RESPONSE:\n{response}")
        print(f"{'='*80}")

if __name__ == "__main__":
    main()