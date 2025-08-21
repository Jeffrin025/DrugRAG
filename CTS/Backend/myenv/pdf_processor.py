# import os
# import re
# import PyPDF2
# from typing import List, Dict, Any
# import uuid

# class PDFProcessor:
#     """PDF processor that handles text extraction, section identification, and chunking"""
    
#     def __init__(self):
#         # FDA sections for better organization
#         self.fda_sections = [
#             "BOXED WARNING", "INDICATIONS AND USAGE", "DOSAGE AND ADMINISTRATION",
#             "CONTRAINDICATIONS", "WARNINGS AND PRECAUTIONS", "ADVERSE REACTIONS",
#             "DRUG INTERACTIONS", "USE IN SPECIFIC POPULATIONS", "PATIENT COUNSELING INFORMATION",
#             "CLINICAL PHARMACOLOGY", "HOW SUPPLIED/STORAGE AND HANDLING", "MEDICATION GUIDE",
#             "DESCRIPTION", "CLINICAL STUDIES", "MECHANISM OF ACTION", "PHARMACOKINETICS",
#             "NONCLINICAL TOXICOLOGY", "CLINICAL TRIALS"
#         ]
        
#         self.fda_section_pattern = re.compile(
#             r'^\s*(' + '|'.join(re.escape(section) for section in self.fda_sections) + r')\s*$',
#             re.IGNORECASE | re.MULTILINE
#         )
    
#     def extract_text_from_pdf(self, pdf_path: str) -> str:
#         """Extract text from a PDF file with robust error handling"""
#         text = ""
#         try:
#             with open(pdf_path, 'rb') as file:
#                 pdf_reader = PyPDF2.PdfReader(file)
#                 for page_num, page in enumerate(pdf_reader.pages):
#                     try:
#                         page_text = page.extract_text()
#                         if page_text and page_text.strip():
#                             text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
#                         else:
#                             text += f"--- Page {page_num + 1} ---\n[Content not extractable - may contain images/scanned content]\n\n"
#                     except Exception as page_error:
#                         text += f"--- Page {page_num + 1} ---\n[Error extracting page content: {str(page_error)}]\n\n"
#         except Exception as e:
#             print(f"Error reading PDF {pdf_path}: {e}")
#             return f"Error extracting text from {pdf_path}: {str(e)}"
#         return text
    
#     def is_fda_format(self, text: str) -> bool:
#         """Check if the document follows FDA format"""
#         fda_section_count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
#         return fda_section_count >= 3
    
#     def extract_sections(self, text: str) -> List[Dict[str, Any]]:
#         """Extract sections from document, preserving all content with robust parsing"""
#         sections = []
#         current_section = "INTRODUCTION"
#         content = ""
#         page_num = 1
#         is_fda = self.is_fda_format(text)
        
#         lines = text.split('\n')
#         for line in lines:
#             # Handle page breaks
#             if line.startswith("--- Page "):
#                 if content.strip():
#                     sections.append({
#                         "section": current_section,
#                         "content": content.strip(),
#                         "page_start": page_num,
#                         "page_end": page_num,
#                         "is_fda": is_fda
#                     })
#                 content = ""
#                 match = re.match(r'--- Page (\d+) ---', line)
#                 if match:
#                     page_num = int(match.group(1))
#                 continue
            
#             # Handle section headers based on document type
#             section_match = None
#             if is_fda:
#                 section_match = self.fda_section_pattern.match(line.upper())
#             else:
#                 # Generic section detection for non-FDA documents
#                 section_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+(?:\.|:)?)\s*$', line) 
#                                and len(line.strip()) < 100 
#                                and not line.strip().isdigit())
            
#             if section_match:
#                 if content.strip():
#                     sections.append({
#                         "section": current_section,
#                         "content": content.strip(),
#                         "page_start": page_num,
#                         "page_end": page_num,
#                         "is_fda": is_fda
#                     })
#                 current_section = line.strip().upper()
#                 content = ""
#             else:
#                 content += line + "\n"
        
#         # Add the final section
#         if content.strip():
#             sections.append({
#                 "section": current_section,
#                 "content": content.strip(),
#                 "page_start": page_num,
#                 "page_end": page_num,
#                 "is_fda": is_fda
#             })
        
#         return sections
    
#     def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
#         """Create semantic chunks with overlap for better context preservation"""
#         chunks = []
#         words = content.split()
        
#         # Handle very short content
#         if len(words) <= chunk_size:
#             return [{"content": content, "chunk_id": "chunk_0"}]
        
#         for i in range(0, len(words), chunk_size - overlap):
#             chunk_words = words[i:i + chunk_size]
#             chunk_text = " ".join(chunk_words)
            
