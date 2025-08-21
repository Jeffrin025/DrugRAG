from rag_orchestrator import RAGOrchestrator

def main():
    # Initialize the system
    pdf_folder = "./pdf"
    gemini_api_key = "AIzaSyC-A38J-YOmAEej4M-m2VCDcHSTn-1MzTo"
    
    rag_system = RAGOrchestrator(pdf_folder, gemini_api_key)
    
    # Load PDFs
    print("Loading PDFs into the system...")
    rag_system.load_pdfs()
    
    # Example queries
    queries = [
        "What is the recommended intravenous dose of Orencia for rheumatoid arthritis?",
        "What are the most common side effects of Simponi ARIA?",
        "How should Orencia be administered subcutaneously?",
        "Are there any drug interactions between Orencia and methotrexate?"
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