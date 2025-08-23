# import chromadb
# import shutil
# from typing import List, Dict, Any, Optional
# import os

# class EfficientVectorDB:
#     """Vector database manager for storing and retrieving document chunks"""
    
#     def __init__(self, persist_directory: str = "./chroma_db"):
#         self.persist_directory = persist_directory
#         self.client = None
#         self.collection = None
#         self._initialized = False
    
#     def initialize(self, reset: bool = False) -> bool:
#         """Initialize the database with optional cleanup"""
#         try:
#             # Clean up existing database if reset requested
#             if reset and os.path.exists(self.persist_directory):
#                 shutil.rmtree(self.persist_directory)
#                 print(f"Cleaned up existing database at {self.persist_directory}")
            
#             # Create or connect to client and collection
#             self.client = chromadb.PersistentClient(path=self.persist_directory)
#             self.collection = self.client.get_or_create_collection(
#                 name="medical_documents",
#                 metadata={"hnsw:space": "cosine", "description": "FDA drug labels and medical documents"}
#             )
            
#             self._initialized = True
#             if reset:
#                 print("Vector database initialized successfully")
#             else:
#                 print("Connected to existing vector database")
#             return True
            
#         except Exception as e:
#             print(f"Error initializing database: {e}")
#             self._initialized = False
#             return False
        
    
    
#     def is_initialized(self) -> bool:
#         """Check if database is initialized"""
#         return self._initialized and self.collection is not None
    
#     def add_documents_batch(self, documents_batch: List[Dict[str, Any]]) -> bool:
#         """Add a batch of documents to the database"""
#         if not self.is_initialized() or not documents_batch:
#             return False
        
#         try:
#             # Separate documents, metadatas, and ids
#             documents = [doc["content"] for doc in documents_batch]
#             metadatas = [doc["metadata"] for doc in documents_batch]
#             ids = [doc["id"] for doc in documents_batch]
            
#             # Add to collection
#             self.collection.add(
#                 documents=documents,
#                 metadatas=metadatas,
#                 ids=ids
#             )
            
#             print(f"Added {len(documents_batch)} documents to database")
#             return True
            
#         except Exception as e:
#             print(f"Error adding documents to database: {e}")
#             return False
    
    
#     def get_document_count(self) -> int:
#         """Get the number of documents in the collection"""
#         if not self.is_initialized():
#             return 0
#         try:
#             return self.collection.count()
#         except:
#             return 0
    
#     def query(self, query_text: str, n_results: int = 5, pdf_filter: str = None) -> List[Dict[str, Any]]:
#         """Query the database with PDF filtering and robust error handling"""
#         if not self.is_initialized():
#             return []
        
#         try:
#             # Create filter if specific PDF is mentioned
#             where_filter = None
#             if pdf_filter:
#                 # Look for PDF names containing the filter text
#                 where_filter = {"pdf_name": {"$contains": pdf_filter.lower()}}
            
#             results = self.collection.query(
#                 query_texts=[query_text],
#                 n_results=min(n_results * 3, 30),  # Get more results for better filtering
#                 where=where_filter
#             )
            
#             return self._process_query_results(results, n_results)
            
#         except Exception as e:
#             print(f"Error querying database: {e}")
#             # Fallback to query without any filters
#             try:
#                 results = self.collection.query(
#                     query_texts=[query_text],
#                     n_results=n_results * 2
#                 )
#                 return self._process_query_results(results, n_results)
#             except Exception as e2:
#                 print(f"Error in fallback query: {e2}")
#                 # Return empty results instead of crashing
#                 return []
    
#     def _process_query_results(self, results: Any, n_results: int) -> List[Dict[str, Any]]:
#         """Process and rank query results with robust metadata handling"""
#         if not results or not results["documents"] or len(results["documents"][0]) == 0:
#             return []
        
#         scored_results = []
        
#         for i in range(len(results["documents"][0])):
#             metadata = results["metadatas"][0][i]
            
#             # Handle both old and new metadata formats
#             page_start = metadata.get('pdf_page_start', metadata.get('page_start', 1))
#             page_end = metadata.get('pdf_page_end', metadata.get('page_end', page_start))
            
#             score = self._calculate_relevance_score(
#                 results["documents"][0][i],
#                 metadata
#             )
            
