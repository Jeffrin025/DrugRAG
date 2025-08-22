# routes/pdf_routes.py

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from ..services import pdf_service
from ..utils import file_utils

pdf_bp = Blueprint("pdf_routes", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@pdf_bp.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Endpoint to upload a PDF, extract text/images,
    and store metadata + embeddings.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            save_path = file_utils.save_pdf(file, filename)

            # Extract + store
            doc_id = pdf_service.process_pdf(save_path)

            return jsonify({"message": "PDF uploaded & processed", "doc_id": doc_id}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type. Only PDFs allowed."}), 400


@pdf_bp.route("/list", methods=["GET"])
def list_pdfs():
    """
    Endpoint to list all processed PDFs.
    """
    try:
        docs = pdf_service.list_pdfs()
        return jsonify({"documents": docs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
