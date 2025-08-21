import os
from drug_rag_pipeline import DrugRAGPipeline
from query_processor import DrugQueryProcessor
from main import main

if __name__ == "__main__":
    main()

def setup_rag_system():
    """Set up the complete DrugRAG system"""
    
    print("🚀 Setting up DrugRAG System with Gemini")
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

def get_gemini_api_key():
    """Get Gemini API key from environment or user input"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n🔑 Gemini API Key required:")
        print("1. Get your API key from: https://aistudio.google.com/app/apikey")
        print("2. Set it as environment variable: GOOGLE_API_KEY")
        print("3. Or enter it when prompted")
        api_key = input("\nPlease enter your Google Gemini API key: ").strip()
    
    return api_key

def main():
    """Main function to run the complete DrugRAG system with Gemini"""
    
    # Get API key
    api_key = get_gemini_api_key()
    if not api_key:
        print("❌ API key is required to use Gemini")
        return
    
    # Set up the system
    pipeline = setup_rag_system()
    if not pipeline:
        return
    
    # Initialize query processor
    print("\nInitializing Gemini query processor...")
    try:
        query_processor = DrugQueryProcessor(google_api_key=api_key)
        print("✅ Gemini connected successfully!")
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return
    
    print("\n✅ DrugRAG System Ready with Gemini!")
    print("\nYou can now query the system. Example queries:")
    print("  - 'What are the side effects of this drug?'")
    print("  - 'What is the recommended dosage for elderly patients?'")
    print("  - 'Are there any drug interactions with aspirin?'")
    print("  - 'What are the contraindications?'")
    print("\nType 'quit' to exit")
    
    # Interactive query loop
    while True:
        print("\n" + "=" * 60)
        question = input("\n💬 Enter your drug question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if question:
            try:
                result = query_processor.query_with_sources(question)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"\n💊 Answer: {result['answer']}")
                    
                    # Show sources
                    if result['sources']:
                        print(f"\n📚 Sources:")
                        for i, source in enumerate(result['sources'][:3]):
                            print(f"  {i+1}. {source['source_file']}")
                            print(f"     Section: {source['section']}")
                            print(f"     Pages: {source['pages']}")
                            print(f"     Preview: {source['content_preview']}")
                    else:
                        print("\n📚 No specific sources found")
                        
            except Exception as e:
                print(f"❌ Error processing query: {e}")

if __name__ == "__main__":
    main()