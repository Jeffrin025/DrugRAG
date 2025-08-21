import os
from dotenv import load_dotenv
from rag_orchestrator import RAGOrchestrator

def main():
    load_dotenv()
    pdf_dir = os.environ.get("PDF_DIR", "./pdf")          # not used at query time, but ok to keep
    chroma_path = os.environ.get("CHROMA_PATH", "./chroma_db")
    gemini_key = os.environ.get("AIzaSyAPUWBdEabp0A1XkPNSoS6LQZMa6HNB_vI")         # optional; if missing, fallback mode is used

    rag = RAGOrchestrator(pdf_directory=pdf_dir, chroma_path=chroma_path, gemini_api_key=gemini_key)

    # Example queries
    queries = [
        "What is the recommended dosage of rinvoq for rheumatoid arthritis?",
        "What are the most common side effects of Simponi ARIA?",
        "How should Orencia be administered subcutaneously?",
        "Are there any drug interactions between Orencia and methotrexate?",
    ]

    for q in queries:
        print("\n" + "="*80)
        print("QUERY:", q)
        print("="*80)
        ans = rag.answer_query(q)
        print(ans)
        print("="*80)

if __name__ == "__main__":
    main()
