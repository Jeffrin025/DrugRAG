# vector_service.py

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from imageProcessing.config import CHROMA_PERSIST_DIR

import chromadb
from imageProcessing.config import Config

# Persistent client (recommended)
chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_DIR)
# # Initialize Chroma client
# chroma_client = chromadb.Client(
#     Settings(persist_directory=CHROMA_PERSIST_DIR, chroma_db_impl="duckdb+parquet")
# )

# Collection name
COLLECTION_NAME = "drug_docs"

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_or_create_collection():
    """
    Create or fetch the persistent Chroma collection.
    """
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def add_document(doc_id: str, text: str, metadata: dict = None):
    """
    Add a document and its embeddings to the Chroma collection.
    """
    collection = get_or_create_collection()
    embedding = embedding_model.encode(text).tolist()
    collection.add(documents=[text], metadatas=[metadata or {}], ids=[doc_id], embeddings=[embedding])
    print(f" Document {doc_id} added to ChromaDB.")


def query_documents(query: str, top_k: int = 5):
    """
    Query the vector DB for most similar documents.
    """
    collection = get_or_create_collection()
    query_embedding = embedding_model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results


def delete_document(doc_id: str):
    """
    Delete a document from ChromaDB by its ID.
    """
    collection = get_or_create_collection()
    collection.delete(ids=[doc_id])
    print(f" Document {doc_id} deleted from ChromaDB.")


def list_all_documents():
    """
    List all documents stored in the collection.
    """
    collection = get_or_create_collection()
    return collection.get()
