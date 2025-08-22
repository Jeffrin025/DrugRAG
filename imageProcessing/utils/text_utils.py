# imageProcessing/utils/text_utils.py

import re
import nltk

# Make sure punkt is available for sentence tokenization
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

def clean_text(text: str) -> str:
    """
    Basic text cleanup:
    - Removes extra whitespace
    - Normalizes line breaks
    - Strips leading/trailing spaces
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text.strip()

def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using NLTK.
    """
    from nltk.tokenize import sent_tokenize
    return sent_tokenize(text)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split long text into overlapping chunks.
    Useful for feeding into embeddings/vector DB.

    Args:
        text (str): input text
        chunk_size (int): target size of each chunk
        overlap (int): overlap size between chunks

    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def normalize_text(text: str) -> str:
    """
    Normalize text:
    - Lowercasing
    - Remove non-alphanumeric except basic punctuation
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\.,;:!?-]", "", text)
    return text

def deduplicate_chunks(chunks: list[str]) -> list[str]:
    """
    Remove near-duplicate chunks (basic hash-based).
    """
    seen = set()
    unique = []
    for c in chunks:
        c_clean = clean_text(c)
        if c_clean not in seen and c_clean:
            seen.add(c_clean)
            unique.append(c_clean)
    return unique
