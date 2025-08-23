# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from rag_orchestrator import RAGOrchestrator
# from dotenv import load_dotenv
# import google.generativeai as genai
# from enum import Enum
# import os
# from pdf_query_handler import init_pdf_query_handler, pdf_handler
# import uuid
# from werkzeug.utils import secure_filename
# load_dotenv()

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend communication

# # Initialize RAG system
# pdf_folder = "./pdf"
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# rag_system = None
# init_pdf_query_handler(gemini_api_key)

# class QueryIntent(Enum):
#     DRUG_RELATED = "drug_related"  # Query is about drugs, medications, pharmacology
#     GREETING = "greeting"          # Hello, hi, etc.
#     IRRELEVANT = "irrelevant"      # Everything else
# def classify_and_handle_query(query: str):
#     """
#     Uses the Gemini API to classify the user's query intent and generate appropriate responses.
#     For greeting and irrelevant queries, the LLM itself generates the response.
#     """
#     # System prompt that handles both classification and response generation
#     classification_prompt = f"""
#     You are a strict pharmaceutical chatbot. Analyze the user's query and:

#     1. If this is a GREETING (hello, hi, hey, greetings, how are you): 
#        - Respond with: "GREETING_RESPONSE: [your friendly greeting here]"

#     2. If this is IRRELEVANT (anything not related to drugs, medicine, pharmaceuticals, health conditions, treatments):
#        - Respond with: "IRRELEVANT_RESPONSE: [your polite decline here]"

#     3. If this is DRUG-RELATED (anything about drugs, medications, side effects, interactions, dosage, pharmacology, medical conditions):
#        - Respond with only: "DRUG_RELATED_QUERY"

#     User Query: "{query}"

#     Your response:
#     """

#     try:
#         # Use a fast, cheap model for this task
#         genai.configure(api_key=gemini_api_key)
#         model = genai.GenerativeModel('gemini-1.5-flash')
#         response = model.generate_content(classification_prompt)
#         response_text = response.text.strip()

#         # Check the response type
#         if "DRUG_RELATED_QUERY" in response_text:
#             return QueryIntent.DRUG_RELATED, None
#         elif "GREETING_RESPONSE:" in response_text:
#             # Extract just the response part
#             greeting_response = response_text.split("GREETING_RESPONSE:", 1)[1].strip()
#             return QueryIntent.GREETING, greeting_response
#         elif "IRRELEVANT_RESPONSE:" in response_text:
#             # Extract just the response part
#             irrelevant_response = response_text.split("IRRELEVANT_RESPONSE:", 1)[1].strip()
#             return QueryIntent.IRRELEVANT, irrelevant_response
#         else:
#             # Fallback if the model doesn't follow instructions
#             print(f"Unexpected response format: {response_text}")
#             return QueryIntent.DRUG_RELATED, None

#     except Exception as e:
#         print(f"Error during intent classification: {e}. Defaulting to drug_related.")
#         return QueryIntent.DRUG_RELATED, None

# def initialize_rag_system():
#     """Initialize the RAG system"""
#     global rag_system
#     try:
#         rag_system = RAGOrchestrator(pdf_folder, gemini_api_key)
        
#         # Check if database has documents
#         if not rag_system.vector_db.is_initialized():
#             if not rag_system.vector_db.initialize(reset=False):
#                 return False
        
#         if rag_system.vector_db.get_document_count() == 0:
#             return False
            
#         return True
#     except Exception as e:
#         print(f"Error initializing RAG system: {e}")
#         return False

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'database_initialized': rag_system is not None and rag_system.vector_db.is_initialized(),
#         'document_count': rag_system.vector_db.get_document_count() if rag_system else 0
#     })

# @app.route('/api/query', methods=['POST'])
# def process_query():
#     """Process user query"""
#     try:
#         data = request.get_json()
#         query = data.get('query', '').strip()
        
#         if not query:
#             return jsonify({'error': 'Query is required'}), 400
        
#         if not rag_system:
#             initialized = initialize_rag_system()
#             if not initialized:
#                 return jsonify({'error': 'RAG system not initialized. Please run ingestion first.'}), 500
        
