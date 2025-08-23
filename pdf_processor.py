# # import os
# # import re
# # import pdfplumber
# # import camelot
# # import pandas as pd
# # from typing import List, Dict, Any, Tuple, Optional
# # import uuid
# # import json
# # from collections import defaultdict

# # class PDFProcessor:
# #     """Optimized PDF processor for text and table extraction with proper page tracking"""

# #     def __init__(self):
# #         # FDA sections
# #         self.fda_sections = [
# #             "BOXED WARNING", "INDICATIONS AND USAGE", "DOSAGE AND ADMINISTRATION",
# #             "CONTRAINDICATIONS", "WARNINGS AND PRECAUTIONS", "ADVERSE REACTIONS",
# #             "DRUG INTERACTIONS", "USE IN SPECIFIC POPULATIONS", "PATIENT COUNSELING INFORMATION",
# #             "CLINICAL PHARMACOLOGY", "HOW SUPPLIED/STORAGE AND HANDLING", "MEDICATION GUIDE",
# #             "DESCRIPTION", "CLINICAL STUDIES", "MECHANISM OF ACTION", "PHARMACOKINETICS",
# #             "NONCLINICAL TOXICOLOGY", "CLINICAL TRIALS"
# #         ]
# #         self.fda_section_pattern = re.compile(
# #             r'^\s*(' + '|'.join(re.escape(section) for section in self.fda_sections) + r')\s*$',
# #             re.IGNORECASE | re.MULTILINE
# #         )
        
# #         # Page number detection patterns
# #         self.page_number_patterns = [
# #             r'^\s*(\d+)\s*$',  # Just a number on a line
# #             r'^\s*-\s*(\d+)\s*-\s*$',  # - 1 -
# #             r'^\s*Page\s+(\d+)\s*$',  # Page 1
# #             r'^\s*(\d+)\s+of\s+\d+\s*$',  # 1 of 10
# #         ]

# #     def _extract_page_number_from_text(self, text: str, page_num: int) -> int:
# #         """
# #         Try to extract the actual page number from the text content.
# #         Returns the detected page number or falls back to the PDF page number.
# #         """
# #         lines = text.split('\n')
        
# #         # Check first few and last few lines for page numbers
# #         check_lines = lines[:5] + lines[-5:]
        
# #         for line in check_lines:
# #             line = line.strip()
# #             for pattern in self.page_number_patterns:
# #                 match = re.match(pattern, line, re.IGNORECASE)
# #                 if match:
# #                     try:
# #                         detected_page = int(match.group(1))
# #                         # Validate that this is a reasonable page number
# #                         if 1 <= detected_page <= 1000:  # Reasonable range for documents
# #                             return detected_page
# #                     except (ValueError, IndexError):
# #                         continue
        
# #         # Fall back to PDF page number if no page number detected in text
# #         return page_num

# #     def _is_probably_table(self, rows: List[List[str]]) -> bool:
# #         """Improved table detection heuristic"""
# #         if not rows or len(rows) < 2:
# #             return False

# #         # Check if this looks like a paragraph masquerading as a table
# #         if len(rows) == 1 or (len(rows) == 2 and len([c for c in rows[1] if c.strip()]) == 0):
# #             return False

# #         # Count non-empty columns in each row
# #         col_counts = [len([c for c in row if c.strip()]) for row in rows]
# #         avg_cols = sum(col_counts) / len(col_counts)

# #         # Rule 1: must have at least 2 average columns
# #         if avg_cols < 2:
# #             return False

# #         # Rule 2: at least 60% of rows should share similar column count
# #         most_common = max(set(col_counts), key=col_counts.count)
# #         if col_counts.count(most_common) < len(rows) * 0.6:
# #             return False

# #         return True

# #     def _is_likely_header_row(self, row: List[str], next_row: Optional[List[str]] = None) -> bool:
# #         """Determine if a row is likely a header"""
# #         if not any(cell.strip() for cell in row):
# #             return False
        
# #         header_indicators = 0
# #         total_cells = len([cell for cell in row if cell.strip()])
        
# #         for cell in row:
# #             cell_text = cell.strip()
# #             if not cell_text:
# #                 continue
                
# #             # Header indicators
# #             if cell_text.isupper():
# #                 header_indicators += 1
# #             elif re.search(r'[%$#&]|\b(rate|ratio|percentage|score|value)\b', cell_text.lower()):
# #                 header_indicators += 1
# #             elif len(cell_text) < 20 and not cell_text.isdigit():
# #                 header_indicators += 1
        
# #         # If next row is provided, check if it contains data (numbers)
# #         if next_row:
# #             data_indicators = 0
# #             for cell in next_row:
# #                 if re.search(r'\d', cell):
# #                     data_indicators += 1
# #                     break
            
# #             if data_indicators > 0 and header_indicators > 0:
# #                 return True
        
# #         return header_indicators / total_cells > 0.5 if total_cells > 0 else False

# #     def _structure_table_data(self, rows: List[List[str]], page_num: int, table_index: int) -> Dict[str, Any]:
# #         """Improved table structure detection"""
# #         if not rows or len(rows) < 2:
# #             return {
# #                 "table_id": str(uuid.uuid4()),
# #                 "page_number": page_num,
# #                 "table_index": table_index,
# #                 "headers": [],
# #                 "data": [],
# #                 "text_representation": "",
# #                 "raw_rows": rows
# #             }
        
# #         # Try to identify header row
# #         header_row_idx = 0
# #         found_header = False
        
# #         if len(rows) > 1 and self._is_likely_header_row(rows[0], rows[1]):
# #             header_row_idx = 0
# #             found_header = True
# #         else:
# #             for i in range(min(3, len(rows) - 1)):
# #                 if self._is_likely_header_row(rows[i], rows[i + 1]):
# #                     header_row_idx = i
# #                     found_header = True
# #                     break
        
# #         if found_header:
# #             headers = [cell.strip() for cell in rows[header_row_idx]]
# #             data_rows = rows[header_row_idx + 1:]
# #         else:
# #             max_cols = max(len(row) for row in rows)
# #             headers = [f"Column_{i+1}" for i in range(max_cols)]
# #             data_rows = rows
        
# #         # Clean up headers
# #         max_data_cols = max((len(row) for row in data_rows), default=0)
# #         if len(headers) < max_data_cols:
# #             headers.extend([f"Column_{i+1}" for i in range(len(headers), max_data_cols)])
        
# #         # Process data rows
# #         structured_data = []
# #         for row in data_rows:
# #             if any(cell.strip() for cell in row):
# #                 padded_row = row + [''] * (len(headers) - len(row))
# #                 structured_data.append([cell.strip() for cell in padded_row])
        
# #         # Create text representation
# #         text_representation = self._create_table_text_representation(headers, structured_data, page_num)
        
# #         return {
# #             "table_id": str(uuid.uuid4()),
# #             "page_number": page_num,
# #             "table_index": table_index,
# #             "headers": headers,
# #             "data": structured_data,
# #             "text_representation": text_representation,
# #             "raw_rows": rows
# #         }

# #     def _create_table_text_representation(self, headers: List[str], data: List[List[str]], page_num: int) -> str:
# #         """Create comprehensive textual representation of table for better searchability"""
# #         text_rep = f"Table from page {page_num}. "
        
# #         # Add headers
# #         if headers:
# #             text_rep += f"Headers: {', '.join([h for h in headers if h])}. "
        
# #         # Add all data rows (not just sample) for comprehensive search
# #         for i, row in enumerate(data):
# #             if any(cell.strip() for cell in row):  # Skip empty rows
# #                 row_data = []
# #                 for j, cell in enumerate(row):
# #                     if cell.strip():  # Only include non-empty cells
# #                         header_name = headers[j] if j < len(headers) and headers[j] else f"Column_{j+1}"
# #                         row_data.append(f"{header_name}: {cell}")
                
