# imageProcessing/models/image_model.py

import uuid
import datetime

class Image:
    def __init__(self, document_id: str, page_number: int, image_path: str):
        self.id = str(uuid.uuid4())              # unique image ID
        self.document_id = document_id           # links image to its PDF
        self.page_number = page_number           # page where image was found
        self.image_path = image_path             # stored file path
        self.extracted_at = datetime.datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "image_path": self.image_path,
            "extracted_at": self.extracted_at.isoformat()
        }