#         # --- CLASSIFY AND HANDLE THE QUERY --- #
#         intent, immediate_response = classify_and_handle_query(query)
        
#         if intent == QueryIntent.DRUG_RELATED:
#             # Only drug-related queries go through the full RAG flow
#             response_text = rag_system.query(query)
#         else:
#             # Use the response already generated by the LLM for greeting/irrelevant
#             response_text = immediate_response
#         # --- END OF CLASSIFICATION CODE --- #

#         return jsonify({
#             'response': response_text,
#             'query': query,
#             'detected_intent': intent.value,
#             'success': True
#         })
        
#     except Exception as e:
#         return jsonify({
#             'error': f'Error processing query: {str(e)}',
#             'success': False
#         }), 500

# @app.route('/api/database-info', methods=['GET'])
# def get_database_info():
#     """Get database information"""
#     try:
#         if not rag_system:
#             initialized = initialize_rag_system()
#             if not initialized:
#                 return jsonify({'error': 'RAG system not initialized'}), 400
        
#         pdfs_in_db = rag_system.vector_db.list_all_documents()
        
#         return jsonify({
#             'document_count': rag_system.vector_db.get_document_count(),
#             'pdfs_in_database': pdfs_in_db,
#             'initialized': rag_system.vector_db.is_initialized()
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
# @app.route('/api/upload-and-query', methods=['POST'])
# def upload_and_query():
#     """Endpoint for uploading a PDF and asking a question about it"""
#     try:
#         # Check if the post request has the file part
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file part'}), 400
        
#         file = request.files['file']
#         query = request.form.get('query', '').strip()
        
#         # If user does not select file, browser might submit an empty part
#         if file.filename == '':
#             return jsonify({'error': 'No selected file'}), 400
        
#         if not query:
#             return jsonify({'error': 'No query provided'}), 400
        
#         if file and pdf_handler.allowed_file(file.filename):
#             # Generate a unique session ID
#             session_id = str(uuid.uuid4())
            
#             # Secure the filename and save temporarily
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(pdf_handler.upload_folder, f"{session_id}_{filename}")
#             file.save(file_path)
            
#             # Process the PDF
#             success, doc_count, _ = pdf_handler.process_uploaded_pdf(file_path, session_id)
            
#             if not success or doc_count == 0:
#                 # Clean up the file
#                 if os.path.exists(file_path):
#                     os.remove(file_path)
#                 return jsonify({'error': 'Failed to process PDF. It might be corrupted or unreadable.'}), 400
            
#             # Query the PDF
#             response, query_success, sources = pdf_handler.query_uploaded_pdf(query, session_id)
            
#             # Clean up the file
#             if os.path.exists(file_path):
#                 os.remove(file_path)
            
#             # Format sources for response
#             formatted_sources = []
#             for source in sources:
#                 formatted_sources.append({
#                     'page': source.get('pdf_page_number', source.get('pdf_page_start', 'N/A')),
#                     'section': source.get('section', ''),
#                     'content_preview': source['chunk_text'][:100] + '...' if len(source['chunk_text']) > 100 else source['chunk_text']
#                 })
            
#             if query_success:
#                 return jsonify({
#                     'response': response,
#                     'session_id': session_id,
#                     'documents_processed': doc_count,
#                     'sources': formatted_sources,
#                     'success': True
#                 })
#             else:
#                 # Clean up session on error
#                 pdf_handler.cleanup_session(session_id)
#                 return jsonify({'error': response}), 500
        
#         return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
#     except Exception as e:
#         return jsonify({'error': f'Server error: {str(e)}'}), 500

# @app.route('/api/followup-query', methods=['POST'])
# def followup_query():
#     """Endpoint for asking follow-up questions about an uploaded PDF"""
#     try:
#         data = request.get_json()
#         query = data.get('query', '').strip()
#         session_id = data.get('session_id', '').strip()
        
#         if not query:
#             return jsonify({'error': 'No query provided'}), 400
        
#         if not session_id:
#             return jsonify({'error': 'No session ID provided'}), 400
        
