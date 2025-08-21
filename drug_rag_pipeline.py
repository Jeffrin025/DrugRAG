import os
import re
from typing import List, Dict, Any
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pdf_preprocessor import PDFProcessor

class DrugRAGPipeline:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.processor = PDFProcessor()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.persist_directory = persist_directory
        self.vectorstore = None
        
        # Initialize text splitter with medical-aware chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
            length_function=len,
        )
    
    def process_pdf_folder(self, input_folder: str) -> List[Document]:
        """Process all PDFs in a folder and return LangChain Documents"""
        all_documents = []
        
        pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_folder, pdf_file)
            print(f"Processing: {pdf_file}")
            
            try:
                # Extract text from PDF
                text = self.processor.extract_text_from_pdf(pdf_path)
                
                if text.startswith("Error"):
                    print(f"Skipping {pdf_file}: {text}")
                    continue
                
                # Extract sections
                sections = self.processor.extract_sections(text)
                
                # Create LangChain documents with metadata
                for section in sections:
                    # Split section content into chunks
                    chunks = self.text_splitter.split_text(section['content'])
                    
                    for chunk_index, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": pdf_file,
                                "section": section['section'],
                                "page_start": section['page_start'],
                                "page_end": section['page_end'],
                                "is_fda": section.get('is_fda', False),
                                "chunk_index": chunk_index,
                                "total_chunks": len(chunks),
                                "content_type": self.processor._classify_content_type(chunk)
                            }
                        )
                        all_documents.append(doc)
                
                print(f"✓ Processed {pdf_file}: {len(sections)} sections")
                
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
        
        return all_documents
    
    def create_vector_store(self, documents: List[Document]):
        """Create ChromaDB vector store from documents"""
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vectorstore.persist()
        print(f"✓ Vector store created with {len(documents)} documents")
    
    def load_vector_store(self):
        """Load existing vector store"""
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        print("✓ Vector store loaded")
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents"""
        if self.vectorstore is None:
            self.load_vector_store()
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def search_with_metadata(self, query: str, k: int = 5, **metadata_filters) -> List[Document]:
        """Search with metadata filtering"""
        if self.vectorstore is None:
            self.load_vector_store()
        
        # Build metadata filter
        filter_dict = {}
        for key, value in metadata_filters.items():
            if value is not None:
                filter_dict[key] = value
        
        results = self.vectorstore.similarity_search(
            query, 
            k=k, 
            filter=filter_dict if filter_dict else None
        )
        return results

def main():
    """Main function to run the DrugRAG pipeline"""
    
    # Initialize pipeline
    pipeline = DrugRAGPipeline()
    
    # Set paths
    input_folder = "./pdf_input"
    output_folder = "./processed_output"
    
    # Create folders if they don't exist
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    print("DrugRAG Pipeline Initialized")
    print("=" * 50)
    
    # Check for PDFs
    pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in pdf_input folder.")
        print("Please add some drug label PDFs and run again.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process PDFs and create vector store
    documents = pipeline.process_pdf_folder(input_folder)
    
    if documents:
        pipeline.create_vector_store(documents)
        
        # Test search functionality
        print("\nTesting search functionality...")
        test_queries = [
            "What are the side effects?",
            "Recommended dosage for adults",
            "Contraindications and warnings"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = pipeline.search_documents(query, k=3)
            for i, doc in enumerate(results):
                print(f"  Result {i+1}: {doc.metadata['section']} (Source: {doc.metadata['source']})")
                print(f"    Content: {doc.page_content[:100]}...")
    else:
        print("No documents were processed. Please check your PDF files.")

if __name__ == "__main__":
    main()