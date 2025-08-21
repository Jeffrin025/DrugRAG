import os
import re
import PyPDF2
from typing import List, Dict, Any
import uuid

class PDFProcessor:
    """PDF processor that handles text extraction, section identification, and chunking"""
    
    def __init__(self):
        # FDA sections for better organization
        self.fda_sections = [
            "BOXED WARNING", "INDICATIONS AND USAGE", "DOSAGE AND ADMINISTRATION",
            "CONTRAINDICATIONS", "WARNINGS AND PRECAUTIONS", "ADVERSE REACTIONS",
            "DRUG INTERACTIONS", "USE IN SPECIFIC POPULATIONS", "PATIENT COUNSELING INFORMATION",
            "CLINICAL PHARMACOLOGY", "HOW SUPPLIED/STORAGE AND HANDLING", "MEDICATION GUIDE",
            "DESCRIPTION", "CLINICAL STUDIES", "MECHANISM OF ACTION", "PHARMACOKINETICS",
            "NONCLINICAL TOXICOLOGY", "CLINICAL TRIALS"
        ]
        
        self.fda_section_pattern = re.compile(
            r'^\s*(' + '|'.join(re.escape(section) for section in self.fda_sections) + r')\s*$',
            re.IGNORECASE | re.MULTILINE
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file with robust error handling"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                    else:
                        # Handle pages with images/scanned content
                        text += f"--- Page {page_num + 1} ---\n[Content not extractable - may contain images/scanned content]\n\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return f"Error extracting text from {pdf_path}: {str(e)}"
        return text
    
    def is_fda_format(self, text: str) -> bool:
        """Check if the document follows FDA format"""
        fda_section_count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
        return fda_section_count >= 3
    
    def extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract sections from document, preserving all content with robust parsing"""
        sections = []
        current_section = "INTRODUCTION"
        content = ""
        page_num = 1
        is_fda = self.is_fda_format(text)
        
        lines = text.split('\n')
        for line in lines:
            # Handle page breaks
            if line.startswith("--- Page "):
                if content.strip():
                    sections.append({
                        "section": current_section,
                        "content": content.strip(),
                        "page_start": page_num,
                        "page_end": page_num,
                        "is_fda": is_fda
                    })
                content = ""
                match = re.match(r'--- Page (\d+) ---', line)
                if match:
                    page_num = int(match.group(1))
                continue
            
            # Handle section headers based on document type
            section_match = None
            if is_fda:
                section_match = self.fda_section_pattern.match(line.upper())
            else:
                # Generic section detection for non-FDA documents
                section_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+(?:\.|:)?)\s*$', line) 
                               and len(line.strip()) < 100 
                               and not line.strip().isdigit())
            
            if section_match:
                if content.strip():
                    sections.append({
                        "section": current_section,
                        "content": content.strip(),
                        "page_start": page_num,
                        "page_end": page_num,
                        "is_fda": is_fda
                    })
                current_section = line.strip().upper()
                content = ""
            else:
                content += line + "\n"
        
        # Add the final section
        if content.strip():
            sections.append({
                "section": current_section,
                "content": content.strip(),
                "page_start": page_num,
                "page_end": page_num,
                "is_fda": is_fda
            })
        
        return sections
    
    def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
        """Create semantic chunks with overlap for better context preservation"""
        chunks = []
        words = content.split()
        
        # Handle very short content
        if len(words) <= chunk_size:
            return [{"content": content, "chunk_id": "chunk_0"}]
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            # Ensure we don't create empty chunks
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "chunk_id": f"chunk_{i//chunk_size}"
                })
        
        return chunks
    
    def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare documents for database insertion with proper metadata"""
        documents_batch = []
        
        for section in sections:
            # Ensure the section has chunks
            if "chunks" not in section:
                section["chunks"] = self.chunk_content(section["content"])
                
            for chunk in section["chunks"]:
                doc_id = str(uuid.uuid4())
                document = {
                    "id": doc_id,
                    "content": chunk["content"],
                    "metadata": {
                        "pdf_index": pdf_index,
                        "pdf_name": pdf_name,
                        "section": section["section"],
                        "page_start": section["page_start"],
                        "page_end": section["page_end"],
                        "is_fda": section.get("is_fda", False),
                        "content_type": self._classify_content_type(chunk["content"])
                    }
                }
                documents_batch.append(document)
        
        return documents_batch
    
    def _classify_content_type(self, content: str) -> str:
        """Classify content type for better retrieval"""
        content_lower = content.lower()
        
        medical_keywords = {
            'dose', 'dosage', 'mg', 'kg', 'injection', 'infusion', 'treatment',
            'therapy', 'side effects', 'adverse', 'contraindications', 'warnings',
            'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'
        }
        
        table_keywords = {'table', 'figure', 'chart', 'graph', 'data', 'results'}
        
        if any(keyword in content_lower for keyword in medical_keywords):
            return "medical"
        elif any(keyword in content_lower for keyword in table_keywords):
            return "tabular"
        elif len(content_lower.split()) < 50:  # Short content
            return "metadata"
        else:
            return "general"

# Example usage and testing when run directly
if __name__ == "__main__":
    print("=" * 60)
    print("PDF Processor Module")
    print("=" * 60)
    print("\nThis is a module designed to be imported and used in other scripts.")
    print("\nExample usage:")
    print("from pdf_preprocessor import PDFProcessor")
    print("processor = PDFProcessor()")
    print("text = processor.extract_text_from_pdf('your_file.pdf')")
    print("sections = processor.extract_sections(text)")
    print("documents = processor.prepare_documents_for_db('file.pdf', 0, sections)")
    print("\nTo test with a sample PDF, create a test script that imports this module.")
    print("\nCreating a quick self-test with sample text...")
    print("-" * 40)
    
    # Quick self-test with sample text
    processor = PDFProcessor()
    
    sample_text = """
    INDICATIONS AND USAGE
    This medication is indicated for the treatment of various conditions including pain and inflammation.
    
    DOSAGE AND ADMINISTRATION
    The recommended dosage is 50mg twice daily with food. Do not exceed 200mg per day.
    
    ADVERSE REACTIONS
    Common side effects may include headache, nausea, and dizziness.
    """
    
    print("Testing with sample text...")
    sections = processor.extract_sections(sample_text)
    print(f"✓ Extracted {len(sections)} sections")
    
    for section in sections:
        chunks = processor.chunk_content(section['content'], chunk_size=100, overlap=20)
        print(f"  - {section['section']}: {len(chunks)} chunks")
    
    documents = processor.prepare_documents_for_db("test.pdf", 0, sections)
    print(f"✓ Prepared {len(documents)} documents for database")
    print("\n✅ Self-test completed successfully!")