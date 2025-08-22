import google.generativeai as genai
from typing import List, Dict, Any
import re

class QueryProcessor:
    """Process queries and generate responses with proper citations"""
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze the query to determine optimal retrieval strategy"""
        query_lower = query.lower()
        
        # Drug-specific queries
        drug_keywords = {
            'orencia': 'orencia', 
            'simponi': 'simponi', 
            'aria': 'aria',
            'humira': 'humira', 
            'enbrel': 'enbrel', 
            'remicade': 'remicade', 
            'keytruda': 'keytruda'
        }
        
        mentioned_drugs = []
        pdf_filter = None
        
        for drug, filter_term in drug_keywords.items():
            if drug in query_lower:
                mentioned_drugs.append(drug)
                pdf_filter = filter_term  # Use the most specific match
        
        # Medical content queries
        medical_keywords = {
            'dose', 'dosage', 'side effect', 'adverse', 'warning', 
            'contraindication', 'interaction', 'administration', 'treatment',
            'safety', 'efficacy', 'pharmacokinetics', 'indication'
        }
        is_medical_query = any(keyword in query_lower for keyword in medical_keywords)
        
        return {
            "mentioned_drugs": mentioned_drugs,
            "is_medical_query": is_medical_query,
            "is_fda_specific": is_medical_query,
            "pdf_filter": pdf_filter,
            "prefer_medical": is_medical_query
        }
    
    def format_retrieved_info(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved information using PDF page numbers for citations"""
        if not retrieved_chunks:
            return "No relevant information found in the documents."
        
        formatted_info = ""
        for i, chunk in enumerate(retrieved_chunks, 1):
            # Use PDF page number for citation (preferred over detected page number)
            page_num = chunk.get('pdf_page_number', chunk.get('pdf_page_start', chunk.get('page_start', 1)))
            
            citation_parts = [f"Source: [PDF: {chunk['pdf_name']}"]
            
            if chunk.get('section') and chunk['section'] not in ["TABULAR_DATA", "TABULAR_DATA_ROW"]:
                citation_parts.append(f"Section: {chunk['section']}")
            
            citation_parts.append(f"Page: {page_num}")
            
            # Add table context if available
            if chunk.get('doc_type') in ['table', 'table_row']:
                if chunk.get('table_index'):
                    citation_parts.append(f"Table: {chunk['table_index']}")
                if chunk.get('row_index') is not None:
                    citation_parts.append(f"Row: {chunk['row_index'] + 1}")
            
            citation = ", ".join(citation_parts) + "]"
            
            formatted_info += f"{i}. {citation}\n{chunk['chunk_text']}\n\n"
        
        return formatted_info
        
    def generate_response(self, user_query: str, retrieved_info: str) -> str:
        """Generate natural, conversational response using Gemini with proper source consolidation"""
        prompt = f"""
    You are a medical information specialist providing answers about FDA-approved medications. Your task is to answer the user's question based EXCLUSIVELY on the provided retrieved information from official FDA drug labels.

    USER QUESTION: {user_query}

    RETRIEVED INFORMATION WITH SOURCE CITATIONS:
    {retrieved_info}

    CRITICAL INSTRUCTIONS:
    1.  **Answer using ONLY the information provided above - DO NOT use any external knowledge.**
    2.  **Natural Conversation:** Write your response as if you're having a natural conversation with the user. Do not use formal headings like "SUMMARY:" or "SOURCES:".
    3.  **Clear Organization:** Present the information in a well-structured, easy-to-read format using natural paragraphs and bullet points when appropriate.
    4.  **Source Integration:** Naturally incorporate the source information into your response. At the end, mention "This information comes from:" followed by the consolidated sources.
    5.  **CONSOLIDATE SOURCES:** If the same source (same PDF, same Section, same Page) is mentioned multiple times, list it ONLY ONCE.
    6.  **PAGE ACCURACY:** Ensure page numbers in sources match exactly what was provided in the retrieved information.

    Write your response in a friendly, professional tone as if you're explaining this to someone directly.

    RESPONSE:
    """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean up the response to ensure natural formatting
            response_text = response.text
            
            # Remove any residual markdown formatting that might appear
            response_text = response_text.replace("**", "").replace("__", "")
            
            # Ensure the response ends with proper source attribution
            if "This information comes from:" not in response_text and "Source:" not in response_text:
                # Extract and add sources if not already included
                sources_section = "\n\nThis information comes from the official prescribing information."
                response_text += sources_section
            
            return response_text
            
        except Exception as e:
            return f"I apologize, but I encountered an error while generating the response. Please try again later."