#             scored_results.append({
#                 "chunk_text": results["documents"][0][i],
#                 "pdf_index": metadata.get("pdf_index", 0),
#                 "pdf_name": metadata.get("pdf_name", "unknown"),
#                 "section": metadata.get("section", ""),
#                 "page_start": page_start,
#                 "page_end": page_end,
#                 "pdf_page_number": metadata.get("pdf_page_number", page_start),
#                 "pdf_page_start": metadata.get("pdf_page_start", page_start),
#                 "pdf_page_end": metadata.get("pdf_page_end", page_end),
#                 "is_fda": metadata.get("is_fda", False),
#                 "content_type": metadata.get("content_type", "general"),
#                 "doc_type": metadata.get("doc_type", "text"),
#                 "table_index": metadata.get("table_index"),
#                 "row_index": metadata.get("row_index"),
#                 "score": score
#             })
        
#         # Sort by score and return top results
#         scored_results.sort(key=lambda x: x["score"], reverse=True)
#         return scored_results[:n_results]
    
#     def _calculate_relevance_score(self, chunk_text: str, metadata: Dict[str, Any]) -> float:
#         """Calculate relevance score based on content and metadata"""
#         score = 0.0
        
#         # Content type scoring
#         content_type_weights = {
#             "medical": 0.4,
#             "tabular": 0.3,
#             "general": 0.2,
#             "metadata": 0.1
#         }
#         score += content_type_weights.get(metadata.get("content_type", "general"), 0.2)
        
#         # FDA document bonus
#         if metadata.get("is_fda", False):
#             score += 0.3
        
#         # Section importance (DOSAGE sections are most relevant for medical queries)
#         section = metadata.get("section", "").lower()
#         if any(key in section for key in ['dosage', 'administration']):
#             score += 0.2
#         elif any(key in section for key in ['adverse', 'warning', 'contraindication']):
#             score += 0.1
        
#         return min(score, 1.0)  # Cap at 1.0
#     def list_all_documents(self) -> List[str]:
   
#         if not self.is_initialized():
#             return []
        
#         try:
#             # Get all documents to see what's actually stored
#             results = self.collection.get()
#             pdf_names = set()
            
#             for metadata in results["metadatas"]:
#                 pdf_names.add(metadata.get("pdf_name", "unknown"))
            
#             return list(pdf_names)
#         except Exception as e:
#             print(f"Error listing documents: {e}")
#             return []



import chromadb
import shutil
from typing import List, Dict, Any, Optional
import os
import json