#             # Ensure we don't create empty chunks
#             if chunk_text.strip():
#                 chunks.append({
#                     "content": chunk_text,
#                     "chunk_id": f"chunk_{i//chunk_size}"
#                 })
        
#         return chunks
    
#     def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Prepare documents for database insertion with proper metadata"""
#         documents_batch = []
        
#         for section in sections:
#             for chunk in section.get("chunks", []):
#                 doc_id = str(uuid.uuid4())
#                 document = {
#                     "id": doc_id,
#                     "content": chunk["content"],
#                     "metadata": {
#                         "pdf_index": pdf_index,
#                         "pdf_name": pdf_name,
#                         "section": section["section"],
#                         "page_start": section["page_start"],
#                         "page_end": section["page_end"],
#                         "is_fda": section.get("is_fda", False),
#                         "content_type": self._classify_content_type(chunk["content"])
#                     }
#                 }
#                 documents_batch.append(document)
        
#         return documents_batch
    
#     def _classify_content_type(self, content: str) -> str:
#         """Classify content type for better retrieval"""
#         content_lower = content.lower()
        
#         medical_keywords = {
#             'dose', 'dosage', 'mg', 'kg', 'injection', 'infusion', 'treatment',
#             'therapy', 'side effects', 'adverse', 'contraindications', 'warnings',
#             'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'
#         }
        
#         table_keywords = {'table', 'figure', 'chart', 'graph', 'data', 'results'}
        
#         if any(keyword in content_lower for keyword in medical_keywords):
#             return "medical"
#         elif any(keyword in content_lower for keyword in table_keywords):
#             return "tabular"
#         elif len(content_lower.split()) < 50:  # Short content
#             return "metadata"
#         else:
#             return "general"


import os
import re
import PyPDF2
import pdfplumber
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
        """Extract text from a PDF file with robust error handling including tables"""
        text = ""
        try:
            # First try with pdfplumber for better table handling
            text = self._extract_with_pdfplumber(pdf_path)
            
            # Fallback to PyPDF2 if pdfplumber fails
            if not text.strip() or len(text.strip()) < 100:
                text = self._extract_with_pypdf2(pdf_path)
                
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            text = f"Error extracting text from {pdf_path}: {str(e)}"
        
        return text
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (better for tables)"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract regular text
                    page_text = page.extract_text()
                    
                    # Extract tables and convert to readable text
                    tables_text = self._extract_tables_from_page(page, page_num)
                    
                    if page_text or tables_text:
                        text += f"--- Page {page_num + 1} ---\n"
                        if page_text:
                            text += f"{page_text}\n"
                        if tables_text:
                            text += f"\nTABLES:\n{tables_text}\n"
                        text += "\n"
                    else:
                        text += f"--- Page {page_num + 1} ---\n[Content not extractable - may contain images/scanned content]\n\n"
                        
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            # Fallback to PyPDF2 will be attempted
        
        return text
    
    def _extract_tables_from_page(self, page, page_num: int) -> str:
        """Extract tables from a page and convert to readable text"""
        tables_text = ""
        try:
            tables = page.extract_tables()
            
            if tables:
                for table_num, table in enumerate(tables):
                    if table and any(any(cell for cell in row) for row in table):
                        tables_text += f"\nTable {table_num + 1}:\n"
                        tables_text += self._format_table_as_text(table)
                        tables_text += "\n"
                        
        except Exception as e:
            print(f"Table extraction failed on page {page_num}: {e}")
            
        return tables_text
    
    def _format_table_as_text(self, table: List[List[str]]) -> str:
        """Convert table data to readable text format"""
        if not table or not any(table):
            return ""
        
        # Clean the table data
        cleaned_table = []
        for row in table:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            cleaned_table.append(cleaned_row)
        
        # Format as readable text
        table_text = ""
        for row in cleaned_table:
            # Filter out empty rows
            if any(cell for cell in row):
                table_text += " | ".join(row) + "\n"
        
        return table_text
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Fallback extraction using PyPDF2"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                        else:
                            text += f"--- Page {page_num + 1} ---\n[Content not extractable - may contain images/scanned content]\n\n"
                    except Exception as page_error:
                        text += f"--- Page {page_num + 1} ---\n[Error extracting page content: {str(page_error)}]\n\n"
        except Exception as e:
            print(f"PyPDF2 extraction also failed: {e}")
            
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
            # First ensure sections have chunks
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
                        "content_type": self._classify_content_type(chunk["content"]),
                        "has_tables": "TABLES:" in chunk["content"]  # Track table content
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
        
        # Check for table content first
        if "TABLES:" in content or any(keyword in content_lower for keyword in table_keywords):
            return "tabular"
        elif any(keyword in content_lower for keyword in medical_keywords):
            return "medical"
        elif len(content_lower.split()) < 50:  # Short content
            return "metadata"
        else:
            return "general"