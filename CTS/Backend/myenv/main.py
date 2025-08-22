from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_orchestrator import RAGOrchestrator
from dotenv import load_dotenv
import google.generativeai as genai
from enum import Enum
import os
import json

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize RAG system
pdf_folder = "./pdf"
gemini_api_key = os.getenv("GEMINI_API_KEY")
rag_system = None

# BERT model components
bert_model = None
bert_tokenizer = None
label_encoder = None
bert_available = False

class QueryIntent(Enum):
    DRUG_RELATED = "drug_related"  # Query is about drugs, medications, pharmacology
    GREETING = "greeting"          # Hello, hi, etc.
    IRRELEVANT = "irrelevant"      # Everything else

def load_bert_intent_classifier(model_path="models"):
    """
    Load BERT model and intent labels for classification
    """
    global bert_model, bert_tokenizer, label_encoder, bert_available
    
    try:
        if not os.path.exists(model_path):
            print(f"BERT model directory not found at {model_path}")
            return False
        
        # Check if model files exist (support both .safetensors and .bin formats)
        model_files = os.listdir(model_path)
        required_files = ['config.json', 'special_tokens_map.json', 'vocab.txt', 'label_mapping.json']
        
        # Check for either safetensors or pytorch model file
        has_safetensors = 'model.safetensors' in model_files
        has_pytorch_bin = 'pytorch_model.bin' in model_files
        
        if not (has_safetensors or has_pytorch_bin):
            print(f"Missing model weights file in {model_path}. Found: {model_files}")
            return False
        
        if not all(file in model_files for file in required_files):
            print(f"Missing required files in {model_path}. Found: {model_files}")
            return False
        
        # Import required libraries
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from sklearn.preprocessing import LabelEncoder
        import torch
        import numpy as np
        
        # Load model and tokenizer
        bert_model = AutoModelForSequenceClassification.from_pretrained(model_path)
        bert_tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load label mapping and create label encoder
        with open(f'{model_path}/label_mapping.json', 'r') as f:
            label_mapping = json.load(f)
        
        # Create label encoder from mapping
        label_encoder = LabelEncoder()
        classes = [label_mapping[str(i)] for i in range(len(label_mapping))]
        label_encoder.classes_ = np.array(classes)
        
        print("BERT intent classifier loaded successfully")
        print(f"Available intents: {list(label_encoder.classes_)}")
        bert_available = True
        return True
        
    except ImportError as e:
        print(f"Required libraries not available: {e}")
        return False
    except Exception as e:
        print(f"Error loading BERT model: {e}")
        return False

def classify_query_bert(query: str):
    """
    Classify query using BERT model
    """
    if not bert_available:
        raise Exception("BERT model not available")
    
    try:
        import torch
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        bert_model.to(device)
        
        # Tokenize
        encoding = bert_tokenizer(
            query,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)
        
        # Predict
        with torch.no_grad():
            outputs = bert_model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_idx = torch.argmax(predictions, dim=1).item()
            confidence = predictions[0][predicted_idx].item()
        
        # Map to intent
        intent_name = label_encoder.inverse_transform([predicted_idx])[0]
        
        return intent_name, confidence
        
    except Exception as e:
        raise Exception(f"BERT prediction error: {e}")

def classify_and_handle_query(query: str):
    """
    Uses BERT model if available, otherwise falls back to Gemini API
    """
    # First try BERT if available
    if bert_available:
        try:
            intent_name, confidence = classify_query_bert(query)
            print(f"Query: '{query}' -> BERT Intent: {intent_name} (confidence: {confidence:.3f})")
            
            # Map BERT intents to your QueryIntent enum
            if intent_name == "drug_medical":
                return QueryIntent.DRUG_RELATED, None
            elif intent_name == "greeting":
                greeting_response = "Hello! I'm a pharmaceutical assistant. How can I help you with drug-related questions today?"
                return QueryIntent.GREETING, greeting_response
            elif intent_name == "irrelevant":
                irrelevant_response = "I'm sorry, I'm specifically designed to answer questions about pharmaceuticals, drugs, and medications. Please ask me about drug-related topics."
                return QueryIntent.IRRELEVANT, irrelevant_response
            
        except Exception as e:
            print(f"BERT classification failed: {e}. Falling back to Gemini API.")
    
    # Fallback to Gemini API
    return classify_with_gemini(query)

def classify_with_gemini(query: str):
    """
    Use Gemini API for intent classification
    """
    print("Using Gemini API for intent classification...")
    
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
        print(f"Error during Gemini classification: {e}. Defaulting to drug_related.")
        return QueryIntent.DRUG_RELATED, None

def initialize_rag_system():
    """Initialize the RAG system and BERT classifier"""
    global rag_system
    
    # Try to load BERT classifier
    print("Attempting to load BERT intent classifier...")
    load_bert_intent_classifier()
    
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
        'document_count': rag_system.vector_db.get_document_count() if rag_system else 0,
        'bert_model_loaded': bert_available,
        'available_intents': list(label_encoder.classes_) if label_encoder else []
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
        
        # Classify and handle the query
        intent, immediate_response = classify_and_handle_query(query)
        
        if intent == QueryIntent.DRUG_RELATED:
            # Only drug-related queries go through the full RAG flow
            response_text = rag_system.query(query)
        else:
            # Use the response already generated for greeting/irrelevant
            response_text = immediate_response

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

@app.route('/api/bert-info', methods=['GET'])
def get_bert_info():
    """Get BERT model information"""
    try:
        return jsonify({
            'bert_loaded': bert_available,
            'available_intents': list(label_encoder.classes_) if label_encoder else [],
            'model_architecture': 'BERT' if bert_available else None,
            'model_directory': 'models' if bert_available else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize RAG system and BERT classifier on startup
    print("Initializing RAG system and BERT classifier...")
    if initialize_rag_system():
        print("RAG system initialized successfully")
        print(f"Documents in database: {rag_system.vector_db.get_document_count()}")
    else:
        print("Warning: RAG system could not be initialized. Please run ingestion first.")
    
    # Run Flask app with debug=False to avoid the socket error
    app.run(debug=False, host='0.0.0.0', port=5000)
