# query_routes.py
from flask import Blueprint, request, jsonify
from services import query_service

# Create a blueprint
query_bp = Blueprint("query_bp", __name__)

@query_bp.route("/query", methods=["POST"])
def run_query():
    """
    Accepts a natural language query and returns an answer from Gemini + Chroma.
    """
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    query_text = data["query"]

    try:
        response = query_service.query_documents(query_text, top_k=5)
        return jsonify({"query": query_text, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