class EfficientVectorDB:
    """Enhanced Vector database manager with improved multimodal support"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialized = False
    
    def initialize(self, reset: bool = False) -> bool:
        """Initialize the database with optional cleanup"""
        try:
            # Clean up existing database if reset requested
            if reset and os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"Cleaned up existing database at {self.persist_directory}")
            
            # Create or connect to client and collection
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name="medical_documents",
                metadata={"hnsw:space": "cosine", "description": "FDA drug labels and medical documents with multimodal support"}
            )
            
            self._initialized = True
            if reset:
                print("Vector database initialized successfully")
            else:
                print("Connected to existing vector database")
            return True
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            self._initialized = False
            return False
        
    def is_initialized(self) -> bool:
        """Check if database is initialized"""
        return self._initialized and self.collection is not None
    
    def add_documents_batch(self, documents_batch: List[Dict[str, Any]]) -> bool:
        """Add a batch of documents to the database"""
        if not self.is_initialized() or not documents_batch:
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
    
    def get_document_count(self) -> int:
        """Get the number of documents in the collection"""
        if not self.is_initialized():
            return 0
        try:
            return self.collection.count()
        except:
            return 0
    
    def query(self, query_text: str, n_results: int = 8, pdf_filter: str = None, 
              content_types: List[str] = None) -> List[Dict[str, Any]]:
        """Enhanced query with content type filtering and multimodal support"""
        if not self.is_initialized():
            return []
        
        try:
            # Build where filter
            where_filter = {}
            
            if pdf_filter:
                where_filter["pdf_name"] = {"$contains": pdf_filter.lower()}
            
            if content_types:
                where_filter["content_type"] = {"$in": content_types}
            
            # Get more results for better filtering
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results * 3, 25),
                where=where_filter if where_filter else None
            )
            
            return self._process_query_results(results, n_results)
            
        except Exception as e:
            print(f"Error querying database: {e}")
            # Fallback to query without any filters
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=n_results * 2
                )
                return self._process_query_results(results, n_results)
            except Exception as e2:
                print(f"Error in fallback query: {e2}")
                return []
    
    def _process_query_results(self, results: Any, n_results: int) -> List[Dict[str, Any]]:
        """Process and rank query results with enhanced metadata handling"""
        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            return []
        
        scored_results = []
        
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            
            # Handle metadata parsing safely
            try:
                if isinstance(metadata.get('table_data_sample'), str):
                    metadata['table_data_sample'] = json.loads(metadata['table_data_sample'])
            except:
                metadata['table_data_sample'] = []
            
            # Get page information with proper fallbacks
            page_info = self._get_page_info(metadata)
            
            score = self._calculate_relevance_score(
                results["documents"][0][i],
                metadata,
                results["distances"][0][i] if results["distances"] else 0.5
            )
            
            scored_results.append({
                "chunk_text": results["documents"][0][i],
                "pdf_index": metadata.get("pdf_index", 0),
                "pdf_name": metadata.get("pdf_name", "unknown"),
                "section": metadata.get("section", ""),
                "page_start": page_info.get("start", 1),
                "page_end": page_info.get("end", 1),
                "pdf_page_number": metadata.get("pdf_page_number", page_info.get("start", 1)),
                "pdf_page_start": metadata.get("pdf_page_start", page_info.get("start", 1)),
                "pdf_page_end": metadata.get("pdf_page_end", page_info.get("end", 1)),
                "is_fda": metadata.get("is_fda", False),
                "content_type": metadata.get("content_type", "general"),
                "doc_type": metadata.get("doc_type", "text"),
                "table_index": metadata.get("table_index"),
                "row_index": metadata.get("row_index"),
                "image_index": metadata.get("image_index"),
                "score": score,
                "distance": results["distances"][0][i] if results["distances"] else 0.5
            })
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:n_results]
    
    def _get_page_info(self, metadata: Dict[str, Any]) -> Dict[str, int]:
        """Extract page information with proper fallbacks"""
        page_start = (
            metadata.get('pdf_page_start') or 
            metadata.get('page_start') or 
            metadata.get('pdf_page_number') or 
            1
        )
        
        page_end = (
            metadata.get('pdf_page_end') or 
            metadata.get('page_end') or 
            page_start
        )
        
        return {"start": page_start, "end": page_end}
    
    def _calculate_relevance_score(self, chunk_text: str, metadata: Dict[str, Any], distance: float) -> float:
        """Calculate enhanced relevance score"""
        base_score = 1.0 - min(distance, 1.0)  # Convert distance to similarity
        
        # Content type weights
        content_type_weights = {
            "medical": 0.5,
            "tabular": 0.4,
            "visual": 0.4,
            "general": 0.3,
            "metadata": 0.1
        }
        
        content_bonus = content_type_weights.get(metadata.get("content_type", "general"), 0.3)
        
        # FDA document bonus
        fda_bonus = 0.3 if metadata.get("is_fda", False) else 0.0
        
        # Section importance
        section = metadata.get("section", "").lower()
        section_bonus = 0.0
        if any(key in section for key in ['dosage', 'administration']):
            section_bonus = 0.2
        elif any(key in section for key in ['adverse', 'warning', 'contraindication']):
            section_bonus = 0.1
        
        # Document type bonus
        doc_type_bonus = 0.1 if metadata.get("doc_type") in ["table", "image"] else 0.0
        
        # Calculate final score
        final_score = base_score * 0.6 + content_bonus * 0.2 + fda_bonus * 0.1 + section_bonus * 0.1 + doc_type_bonus * 0.1
        
        return min(final_score, 1.0)
    
    def list_all_documents(self) -> List[str]:
        """List all unique PDF names in the database"""
        if not self.is_initialized():
            return []
        
        try:
            results = self.collection.get()
            pdf_names = set()
            
            for metadata in results["metadatas"]:
                pdf_name = metadata.get("pdf_name")
                if pdf_name and pdf_name != "unknown":
                    pdf_names.add(pdf_name)
            
            return list(pdf_names)
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []