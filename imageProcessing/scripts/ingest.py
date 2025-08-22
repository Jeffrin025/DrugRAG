import os
import sys

# add project root (DRUGPDF/) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from imageProcessing.config import CHROMA_PERSIST_DIR, GEMINI_API_KEY

from services import pdf_service, ocr_service, image_service, vector_service
from utils import logging_utils


logger = logging_utils.get_logger(__name__)

def ingest_pdf(pdf_path: str):
    """
    Ingests a PDF into the RAG pipeline:
      1. Extract text
      2. Extract images
      3. Run OCR on images
      4. Store everything in vector DB
    """
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return

    logger.info(f" Starting ingestion: {pdf_path}")

    # 1. Extract text from PDF
    text_chunks = pdf_service.extract_text(pdf_path)
    logger.info(f" Extracted {len(text_chunks)} text chunks")

    # 2. Extract images
    images = image_service.extract_images(pdf_path)
    logger.info(f" Extracted {len(images)} images")

    # 3. OCR on images → text
    ocr_texts = []
    for idx, img in enumerate(images, start=1):
        text = ocr_service.extract_text_from_image(img)
        if text.strip():
            ocr_texts.append(text)
        logger.info(f"🔎 OCR done for image {idx}")

    # Merge all text (direct + OCR)
    all_texts = text_chunks + ocr_texts

    # 4. Store in vector DB
    for chunk in all_texts:
        vector_service.store_text(chunk, metadata={"source": pdf_path})

    logger.info(f"🎉 Ingestion complete for {pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <pdf_path>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    ingest_pdf(pdf_file)