#         # Check if session exists and has documents
#         try:
#             results = pdf_handler.temp_db.collection.get(where={"session_id": session_id})
#             if not results or not results["ids"]:
#                 return jsonify({'error': 'Session expired or not found. Please upload the PDF again.'}), 404
#         except:
#             return jsonify({'error': 'Session expired or not found. Please upload the PDF again.'}), 404
        
#         # Query the PDF
#         response, success, sources = pdf_handler.query_uploaded_pdf(query, session_id)
        
#         # Format sources for response
#         formatted_sources = []
#         for source in sources:
#             formatted_sources.append({
#                 'page': source.get('pdf_page_number', source.get('pdf_page_start', 'N/A')),
#                 'section': source.get('section', ''),
#                 'content_preview': source['chunk_text'][:100] + '...' if len(source['chunk_text']) > 100 else source['chunk_text']
#             })
        
#         if success:
#             return jsonify({
#                 'response': response,
#                 'session_id': session_id,
#                 'sources': formatted_sources,
#                 'success': True
#             })
#         else:
#             return jsonify({'error': response}), 500
        
#     except Exception as e:
#         return jsonify({'error': f'Server error: {str(e)}'}), 500

# @app.route('/api/cleanup-session', methods=['POST'])
# def cleanup_session():
#     """Endpoint to clean up a session manually"""
#     try:
#         data = request.get_json()
#         session_id = data.get('session_id', '').strip()
        
#         if not session_id:
#             return jsonify({'error': 'No session ID provided'}), 400
        
#         success = pdf_handler.cleanup_session(session_id)
        
#         if success:
#             return jsonify({'message': f'Session {session_id} cleaned up successfully', 'success': True})
#         else:
#             return jsonify({'error': f'Failed to clean up session {session_id}'}), 500
            
#     except Exception as e:
#         return jsonify({'error': f'Server error: {str(e)}'}), 500

# if __name__ == '__main__':
#     # Initialize RAG system on startup
#     print("Initializing RAG system...")
#     if initialize_rag_system():
#         print("RAG system initialized successfully")
#         print(f"Documents in database: {rag_system.vector_db.get_document_count()}")
#     else:
#         print("Warning: RAG system could not be initialized. Please run ingestion first.")
    
#     # Run Flask app
#     app.run(debug=True, host='0.0.0.0', port=5000)



# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from rag_orchestrator import RAGOrchestrator
# from dotenv import load_dotenv
# import google.generativeai as genai
# from enum import Enum
# import os

# load_dotenv()

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend communication

# # Initialize RAG system
# pdf_folder = "./pdf"
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# rag_system = None

# class QueryIntent(Enum):
#     DRUG_RELATED = "drug_related"  # Query is about drugs, medications, pharmacology
#     GREETING = "greeting"          # Hello, hi, etc.
#     IRRELEVANT = "irrelevant"      # Everything else

# def classify_and_handle_query(query: str):
#     """
#     Uses the Gemini API to classify the user's query intent and generate appropriate responses.
#     For greeting and irrelevant queries, the LLM itself generates the response.
#     """
#     # System prompt that handles both classification and response generation
#     classification_prompt = f"""
#     You are a strict pharmaceutical chatbot. Analyze the user's query and:

#     1. If this is a GREETING (hello, hi, hey, greetings, how are you): 
#        - Respond with: "GREETING_RESPONSE: [your friendly greeting here]"

#     2. If this is IRRELEVANT (anything not related to drugs, medicine, pharmaceuticals, health conditions, treatments):
#        - Respond with: "IRRELEVANT_RESPONSE: [your polite decline here]"

#     3. If this is DRUG-RELATED (anything about drugs, medications, side effects, interactions, dosage, pharmacology, medical conditions):
#        - Respond with only: "DRUG_RELATED_QUERY"

#     User Query: "{query}"

#     Your response:
#     """

#     try:
#         # Use a fast, cheap model for this task
#         genai.configure(api_key=gemini_api_key)
#         model = genai.GenerativeModel('gemini-1.5-flash')
#         response = model.generate_content(classification_prompt)
#         response_text = response.text.strip()

