from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from drug_rag_pipeline import DrugRAGPipeline
import os

class DrugQueryProcessor:
    def __init__(self, google_api_key: str = None):
        # Load your vector store
        self.pipeline = DrugRAGPipeline()
        self.pipeline.load_vector_store()
        
        # API key
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass it as argument.")
        
        # Set up Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-pro",  # Updated to a valid model
            temperature=0.1,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
        
        # Prompt template
        prompt_text = """You are a medical assistant specializing in drug information.
Use the following context from drug labels to answer the question accurately and safely.

CONTEXT:
{context}

QUESTION:
{question}

GUIDELINES:
1. Answer based ONLY on the provided context.
2. If info not in context, say "I don't have enough info from drug labels to answer."
3. Include source section/document name when possible.
4. Prioritize safety info.

MEDICAL RESPONSE:"""

        self.prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["context", "question"]
        )
        
        # Set up RetrievalQA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.pipeline.vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": self.prompt},
            return_source_documents=True
        )

    def query(self, question: str, **metadata_filters) -> dict:
        """Process a drug-related query"""
        try:
            # Apply filters if provided
            if metadata_filters:
                self.qa_chain.retriever = self.pipeline.vectorstore.as_retriever(
                    search_kwargs={"k": 5, "filter": metadata_filters}
                )
            
            result = self.qa_chain({"query": question})
            return result
        except Exception as e:
            return {"error": str(e), "result": "Unable to process query"}

    def simple_query(self, question: str) -> str:
        result = self.query(question)
        if "error" in result:
            return f"Error: {result['error']}"
        return result["result"]

    def query_with_sources(self, question: str) -> dict:
        """Query with source details"""
        result = self.query(question)
        if "error" in result:
            return result

        sources = []
        for doc in result.get('source_documents', []):
            sources.append({
                "source_file": doc.metadata.get('source', 'Unknown'),
                "section": doc.metadata.get('section', 'Unknown'),
                "pages": f"{doc.metadata.get('page_start', '?')}-{doc.metadata.get('page_end', '?')}",
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })

        return {"answer": result["result"], "sources": sources}

# Test function
if __name__ == "__main__":
    api_key = os.getenv("GOOGLE_API_KEY")
    processor = DrugQueryProcessor(google_api_key=api_key)
    q = "What are the side effects of Herceptin?"
    res = processor.query_with_sources(q)
    print(res)
