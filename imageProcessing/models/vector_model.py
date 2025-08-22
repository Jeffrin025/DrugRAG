# imageProcessing/models/vector_model.py

import uuid
import datetime
from typing import List, Optional

class Vector:
    def __init__(
        self,
        content_id: str,                 # ID of text chunk or image
        content_type: str,               # "text" or "image"
        embedding: List[float],          # vector representation
        document_id: Optional[str] = None,
        page_number: Optional[int] = None
    ):
        self.id = str(uuid.uuid4())      # unique vector ID
        self.content_id = content_id     # ties back to Document or Image model
        self.content_type = content_type
        self.embedding = embedding
        self.document_id = document_id
        self.page_number = page_number
        self.created_at = datetime.datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "embedding": self.embedding,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "created_at": self.created_at.isoformat()
        }
