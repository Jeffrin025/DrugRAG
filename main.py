from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_orchestrator import RAGOrchestrator
from dotenv import load_dotenv
import google.generativeai as genai
from enum import Enum
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize RAG system
pdf_folder = "./pdf"
gemini_api_key = os.getenv("GEMINI_API_KEY")
rag_system = None

# Conversation memory storage
conversation_memory = {}

class Conversation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.current_topic = None  # Track the current drug/topic
    
    def update_topic(self, query: str):
        """Detect and update the current topic based on query"""
        query_lower = query.lower()
        
        # Drug-specific keywords
        drug_keywords = {
            'orencia': 'orencia', 
            'simponi': 'simponi', 
            'aria': 'aria',
            'humira': 'humira', 
            'enbrel': 'enbrel', 
            'remicade': 'remicade', 
            'keytruda': 'keytruda'
        }
        
        # Check if a new drug is mentioned
        new_topic = None
        for drug, keyword in drug_keywords.items():
            if keyword in query_lower:
                new_topic = drug
                break
        
        # Update topic if changed
        if new_topic and new_topic != self.current_topic:
            self.current_topic = new_topic
            print(f"Topic changed to: {new_topic}")
        
        return self.current_topic
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        message = {
            "role": role, 
            "content": content, 
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.last_accessed = datetime.now()
        
        # Keep only last 15 messages to manage context length
        if len(self.messages) > 15:
            self.messages = self.messages[-15:]
    
    def get_conversation_context(self, last_n: int = 4):
        """Get formatted conversation context for LLM"""
        context_messages = self.messages[-last_n:] if last_n > 0 else self.messages
        
        # Add topic context
        context = f"Current topic: {self.current_topic or 'General'}\n\n"
        context += "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in context_messages 
            if msg['role'] in ['User', 'Assistant']
        ])
        
        return context
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "message_count": len(self.messages),
            "current_topic": self.current_topic
        }

def get_or_create_conversation(session_id):
    if session_id not in conversation_memory:
        conversation_memory[session_id] = Conversation(session_id)
    
    # Clean up old conversations (older than 24 hours)
    cleanup_old_conversations()
    
    return conversation_memory[session_id]

def cleanup_old_conversations():
    now = datetime.now()
    expired_sessions = []
    for session_id, conv in conversation_memory.items():
        if now - conv.last_accessed > timedelta(hours=24):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_memory[session_id]

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
    """Process user query with enhanced topic tracking"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        session_id = data.get('session_id')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Generate new session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"Generated new session ID: {session_id}")
        
        if not rag_system:
            initialized = initialize_rag_system()
            if not initialized:
                return jsonify({'error': 'RAG system not initialized. Please run ingestion first.'}), 500
        
        # Get or create conversation with the specific session_id
        conversation = get_or_create_conversation(session_id)
        
        # Update topic based on current query
        current_topic = conversation.update_topic(query)
        
        # Add user message to conversation with metadata
        conversation.add_message("User", query, {
            "query_type": "user_input",
            "topic": current_topic,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get conversation context for RAG with topic information
        conversation_context = conversation.get_conversation_context(last_n=4)
        
        # Classify and handle the query
        intent, immediate_response = classify_and_handle_query(query)
        
        if intent == QueryIntent.DRUG_RELATED:
            # Enhance query with topic context for better retrieval
            enhanced_query = f"{current_topic.upper() if current_topic else ''} {query}"
            
            # Pass enhanced query and conversation context to RAG system
            response_text = rag_system.query(enhanced_query, conversation_context)
        else:
            response_text = immediate_response
        
        # Add assistant response to conversation
        conversation.add_message("Assistant", response_text, {
            "response_type": "rag_response" if intent == QueryIntent.DRUG_RELATED else "general_response",
            "intent": intent.value,
            "topic": current_topic,
            "timestamp": datetime.now().isoformat()
        })
        
        # Prepare response with session information
        response_data = {
            'response': response_text,
            'query': query,
            'detected_intent': intent.value,
            'current_topic': current_topic,
            'session_id': session_id,
            'message_count': len(conversation.messages),
            'success': True,
            'session_info': {
                'created_at': conversation.created_at.isoformat(),
                'last_accessed': conversation.last_accessed.isoformat()
            }
        }
        
        return jsonify(response_data)
        
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

@app.route('/api/conversation-history', methods=['GET'])
def get_conversation_history():
    """Get conversation history for a session"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'session_id parameter is required'}), 400
        
        if session_id in conversation_memory:
            conversation = conversation_memory[session_id]
            return jsonify({
                'session_id': session_id,
                'messages': conversation.messages,
                'created_at': conversation.created_at.isoformat(),
                'last_accessed': conversation.last_accessed.isoformat(),
                'current_topic': conversation.current_topic
            })
        else:
            return jsonify({
                'session_id': session_id,
                'messages': [],
                'error': 'Session not found'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """Get list of all active sessions"""
    try:
        sessions = []
        for session_id, conv in conversation_memory.items():
            sessions.append({
                "session_id": session_id,
                "created_at": conv.created_at.isoformat(),
                "last_accessed": conv.last_accessed.isoformat(),
                "message_count": len(conv.messages),
                "current_topic": conv.current_topic
            })
        
        return jsonify({"sessions": sessions, "total": len(sessions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a specific session"""
    try:
        if session_id in conversation_memory:
            del conversation_memory[session_id]
            return jsonify({'success': True, 'message': f'Session {session_id} deleted'})
        else:
            return jsonify({'error': 'Session not found'}), 404
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