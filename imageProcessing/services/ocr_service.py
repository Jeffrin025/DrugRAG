# ocr_service.py  
""""
What this does:
* Uses pdf2image to render PDF pages as images.
* Uses pytesseract to run OCR on each page.
"""

# ocr_service.py
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Path to Tesseract executable (update if needed)
# Example for Windows: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")


def extract_text_from_image_pdf(pdf_path: str) -> str:
    """
    Extract text from an image-based PDF using OCR.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        str: Extracted text content.
    """
    try:
        # Convert PDF to images
        pages = convert_from_path(pdf_path)
        extracted_text = []

        for page_number, page in enumerate(pages, start=1):
            # Convert page to text via OCR
            text = pytesseract.image_to_string(page, lang="eng")
            extracted_text.append(text)

        return "\n".join(extracted_text).strip()

    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {str(e)}")