#         # Check the response type
#         if "DRUG_RELATED_QUERY" in response_text:
#             return QueryIntent.DRUG_RELATED, None
#         elif "GREETING_RESPONSE:" in response_text:
#             # Extract just the response part
#             greeting_response = response_text.split("GREETING_RESPONSE:", 1)[1].strip()
#             return QueryIntent.GREETING, greeting_response
#         elif "IRRELEVANT_RESPONSE:" in response_text:
#             # Extract just the response part
#             irrelevant_response = response_text.split("IRRELEVANT_RESPONSE:", 1)[1].strip()
#             return QueryIntent.IRRELEVANT, irrelevant_response
#         else:
#             # Fallback if the model doesn't follow instructions
#             print(f"Unexpected response format: {response_text}")
#             return QueryIntent.DRUG_RELATED, None

#     except Exception as e:
#         print(f"Error during intent classification: {e}. Defaulting to drug_related.")
#         return QueryIntent.DRUG_RELATED, None

# def initialize_rag_system():
#     """Initialize the RAG system"""
#     global rag_system
#     try:
#         rag_system = RAGOrchestrator(pdf_folder, gemini_api_key)
        
#         # Check if database has documents
#         if not rag_system.vector_db.is_initialized():
#             if not rag_system.vector_db.initialize(reset=False):
#                 return False
        
#         if rag_system.vector_db.get_document_count() == 0:
#             return False
            
#         return True
#     except Exception as e:
#         print(f"Error initializing RAG system: {e}")
#         return False

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'database_initialized': rag_system is not None and rag_system.vector_db.is_initialized(),
#         'document_count': rag_system.vector_db.get_document_count() if rag_system else 0
#     })

# @app.route('/api/query', methods=['POST'])
# def process_query():
#     """Process user query"""
#     try:
#         data = request.get_json()
#         query = data.get('query', '').strip()
        
#         if not query:
#             return jsonify({'error': 'Query is required'}), 400
        
#         if not rag_system:
#             initialized = initialize_rag_system()
#             if not initialized:
#                 return jsonify({'error': 'RAG system not initialized. Please run ingestion first.'}), 500
        
#         # --- CLASSIFY AND HANDLE THE QUERY --- #
#         intent, immediate_response = classify_and_handle_query(query)
        
#         if intent == QueryIntent.DRUG_RELATED:
#             # Only drug-related queries go through the full RAG flow
#             response_text = rag_system.query(query)
#         else:
#             # Use the response already generated by the LLM for greeting/irrelevant
#             response_text = immediate_response
#         # --- END OF CLASSIFICATION CODE --- #

#         return jsonify({
#             'response': response_text,
#             'query': query,
#             'detected_intent': intent.value,
#             'success': True
#         })
        
#     except Exception as e:
#         return jsonify({
#             'error': f'Error processing query: {str(e)}',
#             'success': False
#         }), 500

# @app.route('/api/database-info', methods=['GET'])
# def get_database_info():
#     """Get database information"""
#     try:
#         if not rag_system:
#             initialized = initialize_rag_system()
#             if not initialized:
#                 return jsonify({'error': 'RAG system not initialized'}), 400
        
#         pdfs_in_db = rag_system.vector_db.list_all_documents()
        
#         return jsonify({
#             'document_count': rag_system.vector_db.get_document_count(),
#             'pdfs_in_database': pdfs_in_db,
#             'initialized': rag_system.vector_db.is_initialized()
#         })
        
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     # Initialize RAG system on startup
#     print("Initializing RAG system...")
#     if initialize_rag_system():
#         print("RAG system initialized successfully")
#         print(f"Documents in database: {rag_system.vector_db.get_document_count()}")
#     else:
#         print("Warning: RAG system could not be initialized. Please run ingestion first.")
    
#     # Run Flask app
#     app.run(debug=True, host='0.0.0.0', port=5000)




from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_orchestrator import RAGOrchestrator
from dotenv import load_dotenv
import google.generativeai as genai
from enum import Enum
import os

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize RAG system
pdf_folder = "./pdf"
gemini_api_key = os.getenv("GEMINI_API_KEY")
rag_system = None

class QueryIntent(Enum):
    DRUG_RELATED = "drug_related"  # Query is about drugs, medications, pharmacology
    GREETING = "greeting"          # Hello, hi, etc.
    IRRELEVANT = "irrelevant"      # Everything else

