# image_service.py
import os
import fitz  # PyMuPDF for image-to-text if needed
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from werkzeug.utils import secure_filename
from imageProcessing.config import CHROMA_PERSIST_DIR, GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Setup ChromaDB client
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=GEMINI_API_KEY, model_name="models/embedding-001")

# Create/get collection
collection = chroma_client.get_or_create_collection(name="knowledge_base", embedding_function=embedding_fn)

UPLOAD_FOLDER = "uploads/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_image(file):
    """Save uploaded image to local folder and return path."""
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath

def extract_text_from_image(image_path):
    """Use PyMuPDF OCR-like extraction for text from image."""
    doc = fitz.open(image_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text.strip()

def store_image_in_db(image_path):
    """Extract text, embed, and store in ChromaDB."""
    text = extract_text_from_image(image_path)
    if text:
        collection.add(
            documents=[text],
            metadatas=[{"source": image_path}],
            ids=[f"img_{os.path.basename(image_path)}"]
        )
    return text
