import chromadb
import shutil
from typing import List, Dict, Any
import os

class EfficientVectorDB:
    """Vector database manager for storing and retrieving document chunks"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
    
    def initialize(self) -> bool:
        """Initialize the database with cleanup"""
        try:
            # Clean up existing database
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"Cleaned up existing database at {self.persist_directory}")
            
            # Create new client and collection
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name="medical_documents",
                metadata={"hnsw:space": "cosine", "description": "FDA drug labels and medical documents"}
            )
            print("Vector database initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
    
    def add_documents_batch(self, documents_batch: List[Dict[str, Any]]) -> bool:
        """Add a batch of documents to the database"""
        if not self.collection or not documents_batch:
            return False
        
        try:
            # Separate documents, metadatas, and ids
            documents = [doc["content"] for doc in documents_batch]
            metadatas = [doc["metadata"] for doc in documents_batch]
            ids = [doc["id"] for doc in documents_batch]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Added {len(documents_batch)} documents to database")
            return True
            
        except Exception as e:
            print(f"Error adding documents to database: {e}")
            return False
    
    def query(self, query_text: str, n_results: int = 5, **filters) -> List[Dict[str, Any]]:
        """Query the database with flexible filtering options"""
        if not self.collection:
            return []
        
        try:
            # Build where filter from kwargs
            where_filter = {}
            for key, value in filters.items():
                if value is not None:
                    where_filter[key] = value
            
            # Execute query
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results * 2, 20),  # Get more results for filtering
                where=where_filter if where_filter else None
            )
            
            return self._process_query_results(results, n_results)
            
        except Exception as e:
            print(f"Error querying database: {e}")
            return []
    
    def _process_query_results(self, results: Any, n_results: int) -> List[Dict[str, Any]]:
        """Process and rank query results"""
        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            return []
        
        scored_results = []
        
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            score = self._calculate_relevance_score(
                results["documents"][0][i],
                results["metadatas"][0][i]
            )
            
            scored_results.append({
                "chunk_text": results["documents"][0][i],
                "pdf_index": metadata["pdf_index"],
                "pdf_name": metadata["pdf_name"],
                "section": metadata["section"],
                "page_start": metadata["page_start"],
                "page_end": metadata["page_end"],
                "is_fda": metadata["is_fda"],
                "content_type": metadata.get("content_type", "general"),
                "score": score
            })
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:n_results]
    
    def _calculate_relevance_score(self, chunk_text: str, metadata: Dict[str, Any]) -> float:
        """Calculate relevance score based on content and metadata"""
        score = 0.0
        
        # Content type scoring
        content_type_weights = {
            "medical": 0.4,
            "tabular": 0.3,
            "general": 0.2,
            "metadata": 0.1
        }
        score += content_type_weights.get(metadata.get("content_type", "general"), 0.2)
        
        # FDA document bonus
        if metadata.get("is_fda", False):
            score += 0.3
        
        # Section importance (DOSAGE sections are most relevant for medical queries)
        section = metadata.get("section", "").lower()
        if any(key in section for key in ['dosage', 'administration']):
            score += 0.2
        elif any(key in section for key in ['adverse', 'warning', 'contraindication']):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0