def classify_and_handle_query(query: str):
    """
    Uses the Gemini API to classify the user's query intent and generate appropriate responses.
    For greeting and irrelevant queries, the LLM itself generates the response.
    """
    # System prompt that handles both classification and response generation
    classification_prompt = f"""
    You are a strict pharmaceutical chatbot. Analyze the user's query and:

    1. If this is a GREETING (hello, hi, hey, greetings, how are you): 
       - Respond with: "GREETING_RESPONSE: [your friendly greeting here]"

    2. If this is IRRELEVANT (anything not related to drugs, medicine, pharmaceuticals, health conditions, treatments):
       - Respond with: "IRRELEVANT_RESPONSE: [your polite decline here]"

    3. If this is DRUG-RELATED (anything about drugs, medications, side effects, interactions, dosage, pharmacology, medical conditions):
       - Respond with only: "DRUG_RELATED_QUERY"

    User Query: "{query}"

    Your response:
    """

    try:
        # Use a fast, cheap model for this task
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(classification_prompt)
        response_text = response.text.strip()

        # Check the response type
        if "DRUG_RELATED_QUERY" in response_text:
            return QueryIntent.DRUG_RELATED, None
        elif "GREETING_RESPONSE:" in response_text:
            # Extract just the response part
            greeting_response = response_text.split("GREETING_RESPONSE:", 1)[1].strip()
            return QueryIntent.GREETING, greeting_response
        elif "IRRELEVANT_RESPONSE:" in response_text:
            # Extract just the response part
            irrelevant_response = response_text.split("IRRELEVANT_RESPONSE:", 1)[1].strip()
            return QueryIntent.IRRELEVANT, irrelevant_response
        else:
            # Fallback if the model doesn't follow instructions
            print(f"Unexpected response format: {response_text}")
            return QueryIntent.DRUG_RELATED, None

    except Exception as e:
        print(f"Error during intent classification: {e}. Defaulting to drug_related.")
        return QueryIntent.DRUG_RELATED, None

def initialize_rag_system():
    """Initialize the RAG system"""
    global rag_system
    try:
        rag_system = RAGOrchestrator(pdf_folder, gemini_api_key)
        
        # Check if database has documents
        if not rag_system.vector_db.is_initialized():
            if not rag_system.vector_db.initialize(reset=False):
                return False
        
        if rag_system.vector_db.get_document_count() == 0:
            return False
            
        return True
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database_initialized': rag_system is not None and rag_system.vector_db.is_initialized(),
        'document_count': rag_system.vector_db.get_document_count() if rag_system else 0
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process user query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if not rag_system:
            initialized = initialize_rag_system()
            if not initialized:
                return jsonify({'error': 'RAG system not initialized. Please run ingestion first.'}), 500
        
        # --- CLASSIFY AND HANDLE THE QUERY --- #
        intent, immediate_response = classify_and_handle_query(query)
        
        if intent == QueryIntent.DRUG_RELATED:
            # Only drug-related queries go through the full RAG flow
            response_text = rag_system.query(query)
        else:
            # Use the response already generated by the LLM for greeting/irrelevant
            response_text = immediate_response
        # --- END OF CLASSIFICATION CODE --- #

        return jsonify({
            'response': response_text,
            'query': query,
            'detected_intent': intent.value,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error processing query: {str(e)}',
            'success': False
        }), 500

@app.route('/api/database-info', methods=['GET'])
def get_database_info():
    """Get database information"""
    try:
        if not rag_system:
            initialized = initialize_rag_system()
            if not initialized:
                return jsonify({'error': 'RAG system not initialized'}), 400
        
        pdfs_in_db = rag_system.vector_db.list_all_documents()
        
        return jsonify({
            'document_count': rag_system.vector_db.get_document_count(),
            'pdfs_in_database': pdfs_in_db,
            'initialized': rag_system.vector_db.is_initialized()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize RAG system on startup
    print("Initializing RAG system...")
    if initialize_rag_system():
        print("RAG system initialized successfully")
        print(f"Documents in database: {rag_system.vector_db.get_document_count()}")
    else:
        print("Warning: RAG system could not be initialized. Please run ingestion first.")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)