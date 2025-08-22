project_root/
│── app.py                  # Flask entry point
│── config.py               # Configuration (paths, DB settings, OCR settings)
│── requirements.txt        # Dependencies
│── README.md               # Documentation
│
├── services/               # Core logic (business layer)
│   ├── pdf_service.py      # Extract text & images from PDFs
│   ├── ocr_service.py      # OCR for images (graphs, plots, etc.)
│   ├── image_service.py    # Image preprocessing, saving, metadata
│   ├── vector_service.py   # Embeddings + ChromaDB integration
│   └── query_service.py    # Search pipeline (query to results)
│
├── routes/                 # Flask routes (modularized endpoints)
│   ├── pdf_routes.py       # Upload & process PDFs
│   ├── query_routes.py     # Query handling (ask questions, retrieve images/info)
│   └── health_routes.py    # Health check / monitoring
│
├── models/                 # Database schemas / models
│   ├── document_model.py   # Metadata for PDFs (doc id, name, path, etc.)
│   ├── image_model.py      # Metadata for extracted images (image id, doc id, path, info)
│   └── vector_model.py     # Wrapper for ChromaDB storage handling
│
├── utils/                  # Helper functions
│   ├── file_utils.py       # File handling, storage paths
│   ├── text_utils.py       # Cleaning/normalizing extracted text
│   └── logging_utils.py    # Centralized logging
│
├── static/                 # To serve images
│   └── images/             # Saved extracted images
│
└── templates/              # If web UI is added later (HTML/Jinja2)
    └── index.html
├── tests/
│   ├── test_pdf_service.py
│   ├── test_vector_service.py
│   └── test_query_service.py
├── scripts/
│   ├── ingest.py
│   ├── db_init.py
config/
├── base_config.py
├── dev_config.py
└── prod_config.py