# #                 if row_data:
# #                     text_rep += f"Row {i+1}: {', '.join(row_data)}. "
        
# #         return text_rep.strip()


# #     def extract_text_and_tables(self, pdf_path: str, start_page: int = 1) -> List[Dict[str, Any]]:
# #         """Extract text and tables with proper page tracking and better error handling"""
# #         parsed_pages = []

# #         with pdfplumber.open(pdf_path) as pdf:
# #             for pdf_page_num, page in enumerate(pdf.pages, start=1):
# #                 if pdf_page_num < start_page:
# #                     continue

# #                 # Extract text first to detect actual page number
# #                 full_text = page.extract_text() or ""
# #                 actual_page_num = self._extract_page_number_from_text(full_text, pdf_page_num)
                
# #                 page_data = {
# #                     "pdf_page_number": pdf_page_num,
# #                     "actual_page_number": actual_page_num,
# #                     "text": full_text,
# #                     "tables": []
# #                 }

# #                 # Extract tables with pdfplumber (bordered tables)
# #                 try:
# #                     tables = page.extract_tables()
# #                     if tables:
# #                         for t_idx, table in enumerate(tables):
# #                             if table:
# #                                 formatted_rows = [[str(cell).replace("\n", " ").strip() if cell else "" for cell in row] for row in table]
# #                                 if self._is_probably_table(formatted_rows):
# #                                     structured_table = self._structure_table_data(formatted_rows, actual_page_num, t_idx + 1)
# #                                     page_data["tables"].append(structured_table)
# #                                     print(f"✓ Found table on page {actual_page_num} (PDFplumber)")
# #                                 else:
# #                                     # Treat as paragraph text
# #                                     joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
# #                                     page_data["text"] += "\n" + joined_text
# #                 except Exception as e:
# #                     print(f"⚠️ PDFplumber table extraction error on page {pdf_page_num}: {e}")

# #                 # Try Camelot for borderless tables (with suppressed warnings)
# #                 if not page_data["tables"]:
# #                     try:
# #                         # Temporarily suppress Camelot warnings
# #                         import warnings
# #                         with warnings.catch_warnings():
# #                             warnings.filterwarnings("ignore", category=UserWarning, module="camelot")
                            
# #                             camelot_tables = camelot.read_pdf(pdf_path, pages=str(pdf_page_num), flavor="stream")
# #                             for c_idx, c_table in enumerate(camelot_tables):
# #                                 df = c_table.df
# #                                 formatted_rows = df.values.tolist()
                                
# #                                 if self._is_probably_table(formatted_rows):
# #                                     structured_table = self._structure_table_data(formatted_rows, actual_page_num, c_idx + 1)
# #                                     page_data["tables"].append(structured_table)
# #                                     print(f"✓ Found table on page {actual_page_num} (Camelot)")
# #                                 else:
# #                                     joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
# #                                     page_data["text"] += "\n" + joined_text
# #                     except Exception as e:
# #                         print(f"⚠️ Camelot table extraction error on page {pdf_page_num}: {e}")

# #                 parsed_pages.append(page_data)
                
# #                 # Print progress
# #                 if pdf_page_num % 10 == 0 or pdf_page_num == len(pdf.pages):
# #                     print(f"Processed page {pdf_page_num}/{len(pdf.pages)}")

# #         return parsed_pages
    
# #     def extract_text_from_pdf(self, pdf_path: str, start_page: int = 1) -> str:
# #         """
# #         Returns combined text as a single string for backward compatibility.
# #         This method is needed for the existing RAGOrchestrator code.
# #         """
# #         pages_data = self.extract_text_and_tables(pdf_path, start_page=start_page)
# #         full_text = "\n".join(page['text'] for page in pages_data if page['text'])
# #         return full_text

# #     def is_fda_format(self, text: str) -> bool:
# #         count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
# #         return count >= 3

# #     def extract_sections(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
# #         """Extract sections with proper page tracking"""
# #         if not pages_data:
# #             return []
        
# #         # Combine text from all pages with page markers
# #         combined_text = ""
# #         for page in pages_data:
# #             combined_text += f"\n--- Page {page['actual_page_number']} ---\n{page['text']}"
        
# #         is_fda = self.is_fda_format(combined_text)
# #         sections = []
# #         current_section = "INTRODUCTION"
# #         content = ""
# #         current_page = pages_data[0]['actual_page_number'] if pages_data else 1
# #         page_start = current_page

# #         lines = combined_text.split("\n")
# #         for line in lines:
# #             # Check for page markers
# #             if line.startswith("--- Page "):
# #                 if content.strip():
# #                     sections.append({
# #                         "section": current_section,
# #                         "content": content.strip(),
# #                         "page_start": page_start,
# #                         "page_end": current_page,
# #                         "is_fda": is_fda
# #                     })
# #                     content = ""
                
# #                 match = re.match(r'--- Page (\d+) ---', line)
# #                 if match:
# #                     current_page = int(match.group(1))
# #                     page_start = current_page
# #                 continue

# #             # Check for section headers
# #             section_match = None
# #             if is_fda:
# #                 section_match = self.fda_section_pattern.match(line.upper())
# #             else:
# #                 section_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+(?:\.|:)?)\s*$', line)
# #                                  and len(line.strip()) < 100
# #                                  and not line.strip().isdigit())

# #             if section_match:
# #                 if content.strip():
# #                     sections.append({
# #                         "section": current_section,
# #                         "content": content.strip(),
# #                         "page_start": page_start,
# #                         "page_end": current_page,
# #                         "is_fda": is_fda
# #                     })
# #                 current_section = line.strip().upper()
# #                 content = ""
# #                 page_start = current_page
# #             else:
# #                 content += line + "\n"

# #         if content.strip():
# #             sections.append({
# #                 "section": current_section,
# #                 "content": content.strip(),
# #                 "page_start": page_start,
# #                 "page_end": current_page,
# #                 "is_fda": is_fda
# #             })

# #         return sections

# #     def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
# #         chunks = []
# #         words = content.split()
# #         if len(words) <= chunk_size:
# #             return [{"content": content, "chunk_id": "chunk_0"}]
# #         for i in range(0, len(words), chunk_size - overlap):
# #             chunk_words = words[i:i + chunk_size]
# #             chunk_text = " ".join(chunk_words)
# #             if chunk_text.strip():
# #                 chunks.append({
# #                     "content": chunk_text,
# #                     "chunk_id": f"chunk_{i // chunk_size}"
# #                 })
# #         return chunks

# #     def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, 
# #                             sections: List[Dict[str, Any]], 
# #                                 tables: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
# #         """Prepare documents for database with enhanced table processing"""
# #         documents_batch = []
        
# #         # Process text sections
# #         for section in sections:
# #             if "chunks" not in section:
# #                 section["chunks"] = self.chunk_content(section["content"])
# #             for chunk in section["chunks"]:
# #                 doc_id = str(uuid.uuid4())
# #                 metadata = {
# #                     "pdf_index": pdf_index,
# #                     "pdf_name": pdf_name,
# #                     "section": section["section"],
# #                     "page_start": section["page_start"],
# #                     "page_end": section["page_end"],
# #                     "is_fda": section.get("is_fda", False),
# #                     "content_type": self._classify_content_type(chunk["content"]),
# #                     "has_tables": False,
# #                     "doc_type": "text"
# #                 }
                
# #                 documents_batch.append({
# #                     "id": doc_id,
# #                     "content": chunk["content"],
# #                     "metadata": self._ensure_chromadb_compatible(metadata)
# #                 })
        
# #         # Process tables with enhanced content
# #         if tables:
# #             print(f"Processing {len(tables)} tables for database...")
# #             for table_idx, table in enumerate(tables):
# #                 doc_id = str(uuid.uuid4())
                
