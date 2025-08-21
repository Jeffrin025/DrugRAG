import os
from drug_rag_pipeline import DrugRAGPipeline
from query_processor import DrugQueryProcessor

def setup_rag_system():
    """Set up the complete DrugRAG system"""
    
    print("🚀 Setting up DrugRAG System")
    print("=" * 60)
    
    # Initialize and process PDFs
    pipeline = DrugRAGPipeline()
    
    # Process PDFs if vector store doesn't exist
    if not os.path.exists("./data/chroma_db"):
        print("Processing PDF files...")
        documents = pipeline.process_pdf_folder("./pdf_input")
        if documents:
            pipeline.create_vector_store(documents)
            print(f"✅ Processed {len(documents)} document chunks")
        else:
            print("❌ No documents processed. Please add PDF files to pdf_input folder.")
            return None
    else:
        print("✅ Using existing vector database")
        pipeline.load_vector_store()
    
    return pipeline

def main():
    """Main function to run the complete DrugRAG system"""
    
    # Set up the system
    pipeline = setup_rag_system()
    if not pipeline:
        return
    
    # Initialize query processor
    print("\nInitializing query processor...")
    query_processor = DrugQueryProcessor()
    
    print("\n✅ DrugRAG System Ready!")
    print("\nYou can now query the system. Example queries:")
    print("  - 'What are the side effects of this drug?'")
    print("  - 'What is the recommended dosage?'")
    print("  - 'Are there any contraindications?'")
    
    # Interactive query loop
    while True:
        print("\n" + "=" * 50)
        question = input("\nEnter your question (or 'quit' to exit): ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if question:
            try:
                result = query_processor.query(question)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"\n🤖 Answer: {result['result']}")
                    
                    # Show sources
                    print(f"\n📚 Sources:")
                    for i, doc in enumerate(result['source_documents'][:3]):
                        print(f"  {i+1}. {doc.metadata['section']} - {doc.metadata['source']}")
                        
            except Exception as e:
                print(f"❌ Error processing query: {e}")

if __name__ == "__main__":
    main()