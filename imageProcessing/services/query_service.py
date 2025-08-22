# query_service.py

from imageProcessing.config import GEMINI_API_KEY
import google.generativeai as genai
from imageProcessing.services.vector_service import query_documents, add_document, delete_document, list_all_documents

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def run_query(query_text: str, top_k: int = 3) -> str:
    """
    Query the vector store and get an answer using Gemini.
    """
    # Get relevant docs from Chroma
    results = query_documents(query_text, top_k=top_k)

    if not results or not results.get("documents"):
        return "No relevant documents found."

    # Extract top docs
    docs = results["documents"][0]  # results["documents"] is a list of lists
    context = "\n\n".join(docs)

    # Send to Gemini for final answer
    prompt = f"""
    You are a helpful assistant.
    Use the context below to answer the question.

    Context:
    {context}

    Question:
    {query_text}

    Answer:
    """

    response = model.generate_content(prompt)
    return response.text.strip()


if __name__ == "__main__":
    user_query = "What are the most common side effects of Rinvoq?"
    print(run_query(user_query))