# #                 # Create more detailed table content for better searchability
# #                 detailed_content = self._create_detailed_table_content(table)
                
# #                 metadata = {
# #                     "pdf_index": pdf_index,
# #                     "pdf_name": pdf_name,
# #                     "section": "TABULAR_DATA",
# #                     "page_start": table["page_number"],
# #                     "page_end": table["page_number"],
# #                     "is_fda": False,
# #                     "content_type": "tabular",
# #                     "has_tables": True,
# #                     "doc_type": "table",
# #                     "table_id": table["table_id"],
# #                     "table_index": table["table_index"],
# #                     "citation": f"Page {table['page_number']}, Table {table['table_index']}",
# #                     "table_headers": table["headers"],
# #                     "table_row_count": len(table["data"]),
# #                     "table_data_sample": json.dumps(table["data"][:3]) if table["data"] else "[]"
# #                 }
                
# #                 table_doc = {
# #                     "id": doc_id,
# #                     "content": detailed_content,  # Use detailed content instead of basic representation
# #                     "metadata": self._ensure_chromadb_compatible(metadata)
# #                 }
# #                 documents_batch.append(table_doc)
                
# #                 # Also create individual row documents for better searchability
# #                 row_docs = self._create_row_documents(table, pdf_name, pdf_index)
# #                 documents_batch.extend(row_docs)
        
# #         return documents_batch

# #     def _create_detailed_table_content(self, table: Dict[str, Any]) -> str:
# #         """Create comprehensive table content for semantic search"""
# #         content = f"Table on page {table['page_number']}. "
        
# #         # Add headers
# #         if table["headers"]:
# #             content += f"Table headers: {', '.join([h for h in table['headers'] if h])}. "
        
# #         # Add all data with context
# #         for i, row in enumerate(table["data"]):
# #             if any(cell.strip() for cell in row):
# #                 row_content = []
# #                 for j, cell in enumerate(row):
# #                     if cell.strip():
# #                         header = table["headers"][j] if j < len(table["headers"]) else f"Column_{j+1}"
# #                         row_content.append(f"{header}: {cell}")
                
# #                 if row_content:
# #                     content += f"Row {i+1}: {', '.join(row_content)}. "
        
# #         return content

# #     def _create_row_documents(self, table: Dict[str, Any], pdf_name: str, pdf_index: int, pdf_page_num: int) -> List[Dict[str, Any]]:
# #         """Create individual documents for each table row"""
# #         row_documents = []
        
# #         for row_idx, row in enumerate(table["data"]):
# #             if any(cell.strip() for cell in row):
# #                 doc_id = str(uuid.uuid4())
                
# #                 # Create row content
# #                 row_content = []
# #                 for col_idx, cell in enumerate(row):
# #                     if cell.strip():
# #                         header = table["headers"][col_idx] if col_idx < len(table["headers"]) else f"Column_{col_idx+1}"
# #                         row_content.append(f"{header}: {cell}")
                
# #                 if row_content:
# #                     content = f"Table data from page {pdf_page_num}: {', '.join(row_content)}"
                    
# #                     metadata = {
# #                         "pdf_index": pdf_index,
# #                         "pdf_name": pdf_name,
# #                         "section": "TABULAR_DATA_ROW",
# #                         "pdf_page_number": pdf_page_num,  # Use PDF page number
# #                         "detected_page_number": table["page_number"],  # Detected page number
# #                         "is_fda": False,
# #                         "content_type": "tabular_row",
# #                         "has_tables": True,
# #                         "doc_type": "table_row",
# #                         "table_id": table["table_id"],
# #                         "table_index": table["table_index"],
# #                         "row_index": row_idx,
# #                         "citation": f"Page {pdf_page_num}, Table {table['table_index']}, Row {row_idx+1}"
# #                     }
                    
# #                     row_documents.append({
# #                         "id": doc_id,
# #                         "content": content,
# #                         "metadata": self._ensure_chromadb_compatible(metadata)
# #                     })
        
# #         return row_documents

# #     def _classify_content_type(self, content: str) -> str:
# #         content_lower = content.lower()
# #         medical_keywords = {
# #             'dose', 'dosage', 'mg', 'kg', 'injection', 'infusion', 'treatment',
# #             'therapy', 'side effects', 'adverse', 'contraindications', 'warnings',
# #             'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'
# #         }
# #         table_keywords = {'table', 'figure', 'chart', 'graph', 'data', 'results'}

# #         if "TABLES:" in content or any(keyword in content_lower for keyword in table_keywords):
# #             return "tabular"
# #         elif any(keyword in content_lower for keyword in medical_keywords):
# #             return "medical"
# #         elif len(content_lower.split()) < 50:
# #             return "metadata"
# #         else:
# #             return "general"
        
# #     def _ensure_chromadb_compatible(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
# #         """Ensure all metadata values are compatible with ChromaDB"""
# #         compatible_metadata = {}
# #         for key, value in metadata.items():
# #             if isinstance(value, (list, tuple)):
# #                 # Convert lists to JSON strings
# #                 compatible_metadata[key] = json.dumps(value)
# #             elif isinstance(value, (str, int, float, bool)) or value is None:
# #                 compatible_metadata[key] = value
# #             else:
# #                 # Convert other types to string
# #                 compatible_metadata[key] = str(value)
# #         return compatible_metadata

# #     def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, 
# #                             sections: List[Dict[str, Any]], 
# #                             tables: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
# #         """Prepare documents for database with proper page tracking"""
# #         documents_batch = []
        
# #         # Process text sections - use PDF page numbers for citations
# #         for section in sections:
# #             if "chunks" not in section:
# #                 section["chunks"] = self.chunk_content(section["content"])
# #             for chunk in section["chunks"]:
# #                 doc_id = str(uuid.uuid4())
# #                 metadata = {
# #                     "pdf_index": pdf_index,
# #                     "pdf_name": pdf_name,
# #                     "section": section["section"],
# #                     "pdf_page_start": section["page_start"],  # Store PDF page numbers
# #                     "pdf_page_end": section["page_end"],      # Store PDF page numbers
# #                     "detected_page_start": section["page_start"],  # Detected page numbers
# #                     "detected_page_end": section["page_end"],      # Detected page numbers
# #                     "is_fda": section.get("is_fda", False),
# #                     "content_type": self._classify_content_type(chunk["content"]),
# #                     "has_tables": False,
# #                     "doc_type": "text"
# #                 }
                
# #                 documents_batch.append({
# #                     "id": doc_id,
# #                     "content": chunk["content"],
# #                     "metadata": self._ensure_chromadb_compatible(metadata)
# #                 })
        
# #         # Process tables - use PDF page numbers for citations
# #         if tables:
# #             print(f"Processing {len(tables)} tables for database...")
# #             for table_idx, table in enumerate(tables):
# #                 doc_id = str(uuid.uuid4())
                
# #                 # Use PDF page number for citation (not detected page number)
# #                 pdf_page_num = table.get("pdf_page_number", table["page_number"])
                
# #                 detailed_content = self._create_detailed_table_content(table)
                
# #                 metadata = {
# #                     "pdf_index": pdf_index,
# #                     "pdf_name": pdf_name,
# #                     "section": "TABULAR_DATA",
# #                     "pdf_page_number": pdf_page_num,  # PDF page number
# #                     "detected_page_number": table["page_number"],  # Detected page number
# #                     "is_fda": False,
# #                     "content_type": "tabular",
# #                     "has_tables": True,
# #                     "doc_type": "table",
# #                     "table_id": table["table_id"],
# #                     "table_index": table["table_index"],
# #                     "citation": f"Page {pdf_page_num}, Table {table['table_index']}",
# #                     "table_headers": table["headers"],
# #                     "table_row_count": len(table["data"]),
# #                     "table_data_sample": json.dumps(table["data"][:3]) if table["data"] else "[]"
# #                 }
                
