from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from drug_rag_pipeline import DrugRAGPipeline
import os

class DrugQueryProcessor:
    def __init__(self, openai_api_key: str = None):
        self.pipeline = DrugRAGPipeline()
        self.pipeline.load_vector_store()
        
        # Set up LLM (you can use other models too)
        self.llm = OpenAI(
            temperature=0.1,
            openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo-instruct"
        )
        
        # Custom prompt for drug information
        self.prompt_template = """You are a medical assistant specializing in drug information. 
        Use the following context from drug labels to answer the question accurately and safely.

        Context: {context}

        Question: {question}

        Guidelines:
        1. Answer based ONLY on the provided context
        2. If you don't know the answer, say you don't know
        3. Be precise about dosages, warnings, and side effects
        4. Include the source section and document name when possible

        Answer:"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        # Set up retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.pipeline.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            ),
            chain_type_kwargs={"prompt": self.prompt},
            return_source_documents=True
        )
    
    def query(self, question: str, **metadata_filters) -> dict:
        """Process a drug-related query"""
        try:
            # Prepare filters
            filter_dict = {}
            for key, value in metadata_filters.items():
                if value is not None:
                    filter_dict[key] = value
            
            # Update retriever with filters if provided
            if filter_dict:
                self.qa_chain.retriever = self.pipeline.vectorstore.as_retriever(
                    search_kwargs={"k": 5, "filter": filter_dict}
                )
            
            result = self.qa_chain({"query": question})
            return result
            
        except Exception as e:
            return {"error": str(e), "result": "Unable to process query"}
    
    def simple_query(self, question: str) -> str:
        """Simple query interface"""
        result = self.query(question)
        if "error" in result:
            return f"Error: {result['error']}"
        
        return result["result"]

# Simple test function
def test_query_processor():
    """Test the query processor"""
    processor = DrugQueryProcessor()
    
    test_questions = [
        "What are the common side effects?",
        "What is the recommended dosage?",
        "Are there any drug interactions I should know about?"
    ]
    
    print("Testing Query Processor")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        answer = processor.simple_query(question)
        print(f"Answer: {answer}")
        print("-" * 50)

if __name__ == "__main__":
    test_query_processor()