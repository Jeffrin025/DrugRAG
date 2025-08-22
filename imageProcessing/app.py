"""from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Where to save uploaded PDFs
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Only allow PDFs
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # You can plug in your PDF parsing / OCR logic here
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "filepath": filepath
        }), 200

    return jsonify({"error": "Invalid file type, only PDFs allowed"}), 400


@app.route("/")
def index():
    return jsonify({"message": "PDF Upload API is running"})


if __name__ == "__main__":
    app.run(debug=True)
"""

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions

# ======================
# CONFIG
# ======================
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(
    name="pdf_collection",
    embedding_function=embedding_functions.DefaultEmbeddingFunction()
)

# ======================
# HELPERS
# ======================
def extract_text_from_pdf(pdf_path):
    """Extract text page by page from PDF"""
    text_chunks = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                text_chunks.append({"page": i + 1, "content": text})
    return text_chunks

def store_in_chroma(chunks, pdf_name):
    """Store chunks into ChromaDB"""
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk["content"]],
            metadatas=[{"page": chunk["page"], "source": pdf_name}],
            ids=[f"{pdf_name}_{i}"]
        )

# ======================
# ROUTES
# ======================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Extract & store
    chunks = extract_text_from_pdf(filepath)
    store_in_chroma(chunks, filename)

    return jsonify({"message": f"PDF '{filename}' uploaded and processed successfully!"})

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    query_text = data.get("query", "")

    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    results = collection.query(
        query_texts=[query_text],
        n_results=5
    )

    response = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        response.append({
            "content": doc,
            "page": meta["page"],
            "source": meta["source"]
        })

    return jsonify({"results": response})

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(debug=True)