# #                 table_doc = {
# #                     "id": doc_id,
# #                     "content": detailed_content,
# #                     "metadata": self._ensure_chromadb_compatible(metadata)
# #                 }
# #                 documents_batch.append(table_doc)
                
# #                 # Also create individual row documents
# #                 row_docs = self._create_row_documents(table, pdf_name, pdf_index, pdf_page_num)
# #                 documents_batch.extend(row_docs)
        
# #         return documents_batch

# #     def process_pdf_for_db(self, pdf_path: str, pdf_index: int = 0) -> List[Dict[str, Any]]:
# #         """Complete PDF processing pipeline"""
# #         pdf_name = os.path.basename(pdf_path)
# #         print(f"\n[Processing] Starting processing for {pdf_name}...")
        
# #         # Extract text and tables with proper page tracking
# #         pages_data = self.extract_text_and_tables(pdf_path)
        
# #         # Extract all tables from all pages
# #         all_tables = []
# #         for page in pages_data:
# #             all_tables.extend(page['tables'])
        
# #         print(f"\n[Processing Summary] Extracted {len(all_tables)} tables from {len(pages_data)} pages")
        
# #         # Extract sections from pages data
# #         sections = self.extract_sections(pages_data)
# #         print(f"[Processing Summary] Identified {len(sections)} sections in the document")
        
# #         # Prepare documents for database
# #         documents = self.prepare_documents_for_db(pdf_name, pdf_index, sections, all_tables)
# #         print(f"[Processing Summary] Prepared {len(documents)} documents for database storage")
        
# #         # Count document types
# #         text_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'text')
# #         table_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'table')
# #         print(f"[Processing Summary] Document types - Text: {text_docs}, Tables: {table_docs}")
        
# #         return documents


# # # ====================== ChromaDB Integration ======================
# # def add_to_chroma_db(documents: List[Dict[str, Any]], collection):
# #     """
# #     Add processed documents to ChromaDB collection.
# #     """
# #     ids = [doc["id"] for doc in documents]
# #     contents = [doc["content"] for doc in documents]
# #     metadatas = [doc["metadata"] for doc in documents]
    
# #     print(f"\n[Database] Adding {len(documents)} documents to ChromaDB collection...")
    
# #     # Print sample of what's being added to the database
# #     print(f"[Database Sample] First document content (first 200 chars): {contents[0][:200]}...")
# #     print(f"[Database Sample] First document metadata keys: {list(metadatas[0].keys())}")
    
# #     collection.add(
# #         ids=ids,
# #         documents=contents,
# #         metadatas=metadatas
# #     )
    
# #     print(f"[Database] Successfully added {len(documents)} documents to the collection")
    

# #     return len(documents)



# import os
# import re
# import uuid
# import json
# from typing import List, Dict, Any, Optional
# from unstructured.partition.pdf import partition_pdf
# from unstructured.documents.elements import CompositeElement, Table, Image
# import google.generativeai as genai
# from PIL import Image as PILImage
# import io
# import base64
# import pdfplumber
# import camelot
# import pandas as pd
# import warnings

# class PDFProcessor:
#     """Enhanced PDF processor with multiple extraction strategies"""
    
#     def __init__(self, gemini_api_key: str):
#         self.gemini_api_key = gemini_api_key
#         genai.configure(api_key=gemini_api_key)
#         self.multimodal_model = genai.GenerativeModel('gemini-1.5-flash')
        
#         # FDA sections
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

#     def extract_elements(self, pdf_path: str) -> List[Dict[str, Any]]:
#         """Extract elements using multiple strategies for better table and image detection"""
#         print(f"Extracting elements from {pdf_path}...")
        
#         processed_elements = []
        
#         try:
#             # Strategy 1: Use Unstructured.io for text and basic structure
#             elements = partition_pdf(
#                 filename=pdf_path,
#                 extract_images_in_pdf=True,
#                 infer_table_structure=True,
#                 chunking_strategy="by_title",
#                 max_characters=4000,
#                 new_after_n_chars=3800,
#                 combine_text_under_n_chars=2000,
#                 image_output_dir_path="./extracted_images",
#                 strategy="hi_res",
#                 languages=["eng"],
#             )
            
#             page_number = 1
            
#             for element in elements:
#                 element_data = {
#                     "type": type(element).__name__,
#                     "text": str(element),
#                     "metadata": element.metadata.to_dict(),
#                     "page_number": element.metadata.page_number if hasattr(element.metadata, 'page_number') else page_number
#                 }
                
#                 if hasattr(element.metadata, 'page_number'):
#                     page_number = element.metadata.page_number
                
#                 # Handle tables
#                 if isinstance(element, Table):
#                     element_data["table_data"] = self._structure_table_data(element)
#                     element_data["text_representation"] = self._create_table_text_representation(
#                         element_data["table_data"], element_data["page_number"]
#                     )
                
#                 # Handle images
#                 elif isinstance(element, Image) and hasattr(element.metadata, 'image_path'):
#                     element_data["image_path"] = element.metadata.image_path
#                     element_data["image_description"] = self._describe_image(element_data["image_path"])
                
#                 processed_elements.append(element_data)
            
#         except Exception as e:
#             print(f"Unstructured.io extraction failed: {e}")
        
#         # Strategy 2: Use pdfplumber for additional text extraction
#         try:
#             with pdfplumber.open(pdf_path) as pdf:
#                 for page_num, page in enumerate(pdf.pages, 1):
#                     text = page.extract_text()
#                     if text:
#                         processed_elements.append({
#                             "type": "TextElement",
#                             "text": text,
#                             "metadata": {"page_number": page_num},
#                             "page_number": page_num
#                         })
#         except Exception as e:
#             print(f"PDFPlumber extraction failed: {e}")
        
#         # Strategy 3: Use Camelot for table extraction (better for complex tables)
#         try:
#             tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
#             for i, table in enumerate(tables):
#                 if table.parsing_report and table.parsing_report.get('accuracy', 0) > 50:
#                     table_data = {
#                         "headers": table.df.iloc[0].tolist() if not table.df.empty else [],
#                         "data": table.df.iloc[1:].values.tolist() if len(table.df) > 1 else [],
#                         "row_count": len(table.df) - 1 if len(table.df) > 1 else 0,
#                         "col_count": len(table.df.columns) if not table.df.empty else 0
#                     }
                    
#                     processed_elements.append({
#                         "type": "Table",
#                         "text": table.df.to_string(),
#                         "metadata": {"page_number": table.page},
#                         "page_number": table.page,
#                         "table_data": table_data,
#                         "text_representation": self._create_table_text_representation(table_data, table.page)
#                     })
#         except Exception as e:
#             print(f"Camelot table extraction failed: {e}")
        
#         return processed_elements

#     def _structure_table_data(self, table_element: Table) -> Dict[str, Any]:
#         """Structure table data from Unstructured.io"""
#         table_text = str(table_element)
#         rows = [line.split('\t') for line in table_text.split('\n') if line.strip()]
        
#         if not rows:
#             return {"headers": [], "data": [], "row_count": 0, "col_count": 0}
        
#         # Try to identify headers
#         headers = []
#         data_rows = rows
        
#         if len(rows) > 1 and self._is_likely_header_row(rows[0], rows[1]):
#             headers = [cell.strip() for cell in rows[0]]
#             data_rows = rows[1:]
#         else:
#             max_cols = max(len(row) for row in rows)
#             headers = [f"Column_{i+1}" for i in range(max_cols)]
        
#         return {
#             "headers": headers,
#             "data": data_rows,
#             "row_count": len(data_rows),
#             "col_count": len(headers)
#         }

#     def _is_likely_header_row(self, row: List[str], next_row: List[str]) -> bool:
#         """Determine if a row is likely a header"""
#         if not any(cell.strip() for cell in row):
#             return False
        
