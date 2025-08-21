import os
from typing import List, Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from pdf_processor import PDFProcessor
from vector_db import EfficientVectorDB
from query_processor import QueryProcessor

class RAGState(TypedDict):
    pdf_directory: str
    pdf_files: List[str]
    processed_pdfs: List[Dict[str, Any]]
    current_pdf: Optional[Dict[str, Any]]
    query: str
    query_analysis: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    response: str
    db_initialized: bool
    ingestion_mode: bool

class RAGOrchestrator:
    """Main orchestrator for the RAG system using LangGraph"""
    
    def __init__(self, pdf_directory: str, gemini_api_key: str):
        self.pdf_directory = pdf_directory
        self.pdf_processor = PDFProcessor()
        self.vector_db = EfficientVectorDB()
        self.query_processor = QueryProcessor(gemini_api_key)
        self.workflow = self._create_workflow()
        self._ingestion_completed = False
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(RAGState)
        
        # Add nodes with correct method names
        workflow.add_node("initialize", self._initialize_system)
        workflow.add_node("process_pdf", self._process_next_pdf)
        workflow.add_node("add_to_db", self._add_to_database)
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("retrieve_info", self._retrieve_information)
        workflow.add_node("generate_response", self._generate_response)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges for PDF processing (only in ingestion mode)
        workflow.add_conditional_edges(
            "initialize",
            lambda state: "process_pdf" if state.get("ingestion_mode", False) else "analyze_query"
        )
        
        # Proper PDF processing loop
        workflow.add_edge("process_pdf", "add_to_db")
        workflow.add_conditional_edges(
            "add_to_db",
            lambda state: "process_pdf" if state["pdf_files"] else END
        )
        
        # Add edges for query processing
        workflow.add_edge("analyze_query", "retrieve_info")
        workflow.add_edge("retrieve_info", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _initialize_system(self, state: RAGState) -> dict:
        """Initialize the system"""
        if not os.path.exists(state["pdf_directory"]):
            raise ValueError(f"Directory {state['pdf_directory']} does not exist")
        
        pdf_files = [f for f in os.listdir(state["pdf_directory"]) if f.lower().endswith('.pdf')]
        
        # Only reset DB if we're doing ingestion (when ingestion_mode is True)
        reset_db = state["ingestion_mode"]
        db_initialized = self.vector_db.initialize(reset=reset_db)
        
        return {
            "pdf_files": pdf_files if state["ingestion_mode"] else [],
            "processed_pdfs": [],
            "db_initialized": db_initialized
        }
    
    def _process_next_pdf(self, state: RAGState) -> dict:
        """Process next PDF (only in ingestion mode)"""
        if not state["pdf_files"]:
            return {"pdf_files": [], "current_pdf": None}
        
        pdf_file = state["pdf_files"][0]
        pdf_path = os.path.join(state["pdf_directory"], pdf_file)
        pdf_index = len(state["processed_pdfs"])
        
        print(f"Processing {pdf_file} ({len(state['processed_pdfs']) + 1}/{len(state['pdf_files']) + len(state['processed_pdfs'])})...")
        
        # Extract and process text
        text = self.pdf_processor.extract_text_from_pdf(pdf_path)
        if not text.strip() or "Error extracting" in text:
            print(f"Warning: Could not process {pdf_file}")
            return {"pdf_files": state["pdf_files"][1:], "current_pdf": None}
        
        sections = self.pdf_processor.extract_sections(text)
        if not sections:
            print(f"Warning: No sections found in {pdf_file}")
            return {"pdf_files": state["pdf_files"][1:], "current_pdf": None}
        
        # Chunk sections
        for section in sections:
            section["chunks"] = self.pdf_processor.chunk_content(section["content"])
        
        current_pdf = {
            "name": pdf_file,
            "index": pdf_index,
            "sections": sections
        }
        
        return {
            "current_pdf": current_pdf,
            "pdf_files": state["pdf_files"][1:]
        }
    
    def _add_to_database(self, state: RAGState) -> dict:
        """Add PDF to database (only in ingestion mode)"""
        if not state["current_pdf"] or not state["db_initialized"]:
            return {"processed_pdfs": state["processed_pdfs"]}
        
        current_pdf = state["current_pdf"]
        documents_batch = self.pdf_processor.prepare_documents_for_db(
            current_pdf["name"], 
            current_pdf["index"], 
            current_pdf["sections"]
        )
        
        success = self.vector_db.add_documents_batch(documents_batch)
        
        if success:
            processed_pdfs = state["processed_pdfs"] + [current_pdf]
            print(f"Successfully processed {current_pdf['name']}")
            return {"processed_pdfs": processed_pdfs}
        else:
            print(f"Failed to add {current_pdf['name']} to database")
            return {"processed_pdfs": state["processed_pdfs"]}
    
    def _analyze_query(self, state: RAGState) -> dict:
        """Analyze user query"""
        return {"query_analysis": self.query_processor.analyze_query(state["query"])}
    
    def _retrieve_information(self, state: RAGState) -> dict:
        """Retrieve relevant information without filtering"""
        if not state["db_initialized"]:
            return {"retrieved_chunks": []}
        
        # Retrieve documents without any filtering
        retrieved_chunks = self.vector_db.query(
            state["query"],
            n_results=8  # Get more results for better context
        )
        
        # Return top results without additional filtering
        return {"retrieved_chunks": retrieved_chunks[:5]}
    
    def _generate_response(self, state: RAGState) -> dict:
        """Generate response"""
        retrieved_info = self.query_processor.format_retrieved_info(state["retrieved_chunks"])
        response = self.query_processor.generate_response(state["query"], retrieved_info)
        return {"response": response}
    
    def load_pdfs(self) -> dict:
        """Load all PDFs into the system (one-time ingestion)"""
        initial_state = {
            "pdf_directory": self.pdf_directory,
            "pdf_files": [],
            "processed_pdfs": [],
            "current_pdf": None,
            "query": "",
            "query_analysis": {},
            "retrieved_chunks": [],
            "response": "",
            "db_initialized": False,
            "ingestion_mode": True
        }
        
        result = self.workflow.invoke(initial_state)
        self._ingestion_completed = True
        print(f"Processing complete. Processed {len(result['processed_pdfs'])} PDF files")
        print(f"Total documents in database: {self.vector_db.get_document_count()}")
        return result
    
    def query(self, user_query: str) -> str:
        """Execute a query against the loaded documents (querying only)"""
        # Check if database has documents
        if not self.vector_db.is_initialized():
            # Try to connect to existing database
            if not self.vector_db.initialize(reset=False):
                return "Database not initialized. Please run ingestion first."
        
        if self.vector_db.get_document_count() == 0:
            return "No documents found in database. Please run ingestion first."
        
        query_state = {
            "pdf_directory": self.pdf_directory,
            "pdf_files": [],
            "processed_pdfs": [],
            "current_pdf": None,
            "query": user_query,
            "query_analysis": {},
            "retrieved_chunks": [],
            "response": "",
            "db_initialized": True,
            "ingestion_mode": False
        }
        
        result = self.workflow.invoke(query_state)
        return result["response"]