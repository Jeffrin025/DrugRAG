import os
from typing import List, Dict, Any, Optional
from pdf_processor import PDFProcessor
from vector_db import EfficientVectorDB
from query_processor import QueryProcessor

class RAGOrchestrator:
    """
    Simple orchestrator with two clear operations:
      1) ingest_directory(reset: bool)  -> build/add to persisted Chroma
      2) answer_query(query: str)       -> retrieve from persisted Chroma and answer
    """

    def __init__(self, pdf_directory: str, chroma_path: str = "./chroma_db", gemini_api_key: Optional[str] = None):
        self.pdf_dir = pdf_directory
        self.db = EfficientVectorDB(persist_directory=chroma_path, collection_name="medical_documents")
        self.pdf = PDFProcessor()
        self.qp = QueryProcessor(gemini_api_key=gemini_api_key)

    # ---------------------- INGESTION ---------------------- #
    def ingest_directory(self, reset: bool = False) -> int:
        if not os.path.isdir(self.pdf_dir):
            raise ValueError(f"PDF directory not found: {self.pdf_dir}")
        self.db.initialize(reset=reset)

        files = [f for f in os.listdir(self.pdf_dir) if f.lower().endswith(".pdf")]
        if not files:
            print("No PDFs to ingest.")
            return self.db.count()

        for idx, fname in enumerate(files, start=1):
            path = os.path.join(self.pdf_dir, fname)
            print(f"Ingesting [{idx}/{len(files)}] {fname} ...")
            text = self.pdf.extract_text_from_pdf(path)
            if not text.strip():
                print(f"  Skipped (no extractable text): {fname}")
                continue
            sections = self.pdf.extract_sections(text)
            for s in sections:
                s["chunks"] = self.pdf.chunk_content(s["content"])
            docs = self.pdf.prepare_documents_for_db(fname, idx-1, sections)
            ok = self.db.add_documents_batch(docs)
            if ok:
                print(f"  -> Ingested {len(docs)} chunks.")
            else:
                print(f"  -> Failed to add chunks for {fname}.")
        total = self.db.count()
        print(f"Ingestion complete. Total chunks in DB: {total}")
        return total

    # ----------------------- QUERYING ---------------------- #
    def answer_query(self, user_query: str) -> str:
        analysis = self.qp.analyze_query(user_query)
        chunks = self.db.query(
            user_query,
            n_results=5,
            pdf_name_contains=analysis.get("pdf_filter_contains"),
            is_fda=analysis.get("is_fda_specific"),
        )
        retrieved_info = self.qp.format_retrieved_info(chunks)
        return self.qp.answer(user_query, retrieved_info)