#         header_indicators = 0
#         total_cells = len([cell for cell in row if cell.strip()])
        
#         for cell in row:
#             cell_text = cell.strip()
#             if not cell_text:
#                 continue
                
#             if cell_text.isupper():
#                 header_indicators += 1
#             elif re.search(r'[%$#&]|\b(rate|ratio|percentage|score|value)\b', cell_text.lower()):
#                 header_indicators += 1
#             elif len(cell_text) < 20 and not cell_text.isdigit():
#                 header_indicators += 1
        
#         # Check if next row contains data (numbers)
#         data_indicators = 0
#         for cell in next_row:
#             if re.search(r'\d', cell):
#                 data_indicators += 1
#                 break
        
#         return header_indicators > 0 and data_indicators > 0

#     def _create_table_text_representation(self, table_data: Dict[str, Any], page_num: int) -> str:
#         """Create comprehensive textual representation of table"""
#         text_rep = f"Table from page {page_num}. "
        
#         if table_data["headers"]:
#             text_rep += f"Headers: {', '.join([h for h in table_data['headers'] if h])}. "
        
#         # Add all data rows for comprehensive search
#         for i, row in enumerate(table_data["data"]):
#             if any(cell.strip() for cell in row):
#                 row_data = []
#                 for j, cell in enumerate(row):
#                     if cell.strip() and j < len(table_data["headers"]):
#                         header_name = table_data["headers"][j] if table_data["headers"][j] else f"Column_{j+1}"
#                         row_data.append(f"{header_name}: {cell}")
                
#                 if row_data:
#                     text_rep += f"Row {i+1}: {', '.join(row_data)}. "
        
#         return text_rep.strip()

#     def _describe_image(self, image_path: str) -> str:
#         """Generate description for image using multimodal LLM"""
#         try:
#             if not os.path.exists(image_path):
#                 return "Image description not available - file not found"
            
#             # Load and encode image
#             with open(image_path, "rb") as img_file:
#                 img = PILImage.open(img_file)
                
#                 # Resize if too large
#                 if max(img.size) > 1000:
#                     img.thumbnail((1000, 1000))
                
#                 # Convert to bytes
#                 img_byte_arr = io.BytesIO()
#                 img.save(img_byte_arr, format='JPEG')
#                 img_byte_arr = img_byte_arr.getvalue()
            
#             prompt = """
#             Analyze this medical image from a pharmaceutical document. Describe:
#             1. What the image shows (graph, chart, diagram, molecular structure, etc.)
#             2. Key elements and labels visible
#             3. Any numerical data or trends visible
#             4. The likely purpose or message of this image
            
#             Provide a comprehensive description that would help understand the image content.
#             """
            
#             response = self.multimodal_model.generate_content([
#                 prompt,
#                 {"mime_type": "image/jpeg", "data": base64.b64encode(img_byte_arr).decode('utf-8')}
#             ])
            
#             return response.text
            
#         except Exception as e:
#             print(f"Error describing image {image_path}: {e}")
#             return f"Medical image showing relevant information. [Image processing error: {str(e)}]"

#     def extract_sections(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Extract sections from processed elements"""
#         if not elements:
#             return []
        
#         # Combine text elements with page markers
#         combined_text = ""
#         current_page = 1
        
#         for element in elements:
#             if element["type"] in ["CompositeElement", "TextElement"] and element["text"].strip():
#                 if element["page_number"] != current_page:
#                     combined_text += f"\n--- Page {element['page_number']} ---\n"
#                     current_page = element["page_number"]
#                 combined_text += element["text"] + "\n"
        
#         # Check if document follows FDA format
#         is_fda = self.is_fda_format(combined_text)
        
#         # Extract sections
#         sections = []
#         current_section = "INTRODUCTION"
#         content = ""
#         page_start = 1
#         page_end = 1

#         lines = combined_text.split("\n")
#         for line in lines:
#             # Check for page markers
#             if line.startswith("--- Page "):
#                 if content.strip():
#                     sections.append({
#                         "section": current_section,
#                         "content": content.strip(),
#                         "page_start": page_start,
#                         "page_end": page_end,
#                         "is_fda": is_fda
#                     })
#                     content = ""
                
#                 match = re.match(r'--- Page (\d+) ---', line)
#                 if match:
#                     page_start = int(match.group(1))
#                     page_end = page_start
#                 continue

#             # Check for section headers
#             section_match = None
#             if is_fda:
#                 section_match = self.fda_section_pattern.match(line.upper())
#             else:
#                 section_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+(?:\.|:)?)\s*$', line)
#                                  and len(line.strip()) < 100
#                                  and not line.strip().isdigit())

#             if section_match:
#                 if content.strip():
#                     sections.append({
#                         "section": current_section,
#                         "content": content.strip(),
#                         "page_start": page_start,
#                         "page_end": page_end,
#                         "is_fda": is_fda
#                     })
#                 current_section = line.strip().upper()
#                 content = ""
#                 page_start = page_end
#             else:
#                 content += line + "\n"
#                 page_end = current_page

#         if content.strip():
#             sections.append({
#                 "section": current_section,
#                 "content": content.strip(),
#                 "page_start": page_start,
#                 "page_end": page_end,
#                 "is_fda": is_fda
#             })

#         return sections

#     def is_fda_format(self, text: str) -> bool:
#         count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
#         return count >= 3

#     def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
#         chunks = []
#         words = content.split()
#         if len(words) <= chunk_size:
#             return [{"content": content, "chunk_id": "chunk_0"}]
#         for i in range(0, len(words), chunk_size - overlap):
#             chunk_words = words[i:i + chunk_size]
#             chunk_text = " ".join(chunk_words)
#             if chunk_text.strip():
#                 chunks.append({
#                     "content": chunk_text,
#                     "chunk_id": f"chunk_{i // chunk_size}"
#                 })
#         return chunks

#     def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, 
#                                 elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Prepare all extracted elements for database storage"""
#         documents_batch = []
        
#         # First, extract sections from text elements
#         text_elements = [e for e in elements if e["type"] in ["CompositeElement", "TextElement"]]
#         sections = self.extract_sections(text_elements)
        
#         # Process text sections
#         for section in sections:
#             if "chunks" not in section:
#                 section["chunks"] = self.chunk_content(section["content"])
#             for chunk in section["chunks"]:
#                 doc_id = str(uuid.uuid4())
#                 metadata = {
#                     "pdf_index": pdf_index,
#                     "pdf_name": pdf_name,
#                     "section": section["section"],
#                     "page_start": section["page_start"],
#                     "page_end": section["page_end"],
#                     "is_fda": section.get("is_fda", False),
#                     "content_type": self._classify_content_type(chunk["content"]),
#                     "has_tables": False,
#                     "has_images": False,
#                     "doc_type": "text",
#                     "citation": f"Page {section['page_start']}-{section['page_end']}, {section['section']}"
#                 }
                
#                 documents_batch.append({
#                     "id": doc_id,
#                     "content": chunk["content"],
#                     "metadata": self._ensure_chromadb_compatible(metadata)
#                 })
        
#         # Process tables
#         table_elements = [e for e in elements if e["type"] == "Table"]
#         for table_idx, table in enumerate(table_elements):
#             doc_id = str(uuid.uuid4())
            
#             metadata = {
#                 "pdf_index": pdf_index,
#                 "pdf_name": pdf_name,
#                 "section": "TABULAR_DATA",
#                 "page_number": table["page_number"],
#                 "is_fda": False,
#                 "content_type": "tabular",
#                 "has_tables": True,
#                 "has_images": False,
#                 "doc_type": "table",
#                 "table_id": str(uuid.uuid4()),
#                 "table_index": table_idx + 1,
#                 "citation": f"Page {table['page_number']}, Table {table_idx + 1}",
#                 "table_headers": table.get("table_data", {}).get("headers", []),
#                 "table_row_count": table.get("table_data", {}).get("row_count", 0),
#                 "table_data_sample": json.dumps(table.get("table_data", {}).get("data", [])[:2])
#             }
            
