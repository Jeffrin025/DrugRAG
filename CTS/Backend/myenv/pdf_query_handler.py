import os
import uuid
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
from vector_db import EfficientVectorDB
import google.generativeai as genai

class PDFQueryHandler:
    def __init__(self, gemini_api_key, upload_folder="./temp_uploads", max_file_age_hours=24):
        self.gemini_api_key = gemini_api_key
        self.upload_folder = upload_folder
        self.max_file_age_hours = max_file_age_hours
        self.pdf_processor = PDFProcessor()
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Initialize temporary vector DB for uploaded PDFs
        self.temp_db = EfficientVectorDB(persist_directory="./temp_chroma_db")
        self.temp_db.initialize(reset=False)
        
        # Initialize Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Clean up old files on initialization
        self.cleanup_old_files()

    def cleanup_old_files(self):
        """Remove files older than max_file_age_hours"""
        current_time = datetime.now()
        for filename in os.listdir(self.upload_folder):
            file_path = os.path.join(self.upload_folder, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_time > timedelta(hours=self.max_file_age_hours):
                    os.remove(file_path)
                    print(f"Removed old file: {filename}")

    def allowed_file(self, filename):
        """Check if the file has an allowed extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

    def process_uploaded_pdf(self, pdf_path, session_id):
        """Process an uploaded PDF and add to temporary database"""
        try:
            # Process the PDF
            documents = self.pdf_processor.process_pdf_for_db(pdf_path, pdf_index=0)
            
            # Add session metadata to all documents
            for doc in documents:
                doc['metadata']['session_id'] = session_id
                doc['metadata']['upload_time'] = datetime.now().isoformat()
                doc['metadata']['filename'] = os.path.basename(pdf_path)
            
            # Add to temporary vector DB
            success = self.temp_db.add_documents_batch(documents)
            
            # Count documents for this session
            session_doc_count = sum(1 for doc in documents if doc['metadata'].get('session_id') == session_id)
            
            return success, session_doc_count, documents
        except Exception as e:
            print(f"Error processing uploaded PDF: {e}")
            return False, 0, []

    def format_retrieved_info_with_citations(self, retrieved_chunks):
        """Format retrieved information with proper citations using PDF page numbers"""
        if not retrieved_chunks:
            return "No relevant information found in the document."
        
        formatted_info = "DOCUMENT CONTEXT WITH CITATIONS:\n\n"
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            # Use PDF page number for citation
            page_num = chunk.get('pdf_page_number', chunk.get('pdf_page_start', chunk.get('page_start', 'N/A')))
            
            citation = f"[Source: {chunk.get('filename', 'Document')}, Page {page_num}"
            
            # Add section info if available
            if chunk.get('section') and chunk['section'] not in ["TABULAR_DATA", "TABULAR_DATA_ROW"]:
                citation += f", Section: {chunk['section']}"
            
            # Add table context if available
            if chunk.get('doc_type') in ['table', 'table_row']:
                if chunk.get('table_index'):
                    citation += f", Table {chunk['table_index']}"
                if chunk.get('row_index') is not None:
                    citation += f", Row {chunk['row_index'] + 1}"
            
            citation += "]"
            
            formatted_info += f"{citation}\n{chunk['chunk_text']}\n\n"
        
        return formatted_info

    def query_uploaded_pdf(self, query_text, session_id, n_results=5):
        """Query the temporary database for a specific session with proper citations"""
        try:
            # Create session filter
            where_filter = {"session_id": session_id}
            
            # Query the temporary database
            results = self.temp_db.collection.query(
                query_texts=[query_text],
                n_results=n_results * 3,
                where=where_filter
            )
            
            # Process results
            processed_results = self.temp_db._process_query_results(results, n_results)
            
            # Format the retrieved information with citations
            formatted_info = self.format_retrieved_info_with_citations(processed_results)
            
            # Generate response with citations included
            prompt = f"""
            You are a helpful assistant that answers questions based on the provided document content.
            
            USER QUESTION: {query_text}
            
            DOCUMENT CONTEXT WITH CITATIONS:
            {formatted_info}
            
            INSTRUCTIONS:
            1. Answer the question using ONLY the information provided in the document context above.
            2. Be precise and factual in your response.
            3. Include proper citations in your answer by referencing the page numbers from the source material.
            4. If the information comes from a specific table or section, mention that in your citation.
            5. If you cannot find the answer in the provided context, say so clearly.
            6. Format your response in a clear, professional manner.
            
            RESPONSE:
            """
            
            response = self.model.generate_content(prompt)
            return response.text, True, processed_results
            
        except Exception as e:
            print(f"Error querying uploaded PDF: {e}")
            return f"Error processing your query: {str(e)}", False, []

    def cleanup_session(self, session_id):
        """Remove all documents for a specific session"""
        try:
            # Get all documents for this session
            results = self.temp_db.collection.get(where={"session_id": session_id})
            
            if results and results["ids"]:
                # Delete documents from collection
                self.temp_db.collection.delete(ids=results["ids"])
                print(f"Removed {len(results['ids'])} documents for session {session_id}")
            
            return True
        except Exception as e:
            print(f"Error cleaning up session {session_id}: {e}")
            return False

# Create a singleton instance
pdf_handler = None

def init_pdf_query_handler(gemini_api_key):
    global pdf_handler
    pdf_handler = PDFQueryHandler(gemini_api_key)