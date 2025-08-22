# pdf_service.py
"""
What this does:
* Saves the uploaded PDF inside an uploads/ directory.
* Extracts raw text from each page using PyPDF2.
* Returns the combined extracted text (ready to be split and pushed into ChromaDB).
"""
import os
from PyPDF2 import PdfReader

UPLOAD_FOLDER = "uploads"

def save_uploaded_pdf(file):
    """
    Saves uploaded PDF file to the uploads folder.
    """
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    return file_path


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""  # handle empty pages gracefully
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text.strip()