#             table_doc = {
#                 "id": doc_id,
#                 "content": table.get("text_representation", table["text"]),
#                 "metadata": self._ensure_chromadb_compatible(metadata)
#             }
#             documents_batch.append(table_doc)
        
#         # Process images
#         image_elements = [e for e in elements if e["type"] == "Image" and "image_description" in e]
#         for image_idx, image in enumerate(image_elements):
#             doc_id = str(uuid.uuid4())
            
#             metadata = {
#                 "pdf_index": pdf_index,
#                 "pdf_name": pdf_name,
#                 "section": "VISUAL_DATA",
#                 "page_number": image["page_number"],
#                 "is_fda": False,
#                 "content_type": "visual",
#                 "has_tables": False,
#                 "has_images": True,
#                 "doc_type": "image",
#                 "image_id": str(uuid.uuid4()),
#                 "image_index": image_idx + 1,
#                 "citation": f"Page {image['page_number']}, Figure {image_idx + 1}",
#                 "original_image_path": image.get("image_path", "")
#             }
            
#             image_doc = {
#                 "id": doc_id,
#                 "content": image["image_description"],
#                 "metadata": self._ensure_chromadb_compatible(metadata)
#             }
#             documents_batch.append(image_doc)
        
#         return documents_batch

#     def _classify_content_type(self, content: str) -> str:
#         content_lower = content.lower()
#         medical_keywords = {
#             'dose', 'dosage', 'mg', 'kg', 'injection', 'infusion', 'treatment',
#             'therapy', 'side effects', 'adverse', 'contraindications', 'warnings',
#             'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'
#         }
#         table_keywords = {'table', 'figure', 'chart', 'graph', 'data', 'results'}

#         if "TABLES:" in content or any(keyword in content_lower for keyword in table_keywords):
#             return "tabular"
#         elif any(keyword in content_lower for keyword in medical_keywords):
#             return "medical"
#         elif len(content_lower.split()) < 50:
#             return "metadata"
#         else:
#             return "general"
        
#     def _ensure_chromadb_compatible(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
#         """Ensure all metadata values are compatible with ChromaDB"""
#         compatible_metadata = {}
#         for key, value in metadata.items():
#             if isinstance(value, (list, tuple)):
#                 compatible_metadata[key] = json.dumps(value)
#             elif isinstance(value, (str, int, float, bool)) or value is None:
#                 compatible_metadata[key] = value
#             else:
#                 compatible_metadata[key] = str(value)
#         return compatible_metadata

#     def process_pdf_for_db(self, pdf_path: str, pdf_index: int = 0) -> List[Dict[str, Any]]:
#         """Complete PDF processing pipeline"""
#         pdf_name = os.path.basename(pdf_path)
#         print(f"\n[Processing] Starting processing for {pdf_name}...")
        
#         # Extract all elements using multiple strategies
#         elements = self.extract_elements(pdf_path)
        
#         # Count different element types
#         text_count = sum(1 for e in elements if e["type"] in ["CompositeElement", "TextElement"])
#         table_count = sum(1 for e in elements if e["type"] == "Table")
#         image_count = sum(1 for e in elements if e["type"] == "Image" and "image_description" in e)
        
#         print(f"[Processing Summary] Extracted {text_count} text elements, {table_count} tables, {image_count} images")
        
#         # Prepare documents for database
#         documents = self.prepare_documents_for_db(pdf_name, pdf_index, elements)
#         print(f"[Processing Summary] Prepared {len(documents)} documents for database storage")
        
#         # Count document types
#         text_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'text')
#         table_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'table')
#         image_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'image')
        
#         print(f"[Processing Summary] Document types - Text: {text_docs}, Tables: {table_docs}, Images: {image_docs}")
        
#         return documents



import os
import re
import uuid
import json
from typing import List, Dict, Any, Optional
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import CompositeElement, Table, Image
import google.generativeai as genai
from PIL import Image as PILImage
import io
import base64
import pdfplumber
import camelot
import pandas as pd
import warnings
import fitz  # PyMuPDF for better image extraction
import tempfile
import torch
from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration
import requests

