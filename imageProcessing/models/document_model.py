# imageProcessing/models/document_model.py

import uuid
import datetime

class Document:
    def __init__(self, filename: str, filepath: str):
        self.id = str(uuid.uuid4())              # unique document ID
        self.filename = filename                 # original filename
        self.filepath = filepath                 # where it's stored
        self.uploaded_at = datetime.datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "uploaded_at": self.uploaded_at.isoformat()
        }

