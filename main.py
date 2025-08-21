import os
import sys
from drug_rag_pipeline import DrugRAGPipeline
from query1_processor import DrugQueryProcessor

# Force set your API key manually
os.environ["GOOGLE_API_KEY"] = "YOUR_ACTUAL_GOOGLE_API_KEY_HERE"
print("GOOGLE_API_KEY:", os.environ.get("GOOGLE_API_KEY"))

# ---------------------------
# Load .env safely (handles UTF-8 BOM)
# ---------------------------
dotenv_path = "C:/project/cognizant/DrugRAG/.env"

if os.path.exists(dotenv_path):
    with open(dotenv_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key_name, value = line.split("=", 1)
            os.environ[key_name.strip()] = value.strip()

print("GOOGLE_API_KEY:", os.environ.get("GOOGLE_API_KEY"))

# ---------------------------
# Environment Setup
# ---------------------------
def setup_environment():
    print("🔧 Setting up DrugRAG environment...")

    # Create necessary directories
    os.makedirs("./pdf_input", exist_ok=True)
    os.makedirs("./processed_output", exist_ok=True)
    os.makedirs("./data", exist_ok=True)

    # Check for PDF files
    pdf_files = [f for f in os.listdir("./pdf_input") if f.endswith('.pdf')]
    return pdf_files

# ---------------------------
# Process PDFs and create vector database
# ---------------------------
def process_pdfs():
    print("\n📄 Processing PDF files...")
    
    pipeline = DrugRAGPipeline()
    pdf_files = [f for f in os.listdir("./pdf_input") if f.endswith('.pdf')]

    if not pdf_files:
        print("❌ No PDF files found in ./pdf_input/")
        print("Please add some drug label PDFs and try again.")
        return None

    print(f"Found {len(pdf_files)} PDF file(s) to process")

    documents = pipeline.process_pdf_folder("./pdf_input")

    if documents:
        pipeline.create_vector_store(documents)
        print(f"✅ Successfully processed {len(documents)} document chunks")
        return pipeline
    else:
        print("❌ Failed to process any documents")
        return None

# ---------------------------
# Initialize Gemini query processor
# ---------------------------
def initialize_query_processor():
    print("\n🤖 Initializing Gemini query processor...")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        return None

    try:
        processor = DrugQueryProcessor(google_api_key=api_key)
        print("✅ Gemini connected successfully!")
        return processor
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return None

# ---------------------------
# Interactive Query Mode
# ---------------------------
def interactive_query_mode(processor):
    print("\n" + "="*60)
    print("💊 DrugRAG Interactive Mode")
    print("="*60)
    print("\nYou can now ask questions about the drug information.")
    print("Type 'help' for commands, 'quit' to exit.")

    while True:
        try:
            question = input("\n💬 Your question: ").strip()
            if not question:
                continue
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            if question.lower() in ['help', '?']:
                print_help()
                continue
            if question.lower() in ['sources', 'documents']:
                list_available_documents()
                continue

            # Process the query
            result = processor.query_with_sources(question)

            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n💊 Answer: {result['answer']}")
                if result['sources']:
                    print(f"\n📚 Sources ({len(result['sources'])} found):")
                    for i, source in enumerate(result['sources'][:3]):
                        print(f"  {i+1}. {source['source_file']}")
                        print(f"     Section: {source['section']}")
                        print(f"     Pages: {source['pages']}")
                else:
                    print("\n📚 No sources found for this query")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

# ---------------------------
# Help & Document List
# ---------------------------
def print_help():
    print("\n📖 Available commands:")
    print("  - Ask any question about drug information")
    print("  - 'sources' - List available documents")
    print("  - 'help' - Show this help message")
    print("  - 'quit' - Exit program")

def list_available_documents():
    try:
        pipeline = DrugRAGPipeline()
        pipeline.load_vector_store()
        collection = pipeline.vectorstore._collection
        metadatas = collection.get(include=['metadatas'])['metadatas']

        unique_docs = {}
        for metadata in metadatas:
            if metadata:
                source = metadata.get('source', 'Unknown')
                unique_docs[source] = unique_docs.get(source, 0) + 1

        if unique_docs:
            print(f"\n📂 Available documents ({len(unique_docs)}):")
            for doc_name, chunk_count in unique_docs.items():
                print(f"  - {doc_name} ({chunk_count} chunks)")
        else:
            print("\n📂 No documents found in database")

    except Exception as e:
        print(f"❌ Error listing documents: {e}")

# ---------------------------
# Main Function
# ---------------------------
def main():
    print("="*60)
    print("💊 DrugRAG - Drug Information Retrieval System")
    print("="*60)

    pdf_files = setup_environment()
    vector_db_exists = os.path.exists("./data/chroma_db")

    if not vector_db_exists:
        if not pdf_files:
            print("❌ No PDF files found and no existing database.")
            return
        pipeline = process_pdfs()
        if not pipeline:
            return
    else:
        print("✅ Using existing vector database")

    processor = initialize_query_processor()
    if not processor:
        return

    interactive_query_mode(processor)

if __name__ == "__main__":
    main()
