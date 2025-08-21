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
        """Format retrieved information with detailed citations"""
        if not retrieved_chunks:
            return "No relevant information found in the documents."
        
        formatted_info = ""
        for i, chunk in enumerate(retrieved_chunks, 1):
            citation = f"Source: [PDF: {chunk['pdf_name']}"
            if chunk.get('section'):
                citation += f", Section: {chunk['section']}"
            if chunk.get('page_start') and chunk.get('page_end'):
                citation += f", Pages {chunk['page_start']}-{chunk['page_end']}"
            citation += "]"
            
            formatted_info += f"{i}. {citation}\n{chunk['chunk_text']}\n\n"
        
        return formatted_info
    
    def generate_response(self, user_query: str, retrieved_info: str) -> str:
        """Generate response using Gemini with proper citation enforcement"""
        prompt = f"""
You are a medical information specialist. Based EXCLUSIVELY on the following retrieved information from FDA drug labels and medical documents, please provide a comprehensive answer to the user's question.

USER QUESTION: {user_query}

RETRIEVED INFORMATION WITH SOURCE CITATIONS:
{retrieved_info}

CRITICAL INSTRUCTIONS:
1. Answer using ONLY the information provided above - DO NOT use any external knowledge
2. Be specific, precise, and medically accurate
3. You MUST include the exact source citations in your response for every piece of information
4. Use this citation format: "Source: [PDF: filename, Section: section_name, Pages X-X]"
5. If multiple sources provide the same information, cite all relevant sources
6. If the information cannot be found in the retrieved content, clearly state: "Not found in prescribing information."
7. Keep the response concise but comprehensive
8. For dosage information, always include specific amounts and administration details
9. For side effects, list the most common and serious ones with frequencies if available

IMPORTANT: Your response MUST include proper source citations for every factual statement.

ANSWER:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:

            return f"Error generating response: {str(e)}"
