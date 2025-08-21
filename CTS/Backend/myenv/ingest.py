import os
from dotenv import load_dotenv
from rag_orchestrator import RAGOrchestrator

def main():
    load_dotenv()
    pdf_dir = os.environ.get("PDF_DIR", "./pdf")
    chroma_path = os.environ.get("CHROMA_PATH", "./chroma_db")
    gemini_key = os.environ.get("AIzaSyAPUWBdEabp0A1XkPNSoS6LQZMa6HNB_vI")  # optional

    rag = RAGOrchestrator(pdf_directory=pdf_dir, chroma_path=chroma_path, gemini_api_key=gemini_key)

    # Set reset=True ONLY if you want to rebuild from scratch.
    rag.ingest_directory(reset=True)

if __name__ == "__main__":
    main()