class PDFProcessor:
    """Enhanced PDF processor with multiple extraction strategies"""
    
    def __init__(self, gemini_api_key: str = None):
        if gemini_api_key:
            self.gemini_api_key = gemini_api_key
            genai.configure(api_key=gemini_api_key)
            self.multimodal_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_api_key = None
            self.multimodal_model = None
        
        # Initialize InstructBLIP for image captioning
        self.instructblip_processor = None
        self.instructblip_model = None
        self._initialize_instructblip()
        
        # FDA sections
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
        
        # Create directory for extracted images if it doesn't exist
        self.image_output_dir = "./extracted_images"
        os.makedirs(self.image_output_dir, exist_ok=True)

    def _initialize_instructblip(self):
        """Initialize InstructBLIP model for image captioning"""
        try:
            print("Loading InstructBLIP model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.instructblip_processor = InstructBlipProcessor.from_pretrained(
                "Salesforce/instructblip-flan-t5-xl"
            )
            self.instructblip_model = InstructBlipForConditionalGeneration.from_pretrained(
                "Salesforce/instructblip-flan-t5-xl"
            ).to(device)
            
            print("InstructBLIP model loaded successfully!")
        except Exception as e:
            print(f"Failed to load InstructBLIP model: {e}")
            print("Falling back to basic image description")

    def extract_elements(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract elements using multiple strategies for better table and image detection"""
        print(f"Extracting elements from {pdf_path}...")
        
        processed_elements = []
        
        try:
            # Strategy 1: Use Unstructured.io for text and basic structure
            elements = partition_pdf(
                filename=pdf_path,
                extract_images_in_pdf=True,
                infer_table_structure=True,
                chunking_strategy="by_title",
                max_characters=4000,
                new_after_n_chars=3800,
                combine_text_under_n_chars=2000,
                image_output_dir_path=self.image_output_dir,
                strategy="hi_res",
                languages=["eng"],
            )
            
            page_number = 1
            
            for element in elements:
                element_data = {
                    "type": type(element).__name__,
                    "text": str(element),
                    "metadata": element.metadata.to_dict(),
                    "page_number": element.metadata.page_number if hasattr(element.metadata, 'page_number') else page_number
                }
                
                if hasattr(element.metadata, 'page_number'):
                    page_number = element.metadata.page_number
                
                # Handle tables
                if isinstance(element, Table):
                    element_data["table_data"] = self._structure_table_data(element)
                    element_data["text_representation"] = self._create_table_text_representation(
                        element_data["table_data"], element_data["page_number"]
                    )
                
                # Handle images
                elif isinstance(element, Image) and hasattr(element.metadata, 'image_path'):
                    element_data["image_path"] = element.metadata.image_path
                    element_data["image_description"] = self._describe_image(element_data["image_path"])
                
                processed_elements.append(element_data)
            
        except Exception as e:
            print(f"Unstructured.io extraction failed: {e}")
        
        # Strategy 2: Use pdfplumber for additional text extraction
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        processed_elements.append({
                            "type": "TextElement",
                            "text": text,
                            "metadata": {"page_number": page_num},
                            "page_number": page_num
                        })
        except Exception as e:
            print(f"PDFPlumber extraction failed: {e}")
        
        # Strategy 3: Use Camelot for table extraction (better for complex tables)
        try:
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            for i, table in enumerate(tables):
                if table.parsing_report and table.parsing_report.get('accuracy', 0) > 50:
                    table_data = {
                        "headers": table.df.iloc[0].tolist() if not table.df.empty else [],
                        "data": table.df.iloc[1:].values.tolist() if len(table.df) > 1 else [],
                        "row_count": len(table.df) - 1 if len(table.df) > 1 else 0,
                        "col_count": len(table.df.columns) if not table.df.empty else 0
                    }
                    
                    processed_elements.append({
                        "type": "Table",
                        "text": table.df.to_string(),
                        "metadata": {"page_number": table.page},
                        "page_number": table.page,
                        "table_data": table_data,
                        "text_representation": self._create_table_text_representation(table_data, table.page)
                    })
        except Exception as e:
            print(f"Camelot table extraction failed: {e}")
        
        # Strategy 4: Enhanced image extraction using PyMuPDF (fitZ)
        try:
            image_elements = self._extract_images_with_pymupdf(pdf_path)
            processed_elements.extend(image_elements)
            print(f"Extracted {len(image_elements)} images using PyMuPDF")
        except Exception as e:
            print(f"PyMuPDF image extraction failed: {e}")
        
        return processed_elements

    def _extract_images_with_pymupdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images using PyMuPDF for better image detection"""
        image_elements = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Save image to file
                    image_filename = f"image_page{page_num+1}_{img_index}.{image_ext}"
                    image_path = os.path.join(self.image_output_dir, image_filename)
                    
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    
                    # Generate description
                    image_description = self._describe_image(image_path)
                    
                    image_elements.append({
                        "type": "Image",
                        "text": f"Image on page {page_num+1}",
                        "metadata": {"page_number": page_num+1},
                        "page_number": page_num+1,
                        "image_path": image_path,
                        "image_description": image_description
                    })
        
        doc.close()
        return image_elements

    def _structure_table_data(self, table_element: Table) -> Dict[str, Any]:
        """Structure table data from Unstructured.io"""
        table_text = str(table_element)
        rows = [line.split('\t') for line in table_text.split('\n') if line.strip()]
        
        if not rows:
            return {"headers": [], "data": [], "row_count": 0, "col_count": 0}
        
        # Try to identify headers
        headers = []
        data_rows = rows
        
        if len(rows) > 1 and self._is_likely_header_row(rows[0], rows[1]):
            headers = [cell.strip() for cell in rows[0]]
            data_rows = rows[1:]
        else:
            max_cols = max(len(row) for row in rows)
            headers = [f"Column_{i+1}" for i in range(max_cols)]
        
        return {
            "headers": headers,
            "data": data_rows,
            "row_count": len(data_rows),
            "col_count": len(headers)
        }

    def _is_likely_header_row(self, row: List[str], next_row: List[str]) -> bool:
        """Determine if a row is likely a header"""
        if not any(cell.strip() for cell in row):
            return False
        
        header_indicators = 0
        total_cells = len([cell for cell in row if cell.strip()])
        
        for cell in row:
            cell_text = cell.strip()
            if not cell_text:
                continue
                
            if cell_text.isupper():
                header_indicators += 1
            elif re.search(r'[%$#&]|\b(rate|ratio|percentage|score|value)\b', cell_text.lower()):
                header_indicators += 1
            elif len(cell_text) < 20 and not cell_text.isdigit():
                header_indicators += 1
        
        # Check if next row contains data (numbers)
        data_indicators = 0
        for cell in next_row:
            if re.search(r'\d', cell):
                data_indicators += 1
                break
        
        return header_indicators > 0 and data_indicators > 0

    def _create_table_text_representation(self, table_data: Dict[str, Any], page_num: int) -> str:
        """Create comprehensive textual representation of table"""
        text_rep = f"Table from page {page_num}. "
        
        if table_data["headers"]:
            text_rep += f"Headers: {', '.join([h for h in table_data['headers'] if h])}. "
        
        # Add all data rows for comprehensive search
        for i, row in enumerate(table_data["data"]):
            if any(cell.strip() for cell in row):
                row_data = []
                for j, cell in enumerate(row):
                    if cell.strip() and j < len(table_data["headers"]):
                        header_name = table_data["headers"][j] if table_data["headers"][j] else f"Column_{j+1}"
                        row_data.append(f"{header_name}: {cell}")
                
                if row_data:
                    text_rep += f"Row {i+1}: {', '.join(row_data)}. "
        
        return text_rep.strip()

    def _describe_image(self, image_path: str) -> str:
        """Generate description for image using InstructBLIP"""
        try:
            if not os.path.exists(image_path):
                return "Image description not available - file not found"
            
            # Check if image is too small (likely decorative)
            img = PILImage.open(image_path)
            width, height = img.size
            if width < 50 or height < 50:
                return "Small decorative image - no significant content"
            
            # Use InstructBLIP for image description
            if self.instructblip_processor and self.instructblip_model:
                return self._describe_image_with_instructblip(image_path)
            
            # Fallback to Gemini if available
            elif self.multimodal_model:
                return self._describe_image_with_gemini(image_path)
            
            # Final fallback
            else:
                return self._describe_image_basic(image_path)
            
        except Exception as e:
            print(f"Error describing image {image_path}: {e}")
            return f"Medical image showing relevant information. [Image processing error: {str(e)}]"

    def _describe_image_with_instructblip(self, image_path: str) -> str:
        """Generate image description using InstructBLIP"""
        try:
            # Load and preprocess image
            image = PILImage.open(image_path).convert("RGB")
            
            # Resize if too large
            if max(image.size) > 1000:
                image.thumbnail((1000, 1000))
            
            # Prepare prompt for medical document images
            prompt = "Describe this medical image in detail. Focus on any graphs, charts, molecular structures, or medical diagrams. Include any text labels, numerical values, and the overall purpose of this image in a pharmaceutical context."
            
            # Process image and generate description
            inputs = self.instructblip_processor(images=image, text=prompt, return_tensors="pt").to(self.instructblip_model.device)
            
            outputs = self.instructblip_model.generate(
                **inputs,
                do_sample=True,
                num_beams=5,
                max_length=256,
                min_length=1,
                top_p=0.9,
                repetition_penalty=1.5
            )
            
            generated_text = self.instructblip_processor.decode(outputs[0], skip_special_tokens=True)
            return f"Medical image showing: {generated_text}"
            
        except Exception as e:
            print(f"InstructBLIP failed for {image_path}: {e}")
            # Fallback to basic description
            return self._describe_image_basic(image_path)

    def _describe_image_with_gemini(self, image_path: str) -> str:
        """Generate image description using Gemini (fallback)"""
        try:
            # Load and encode image
            with open(image_path, "rb") as img_file:
                img = PILImage.open(img_file)
                
                # Resize if too large
                if max(img.size) > 1000:
                    img.thumbnail((1000, 1000))
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
            
            prompt = """
            Analyze this medical image from a pharmaceutical document. Describe:
            1. What the image shows (graph, chart, diagram, molecular structure, etc.)
            2. Key elements and labels visible
            3. Any numerical data or trends visible
            4. The likely purpose or message of this image
            
            Provide a comprehensive description that would help understand the image content.
            """
            
            response = self.multimodal_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": base64.b64encode(img_byte_arr).decode('utf-8')}
            ])
            
            return response.text
            
        except Exception as e:
            print(f"Gemini failed for {image_path}: {e}")
            # Fallback to basic description
            return self._describe_image_basic(image_path)

    def _describe_image_basic(self, image_path: str) -> str:
        """Generate a basic description without external APIs"""
        try:
            img = PILImage.open(image_path)
            width, height = img.size
            
            # Simple analysis based on image characteristics
            if width > height * 1.5:
                aspect = "wide"
            elif height > width * 1.5:
                aspect = "tall"
            else:
                aspect = "square"
            
            # Check if it might be a graph/chart (based on color distribution)
            if img.mode == 'RGB':
                pixels = list(img.getdata())
                color_variation = len(set(pixels)) / len(pixels)
                
                if color_variation < 0.1:
                    image_type = "likely a diagram or line drawing"
                elif color_variation > 0.7:
                    image_type = "likely a complex chart or graph"
                else:
                    image_type = "medical illustration"
            else:
                image_type = "medical image"
            
            return f"{aspect} {image_type} from pharmaceutical document. Contains visual information relevant to the content."
            
        except Exception as e:
            return f"Medical image showing relevant information. [Basic processing error: {str(e)}]"

    def extract_sections(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sections from processed elements"""
        if not elements:
            return []
        
        # Combine text elements with page markers
        combined_text = ""
        current_page = 1
        
        for element in elements:
            if element["type"] in ["CompositeElement", "TextElement"] and element["text"].strip():
                if element["page_number"] != current_page:
                    combined_text += f"\n--- Page {element['page_number']} ---\n"
                    current_page = element["page_number"]
                combined_text += element["text"] + "\n"
        
        # Check if document follows FDA format
        is_fda = self.is_fda_format(combined_text)
        
        # Extract sections
        sections = []
        current_section = "INTRODUCTION"
        content = ""
        page_start = 1
        page_end = 1

        lines = combined_text.split("\n")
        for line in lines:
            # Check for page markers
            if line.startswith("--- Page "):
                if content.strip():
                    sections.append({
                        "section": current_section,
                        "content": content.strip(),
                        "page_start": page_start,
                        "page_end": page_end,
                        "is_fda": is_fda
                    })
                    content = ""
                
                match = re.match(r'--- Page (\d+) ---', line)
                if match:
                    page_start = int(match.group(1))
                    page_end = page_start
                continue

            # Check for section headers
            section_match = None
            if is_fda:
                section_match = self.fda_section_pattern.match(line.upper())
            else:
                section_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+(?:\.|:)?)\s*$', line)
                                 and len(line.strip()) < 100
                                 and not line.strip().isdigit())

            if section_match:
                if content.strip():
                    sections.append({
                        "section": current_section,
                        "content": content.strip(),
                        "page_start": page_start,
                        "page_end": page_end,
                        "is_fda": is_fda
                    })
                current_section = line.strip().upper()
                content = ""
                page_start = page_end
            else:
                content += line + "\n"
                page_end = current_page

        if content.strip():
            sections.append({
                "section": current_section,
                "content": content.strip(),
                "page_start": page_start,
                "page_end": page_end,
                "is_fda": is_fda
            })

        return sections

    def is_fda_format(self, text: str) -> bool:
        count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
        return count >= 3

    def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
        chunks = []
        words = content.split()
        if len(words) <= chunk_size:
            return [{"content": content, "chunk_id": "chunk_0"}]
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "chunk_id": f"chunk_{i // chunk_size}"
                })
        return chunks

    def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, 
                                elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare all extracted elements for database storage"""
        documents_batch = []
        
        # First, extract sections from text elements
        text_elements = [e for e in elements if e["type"] in ["CompositeElement", "TextElement"]]
        sections = self.extract_sections(text_elements)
        
        # Process text sections
        for section in sections:
            if "chunks" not in section:
                section["chunks"] = self.chunk_content(section["content"])
            for chunk in section["chunks"]:
                doc_id = str(uuid.uuid4())
                metadata = {
                    "pdf_index": pdf_index,
                    "pdf_name": pdf_name,
                    "section": section["section"],
                    "page_start": section["page_start"],
                    "page_end": section["page_end"],
                    "is_fda": section.get("is_fda", False),
                    "content_type": self._classify_content_type(chunk["content"]),
                    "has_tables": False,
                    "has_images": False,
                    "doc_type": "text",
                    "citation": f"Page {section['page_start']}-{section['page_end']}, {section['section']}"
                }
                
                documents_batch.append({
                    "id": doc_id,
                    "content": chunk["content"],
                    "metadata": self._ensure_chromadb_compatible(metadata)
                })
        
        # Process tables
        table_elements = [e for e in elements if e["type"] == "Table"]
        for table_idx, table in enumerate(table_elements):
            doc_id = str(uuid.uuid4())
            
            metadata = {
                "pdf_index": pdf_index,
                "pdf_name": pdf_name,
                "section": "TABULAR_DATA",
                "page_number": table["page_number"],
                "is_fda": False,
                "content_type": "tabular",
                "has_tables": True,
                "has_images": False,
                "doc_type": "table",
                "table_id": str(uuid.uuid4()),
                "table_index": table_idx + 1,
                "citation": f"Page {table['page_number']}, Table {table_idx + 1}",
                "table_headers": table.get("table_data", {}).get("headers", []),
                "table_row_count": table.get("table_data", {}).get("row_count", 0),
                "table_data_sample": json.dumps(table.get("table_data", {}).get("data", [])[:2])
            }
            
            table_doc = {
                "id": doc_id,
                "content": table.get("text_representation", table["text"]),
                "metadata": self._ensure_chromadb_compatible(metadata)
            }
            documents_batch.append(table_doc)
        
        # Process images
        image_elements = [e for e in elements if e["type"] == "Image" and "image_description" in e]
        for image_idx, image in enumerate(image_elements):
            doc_id = str(uuid.uuid4())
            
            metadata = {
                "pdf_index": pdf_index,
                "pdf_name": pdf_name,
                "section": "VISUAL_DATA",
                "page_number": image["page_number"],
                "is_fda": False,
                "content_type": "visual",
                "has_tables": False,
                "has_images": True,
                "doc_type": "image",
                "image_id": str(uuid.uuid4()),
                "image_index": image_idx + 1,
                "citation": f"Page {image['page_number']}, Figure {image_idx + 1}",
                "original_image_path": image.get("image_path", "")
            }
            
            image_doc = {
                "id": doc_id,
                "content": image["image_description"],
                "metadata": self._ensure_chromadb_compatible(metadata)
            }
            documents_batch.append(image_doc)
        
        return documents_batch

    def _classify_content_type(self, content: str) -> str:
        content_lower = content.lower()
        medical_keywords = {
            'dose', 'dosage', 'mg', 'kg', 'injection', 'infusion', 'treatment',
            'therapy', 'side effects', 'adverse', 'contraindications', 'warnings',
            'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'
        }
        table_keywords = {'table', 'figure', 'chart', 'graph', 'data', 'results'}

        if "TABLES:" in content or any(keyword in content_lower for keyword in table_keywords):
            return "tabular"
        elif any(keyword in content_lower for keyword in medical_keywords):
            return "medical"
        elif len(content_lower.split()) < 50:
            return "metadata"
        else:
            return "general"
        
    def _ensure_chromadb_compatible(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all metadata values are compatible with ChromaDB"""
        compatible_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (list, tuple)):
                compatible_metadata[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                compatible_metadata[key] = value
            else:
                compatible_metadata[key] = str(value)
        return compatible_metadata

    def process_pdf_for_db(self, pdf_path: str, pdf_index: int = 0) -> List[Dict[str, Any]]:
        """Complete PDF processing pipeline"""
        pdf_name = os.path.basename(pdf_path)
        print(f"\n[Processing] Starting processing for {pdf_name}...")
        
        # Extract all elements using multiple strategies
        elements = self.extract_elements(pdf_path)
        
        # Count different element types
        text_count = sum(1 for e in elements if e["type"] in ["CompositeElement", "TextElement"])
        table_count = sum(1 for e in elements if e["type"] == "Table")
        image_count = sum(1 for e in elements if e["type"] == "Image" and "image_description" in e)
        
        print(f"[Processing Summary] Extracted {text_count} text elements, {table_count} tables, {image_count} images")
        
        # Prepare documents for database
        documents = self.prepare_documents_for_db(pdf_name, pdf_index, elements)
        print(f"[Processing Summary] Prepared {len(documents)} documents for database storage")
        
        # Count document types
        text_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'text')
        table_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'table')
        image_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'image')
        
        print(f"[Processing Summary] Document types - Text: {text_docs}, Tables: {table_docs}, Images: {image_docs}")
        
        return documents