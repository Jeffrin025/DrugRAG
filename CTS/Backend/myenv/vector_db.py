import os
from typing import Any, Dict, List, Optional
import chromadb

class EfficientVectorDB:
    """
    Vector database manager for storing and retrieving document chunks.
    Uses persistent Chroma and NEVER deletes the DB unless reset=True.
    """

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "medical_documents"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client: Optional[chromadb.PersistentClient] = None
        self.collection = None

    def connect(self):
        if self.client is None:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "description": "FDA drug labels and medical documents"}
            )

    def initialize(self, reset: bool = False) -> bool:
        """
        Initialize the DB. If reset=True, drops the collection but does NOT delete sqlite file.
        This avoids Windows file-lock issues.
        """
        try:
            self.connect()
            if reset:
                try:
                    self.client.delete_collection(self.collection_name)
                except Exception:
                    pass
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    def add_documents_batch(self, documents_batch: List[Dict[str, Any]]) -> bool:
        if not documents_batch:
            return True
        self.connect()
        try:
            ids = [d["id"] for d in documents_batch]
            docs = [d["content"] for d in documents_batch]
            metas = [d["metadata"] for d in documents_batch]
            self.collection.add(ids=ids, documents=docs, metadatas=metas)
            print(f"Added {len(ids)} chunks.")
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    def count(self) -> int:
        self.connect()
        try:
            info = self.collection.get(limit=1)
            # Chroma doesn't return total count directly; fetch a page and use 'ids' length heuristics or get all ids.
            all_ids = self.collection.get(ids=None, where=None, limit=1_000_000).get("ids", [])
            return len(all_ids)
        except Exception:
            return 0

    def query(self, query_text: str, n_results: int = 5, pdf_name_contains: Optional[str] = None, is_fda: Optional[bool] = None) -> List[Dict[str, Any]]:
        self.connect()
        where: Dict[str, Any] = {}
        if is_fda is not None:
            where["is_fda"] = is_fda
        # For case-insensitive contains, we filter client-side after retrieving more results.
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results * 4, 40),
            where=where or None
        )
        processed: List[Dict[str, Any]] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        for doc, meta in zip(docs, metas):
            if not doc or not meta:
                continue
            if pdf_name_contains:
                if pdf_name_contains.lower() not in (meta.get("pdf_name_lc") or ""):
                    continue
            processed.append({
                "chunk_text": doc,
                "pdf_name": meta.get("pdf_name", "unknown"),
                "section": meta.get("section", ""),
                "page_start": meta.get("page_start", None),
                "page_end": meta.get("page_end", None),
                "is_fda": meta.get("is_fda", False),
                "content_type": meta.get("content_type", "general"),
                "score_hint": self._score_hint(meta),
            })
        processed.sort(key=lambda x: x["score_hint"], reverse=True)
        return processed[:n_results]

    def _score_hint(self, meta: Dict[str, Any]) -> float:
        score = 0.0
        ct = meta.get("content_type", "general")
        score += {"medical": 0.4, "tabular": 0.3, "general": 0.2, "metadata": 0.1}.get(ct, 0.2)
        if meta.get("is_fda"):
            score += 0.3
        sec = (meta.get("section") or "").lower()
        if "dosage" in sec or "administration" in sec:
            score += 0.2
        elif any(k in sec for k in ["adverse", "warning", "contraindication"]):
            score += 0.1
        return min(score, 1.0)
