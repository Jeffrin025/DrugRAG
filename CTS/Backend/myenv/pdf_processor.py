# import os
# import re
# import pdfplumber
# import camelot
# import pandas as pd
# from typing import List, Dict, Any, Tuple
# import uuid
# import json

# class PDFProcessor:
#     """Optimized PDF processor for text and table extraction with structured table storage."""

#     def __init__(self):
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

#     # ====================== Table Heuristic ======================
#     def _is_probably_table(self, rows: List[List[str]]) -> bool:
#         """
#         Heuristic check to avoid misclassifying paragraphs as tables.
#         """
#         if not rows or len(rows) < 2:
#             return False  # too small to be a table

#         # Count non-empty columns in each row
#         col_counts = [len([c for c in row if c.strip()]) for row in rows]
#         avg_cols = sum(col_counts) / len(col_counts)

#         # Rule 1: must have at least 2 average columns
#         if avg_cols < 2:
#             return False

#         # Rule 2: at least half rows should share similar column count
#         most_common = max(set(col_counts), key=col_counts.count)
#         if col_counts.count(most_common) < len(rows) / 2:
#             return False

#         return True

#     # ====================== Table Structure Processing ======================
#     def _structure_table_data(self, rows: List[List[str]], citation: str) -> Dict[str, Any]:
#         """
#         Convert table rows into a structured format with headers and data.
#         """
#         if not rows or len(rows) < 2:
#             return {
#                 "table_id": str(uuid.uuid4()),
#                 "citation": citation,
#                 "headers": [],
#                 "data": [],
#                 "text_representation": ""
#             }
        
#         # Try to identify header row (first row with non-empty values)
#         header_candidates = []
#         for i, row in enumerate(rows):
#             non_empty_count = sum(1 for cell in row if cell.strip())
#             if non_empty_count > 1:  # Header should have multiple non-empty cells
#                 header_candidates.append((i, non_empty_count))
        
#         if header_candidates:
#             # Use the row with the most non-empty cells as header
#             header_row_idx = max(header_candidates, key=lambda x: x[1])[0]
#             headers = [cell.strip() for cell in rows[header_row_idx]]
#             data_rows = rows[header_row_idx+1:]
#         else:
#             # Fallback: use first row as header
#             headers = [cell.strip() for cell in rows[0]]
#             data_rows = rows[1:]
        
#         # Clean up headers
#         headers = [h if h else f"Column_{i+1}" for i, h in enumerate(headers)]
        
#         # Process data rows
#         structured_data = []
#         for row in data_rows:
#             if any(cell.strip() for cell in row):  # Skip entirely empty rows
#                 structured_data.append([cell.strip() for cell in row])
        
#         # Create text representation for semantic search
#         text_representation = self._create_table_text_representation(headers, structured_data, citation)
        
#         return {
#             "table_id": str(uuid.uuid4()),
#             "citation": citation,
#             "headers": headers,
#             "data": structured_data,
#             "text_representation": text_representation
#         }

#     def _create_table_text_representation(self, headers: List[str], data: List[List[str]], citation: str) -> str:
#         """
#         Create a textual representation of the table for semantic search.
#         """
#         text_rep = f"Table from {citation}. "
        
#         # Add headers
#         if headers:
#             text_rep += f"Columns: {', '.join([h for h in headers if h])}. "
        
#         # Add sample data (limit to first few rows to avoid too long text)
#         max_sample_rows = min(3, len(data))
#         for i in range(max_sample_rows):
#             row_text = ", ".join([f"{headers[j] if j < len(headers) else f'Column {j+1}'}: {cell}" 
#                                 for j, cell in enumerate(data[i]) if cell.strip()])
#             if row_text:
#                 text_rep += f"Row {i+1}: {row_text}. "
        
#         if len(data) > max_sample_rows:
#             text_rep += f"Plus {len(data) - max_sample_rows} more rows. "
            
#         return text_rep.strip()

#     # ====================== PDF Extraction ======================
#     def extract_text_and_tables(self, pdf_path: str, start_page: int = 1) -> List[Dict[str, Any]]:
#         """
#         Extract text (two-column aware) and tables from PDF.
#         Handles both bordered (pdfplumber) and borderless (camelot stream) tables.
#         """
#         parsed_pages = []

#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 if page_num < start_page:
#                     continue

#                 page_data = {"page": page_num, "text": "", "tables": []}

#                 # --- Two-column text extraction ---
#                 width, height = page.width, page.height
#                 left_text = page.crop((0, 0, width / 2, height)).extract_text() or ""
#                 right_text = page.crop((width / 2, 0, width, height)).extract_text() or ""
#                 full_text = (left_text + "\n" + right_text).strip()
#                 page_data["text"] = full_text

#                 # --- Extract tables with pdfplumber (bordered) ---
#                 tables = page.extract_tables()
#                 added_table = False
#                 if tables:
#                     for t_idx, table in enumerate(tables):
#                         if table:
#                             formatted_rows = [[str(cell).replace("\n", " ").strip() if cell else "" for cell in row] for row in table]
#                             if self._is_probably_table(formatted_rows):
#                                 citation = f"Page {page_num}, Table {t_idx + 1}"
#                                 structured_table = self._structure_table_data(formatted_rows, citation)
#                                 page_data["tables"].append(structured_table)
#                                 added_table = True

#                                 # ---- DISPLAY TABLE ----
#                                 print(f"\n[Extracted Table] {citation}")
#                                 for row in formatted_rows:
#                                     print(row)
#                             else:
#                                 # Treat as paragraph text
#                                 joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
#                                 page_data["text"] += "\n" + joined_text

#                 # --- Fallback: Try Camelot (borderless) ---
#                 if not added_table:
#                     try:
#                         camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor="stream")
#                         for c_idx, c_table in enumerate(camelot_tables):
#                             df = c_table.df  # pandas DataFrame
#                             formatted_rows = df.values.tolist()
#                             if self._is_probably_table(formatted_rows):
#                                 citation = f"Page {page_num}, Camelot Table {c_idx + 1}"
#                                 structured_table = self._structure_table_data(formatted_rows, citation)
#                                 page_data["tables"].append(structured_table)

#                                 # ---- DISPLAY TABLE ----
#                                 print(f"\n[Extracted Table - Camelot] {citation}")
#                                 for row in formatted_rows:
#                                     print(row)
#                             else:
#                                 # Treat as paragraph text
#                                 joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
#                                 page_data["text"] += "\n" + joined_text
#                     except Exception as e:
#                         print(f"[Page {page_num}] Camelot extraction failed: {e}")

#                 # --- Notify if page has no extractable content ---
#                 if not full_text.strip() and not page_data["tables"]:
#                     print(f"[Page {page_num}] contains only images or non-extractable content.")

#                 parsed_pages.append(page_data)

#         return parsed_pages

#     # ====================== Backward-compatible single string method ======================
#     def extract_text_from_pdf(self, pdf_path: str, start_page: int = 1) -> str:
#         """
#         Returns combined text as a single string for backward compatibility.
#         """
#         pages_data = self.extract_text_and_tables(pdf_path, start_page=start_page)
#         full_text = "\n".join(page['text'] for page in pages_data if page['text'])
#         return full_text

#     # ====================== FDA & section parsing ======================
#     def is_fda_format(self, text: str) -> bool:
#         count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
#         return count >= 3

#     def extract_sections(self, text: str) -> List[Dict[str, Any]]:
#         sections = []
#         current_section = "INTRODUCTION"
#         content = ""
#         page_num = 1
#         is_fda = self.is_fda_format(text)

#         lines = text.split("\n")
#         for line in lines:
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
#                         "page_start": page_num,
#                         "page_end": page_num,
#                         "is_fda": is_fda
#                     })
#                 current_section = line.strip().upper()
#                 content = ""
#             else:
#                 content += line + "\n"

#         if content.strip():
#             sections.append({
#                 "section": current_section,
#                 "content": content.strip(),
#                 "page_start": page_num,
#                 "page_end": page_num,
#                 "is_fda": is_fda
#             })

#         return sections

#     # ====================== Chunking & DB prep ======================
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
#                                 sections: List[Dict[str, Any]], 
#                                 tables: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
#         """
#         Prepare documents for database storage, including both text and tables.
#         """
#         documents_batch = []
        
#         # Process text sections
#         for section in sections:
#             if "chunks" not in section:
#                 section["chunks"] = self.chunk_content(section["content"])
#             for chunk in section["chunks"]:
#                 doc_id = str(uuid.uuid4())
#                 documents_batch.append({
#                     "id": doc_id,
#                     "content": chunk["content"],
#                     "metadata": {
#                         "pdf_index": pdf_index,
#                         "pdf_name": pdf_name,
#                         "section": section["section"],
#                         "page_start": section["page_start"],
#                         "page_end": section["page_end"],
#                         "is_fda": section.get("is_fda", False),
#                         "content_type": self._classify_content_type(chunk["content"]),
#                         "has_tables": False,
#                         "doc_type": "text"
#                     }
#                 })
        
#         # Process tables
#         if tables:
#             for table in tables:
#                 doc_id = str(uuid.uuid4())
#                 documents_batch.append({
#                     "id": doc_id,
#                     "content": table["text_representation"],
#                     "metadata": {
#                         "pdf_index": pdf_index,
#                         "pdf_name": pdf_name,
#                         "section": "TABULAR_DATA",
#                         "page_start": self._extract_page_from_citation(table["citation"]),
#                         "page_end": self._extract_page_from_citation(table["citation"]),
#                         "is_fda": False,  # Tables will be associated with sections through semantic search
#                         "content_type": "tabular",
#                         "has_tables": True,
#                         "doc_type": "table",
#                         "table_id": table["table_id"],
#                         "citation": table["citation"],
#                         "table_headers": table["headers"],
#                         "table_data": json.dumps(table["data"])  # Store as JSON string
#                     }
#                 })
        
#         return documents_batch

#     def _extract_page_from_citation(self, citation: str) -> int:
#         """Extract page number from citation string."""
#         match = re.search(r'Page (\d+)', citation)
#         return int(match.group(1)) if match else 1

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

#     # ====================== Main processing method ======================
#     def process_pdf_for_db(self, pdf_path: str, pdf_index: int = 0) -> List[Dict[str, Any]]:
#         """
#         Complete PDF processing pipeline for database storage.
#         """
#         pdf_name = os.path.basename(pdf_path)
        
#         # Extract text and tables
#         pages_data = self.extract_text_and_tables(pdf_path)
        
#         # Combine all text for section parsing
#         full_text = "\n".join(page['text'] for page in pages_data if page['text'])
        
#         # Extract all tables from all pages
#         all_tables = []
#         for page in pages_data:
#             all_tables.extend(page['tables'])
        
#         # Extract sections from text
#         sections = self.extract_sections(full_text)
        
#         # Prepare documents for database
#         documents = self.prepare_documents_for_db(pdf_name, pdf_index, sections, all_tables)
        
#         return documents


# # ====================== ChromaDB Integration ======================
# def add_to_chroma_db(documents: List[Dict[str, Any]], collection):
#     """
#     Add processed documents to ChromaDB collection.
#     """
#     ids = [doc["id"] for doc in documents]
#     contents = [doc["content"] for doc in documents]
#     metadatas = [doc["metadata"] for doc in documents]
    
#     collection.add(
#         ids=ids,
#         documents=contents,
#         metadatas=metadatas
#     )
    
#     return len(documents)


import os
import re
import pdfplumber
import camelot
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import uuid
import json

class PDFProcessor:
    """Optimized PDF processor for text and table extraction with structured table storage."""

    def __init__(self):
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

    # ====================== IMPROVED Table Heuristic ======================
    def _is_probably_table(self, rows: List[List[str]]) -> bool:
        """
        Improved heuristic check to avoid misclassifying paragraphs as tables.
        """
        if not rows or len(rows) < 2:
            return False

        # Check if this looks like a paragraph masquerading as a table
        if len(rows) == 1 or (len(rows) == 2 and len([c for c in rows[1] if c.strip()]) == 0):
            return False

        # Count non-empty columns in each row
        col_counts = [len([c for c in row if c.strip()]) for row in rows]
        avg_cols = sum(col_counts) / len(col_counts)

        # Rule 1: must have at least 2 average columns
        if avg_cols < 2:
            return False

        # Rule 2: at least 60% of rows should share similar column count
        most_common = max(set(col_counts), key=col_counts.count)
        if col_counts.count(most_common) < len(rows) * 0.6:
            return False

        return True

    def _is_likely_header_row(self, row: List[str], next_row: Optional[List[str]] = None) -> bool:
        """
        Determine if a row is likely a header based on content patterns.
        """
        if not any(cell.strip() for cell in row):
            return False
        
        # Check for header-like patterns
        header_indicators = 0
        total_cells = len([cell for cell in row if cell.strip()])
        
        for cell in row:
            cell_text = cell.strip()
            if not cell_text:
                continue
                
            # Header indicators
            if cell_text.isupper():  # All caps often indicates headers
                header_indicators += 1
            elif re.search(r'[%$#&]|\b(rate|ratio|percentage|score|value)\b', cell_text.lower()):
                header_indicators += 1  # Contains special chars or measurement terms
            elif len(cell_text) < 20 and not cell_text.isdigit():  # Short, non-numeric text
                header_indicators += 1
        
        # If next row is provided, check if it contains data (numbers)
        if next_row:
            data_indicators = 0
            for cell in next_row:
                if re.search(r'\d', cell):  # Contains numbers
                    data_indicators += 1
                    break
            
            if data_indicators > 0 and header_indicators > 0:
                return True
        
        # If no next row, use threshold
        return header_indicators / total_cells > 0.5 if total_cells > 0 else False

    # ====================== IMPROVED Table Structure Processing ======================
    def _structure_table_data(self, rows: List[List[str]], citation: str) -> Dict[str, Any]:
        """
        Improved table structure detection with better header identification.
        """
        if not rows or len(rows) < 2:
            return {
                "table_id": str(uuid.uuid4()),
                "citation": citation,
                "headers": [],
                "data": [],
                "text_representation": "",
                "raw_rows": rows  # Store original rows for reference
            }
        
        # Try to identify header row using improved logic
        header_row_idx = 0  # Default to first row
        found_header = False
        
        # Check if first row looks like a header
        if len(rows) > 1 and self._is_likely_header_row(rows[0], rows[1]):
            header_row_idx = 0
            found_header = True
        else:
            # Look for a header row in the first few rows
            for i in range(min(3, len(rows) - 1)):
                if self._is_likely_header_row(rows[i], rows[i + 1]):
                    header_row_idx = i
                    found_header = True
                    break
        
        if found_header:
            headers = [cell.strip() for cell in rows[header_row_idx]]
            data_rows = rows[header_row_idx + 1:]
        else:
            # No clear header found, use generic column names
            max_cols = max(len(row) for row in rows)
            headers = [f"Column_{i+1}" for i in range(max_cols)]
            data_rows = rows  # Use all rows as data
        
        # Clean up headers - ensure we have headers for all columns
        max_data_cols = max((len(row) for row in data_rows), default=0)
        if len(headers) < max_data_cols:
            headers.extend([f"Column_{i+1}" for i in range(len(headers), max_data_cols)])
        
        # Process data rows
        structured_data = []
        for row in data_rows:
            if any(cell.strip() for cell in row):  # Skip entirely empty rows
                # Ensure row has same number of columns as headers
                padded_row = row + [''] * (len(headers) - len(row))
                structured_data.append([cell.strip() for cell in padded_row])
        
        # Create text representation for semantic search
        text_representation = self._create_table_text_representation(headers, structured_data, citation)
        
        return {
            "table_id": str(uuid.uuid4()),
            "citation": citation,
            "headers": headers,
            "data": structured_data,
            "text_representation": text_representation,
            "raw_rows": rows  # Store original for debugging
        }

    def _create_table_text_representation(self, headers: List[str], data: List[List[str]], citation: str) -> str:
        """
        Create a textual representation of the table for semantic search.
        """
        text_rep = f"Table from {citation}. "
        
        # Add headers
        if headers:
            text_rep += f"Columns: {', '.join([h for h in headers if h])}. "
        
        # Add sample data (limit to first few rows to avoid too long text)
        max_sample_rows = min(3, len(data))
        for i in range(max_sample_rows):
            row_text = ", ".join([f"{headers[j] if j < len(headers) else f'Column {j+1}'}: {cell}" 
                                for j, cell in enumerate(data[i]) if cell.strip()])
            if row_text:
                text_rep += f"Row {i+1}: {row_text}. "
        
        if len(data) > max_sample_rows:
            text_rep += f"Plus {len(data) - max_sample_rows} more rows. "
            
        return text_rep.strip()

    # ====================== IMPROVED PDF Extraction ======================
    def extract_text_and_tables(self, pdf_path: str, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Extract text and tables with improved table detection.
        """
        parsed_pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                if page_num < start_page:
                    continue

                page_data = {"page": page_num, "text": "", "tables": []}

                # --- Two-column text extraction ---
                width, height = page.width, page.height
                left_text = page.crop((0, 0, width / 2, height)).extract_text() or ""
                right_text = page.crop((width / 2, 0, width, height)).extract_text() or ""
                full_text = (left_text + "\n" + right_text).strip()
                page_data["text"] = full_text

                # --- Extract tables with pdfplumber (bordered) ---
                tables = page.extract_tables()
                added_table = False
                
                if tables:
                    for t_idx, table in enumerate(tables):
                        if table:
                            formatted_rows = [[str(cell).replace("\n", " ").strip() if cell else "" for cell in row] for row in table]
                            if self._is_probably_table(formatted_rows):
                                citation = f"Page {page_num}, Table {t_idx + 1}"
                                structured_table = self._structure_table_data(formatted_rows, citation)
                                page_data["tables"].append(structured_table)
                                added_table = True

                                # ---- DISPLAY TABLE ----
                                print(f"\n[Extracted Table] {citation}")
                                print(f"Headers: {structured_table['headers']}")
                                for i, row in enumerate(structured_table['data']):
                                    print(f"Row {i}: {row}")
                                    
                                # Print structured table information
                                print(f"\n[Table Structure] Header row identified: {structured_table['headers']}")
                                print(f"[Table Structure] Number of data rows: {len(structured_table['data'])}")
                                print(f"[Table Structure] Text representation: {structured_table['text_representation'][:200]}...")
                            else:
                                # Treat as paragraph text
                                joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
                                page_data["text"] += "\n" + joined_text

                # --- Fallback: Try Camelot (borderless) ---
                if not added_table:
                    try:
                        camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor="stream")
                        for c_idx, c_table in enumerate(camelot_tables):
                            df = c_table.df
                            formatted_rows = df.values.tolist()
                            
                            if self._is_probably_table(formatted_rows):
                                citation = f"Page {page_num}, Camelot Table {c_idx + 1}"
                                structured_table = self._structure_table_data(formatted_rows, citation)
                                page_data["tables"].append(structured_table)

                                # ---- DISPLAY TABLE ----
                                print(f"\n[Extracted Table - Camelot] {citation}")
                                print(f"Headers: {structured_table['headers']}")
                                for i, row in enumerate(structured_table['data']):
                                    print(f"Row {i}: {row}")
                                    
                                # Print structured table information
                                print(f"\n[Table Structure] Header row identified: {structured_table['headers']}")
                                print(f"[Table Structure] Number of data rows: {len(structured_table['data'])}")
                                print(f"[Table Structure] Text representation: {structured_table['text_representation']}")
                            else:
                                # Treat as paragraph text
                                joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
                                page_data["text"] += "\n" + joined_text
                    except Exception as e:
                        print(f"[Page {page_num}] Camelot extraction failed: {e}")

                # --- Notify if page has no extractable content ---
                if not full_text.strip() and not page_data["tables"]:
                    print(f"[Page {page_num}] contains only images or non-extractable content.")

                parsed_pages.append(page_data)

        return parsed_pages

    # ====================== Backward-compatible single string method ======================
    def extract_text_from_pdf(self, pdf_path: str, start_page: int = 1) -> str:
        """
        Returns combined text as a single string for backward compatibility.
        """
        pages_data = self.extract_text_and_tables(pdf_path, start_page=start_page)
        full_text = "\n".join(page['text'] for page in pages_data if page['text'])
        return full_text

    # ====================== FDA & section parsing ======================
    def is_fda_format(self, text: str) -> bool:
        count = sum(1 for section in self.fda_sections if section.upper() in text.upper())
        return count >= 3

    def extract_sections(self, text: str) -> List[Dict[str, Any]]:
        sections = []
        current_section = "INTRODUCTION"
        content = ""
        page_num = 1
        is_fda = self.is_fda_format(text)

        lines = text.split("\n")
        for line in lines:
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
                        "page_start": page_num,
                        "page_end": page_num,
                        "is_fda": is_fda
                    })
                current_section = line.strip().upper()
                content = ""
            else:
                content += line + "\n"

        if content.strip():
            sections.append({
                "section": current_section,
                "content": content.strip(),
                "page_start": page_num,
                "page_end": page_num,
                "is_fda": is_fda
            })

        return sections

    # ====================== Chunking & DB prep ======================
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

    # ====================== Database Preparation ======================
    def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, 
                                sections: List[Dict[str, Any]], 
                                tables: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Prepare documents for database storage, including both text and tables.
        """
        documents_batch = []
        
        # Process text sections
        for section in sections:
            if "chunks" not in section:
                section["chunks"] = self.chunk_content(section["content"])
            for chunk in section["chunks"]:
                doc_id = str(uuid.uuid4())
                documents_batch.append({
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
                        "has_tables": False,
                        "doc_type": "text"
                    }
                })
        
        # Process tables with improved metadata
        if tables:
            print(f"\n[Database Preparation] Preparing {len(tables)} tables for database storage...")
            for table in tables:
                doc_id = str(uuid.uuid4())
                table_doc = {
                    "id": doc_id,
                    "content": table["text_representation"],
                    "metadata": {
                        "pdf_index": pdf_index,
                        "pdf_name": pdf_name,
                        "section": "TABULAR_DATA",
                        "page_start": self._extract_page_from_citation(table["citation"]),
                        "page_end": self._extract_page_from_citation(table["citation"]),
                        "is_fda": False,
                        "content_type": "tabular",
                        "has_tables": True,
                        "doc_type": "table",
                        "table_id": table["table_id"],
                        "citation": table["citation"],
                        "table_headers": table["headers"],
                        "table_data": json.dumps(table["data"]),
                        "table_data_full": json.dumps(table["raw_rows"])  # Store original table structure
                    }
                }
                documents_batch.append(table_doc)
                
                # Print table document information
                print(f"\n[Table Document] ID: {doc_id}")
                print(f"[Table Document] Citation: {table['citation']}")
                print(f"[Table Document] Headers: {table['headers']}")
                print(f"[Table Document] Data rows: {len(table['data'])}")
                print(f"[Table Document] Content preview: {table_doc['content']}...")
        
        return documents_batch

    def _extract_page_from_citation(self, citation: str) -> int:
        """Extract page number from citation string."""
        match = re.search(r'Page (\d+)', citation)
        return int(match.group(1)) if match else 1

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

    # ====================== Main processing method ======================
    def process_pdf_for_db(self, pdf_path: str, pdf_index: int = 0) -> List[Dict[str, Any]]:
        """
        Complete PDF processing pipeline for database storage.
        """
        pdf_name = os.path.basename(pdf_path)
        print(f"\n[Processing] Starting processing for {pdf_name}...")
        
        # Extract text and tables
        pages_data = self.extract_text_and_tables(pdf_path)
        
        # Combine all text for section parsing
        full_text = "\n".join(page['text'] for page in pages_data if page['text'])
        
        # Extract all tables from all pages
        all_tables = []
        for page in pages_data:
            all_tables.extend(page['tables'])
        
        print(f"\n[Processing Summary] Extracted {len(all_tables)} tables from {len(pages_data)} pages")
        
        # Extract sections from text
        sections = self.extract_sections(full_text)
        print(f"[Processing Summary] Identified {len(sections)} sections in the document")
        
        # Prepare documents for database
        documents = self.prepare_documents_for_db(pdf_name, pdf_index, sections, all_tables)
        print(f"[Processing Summary] Prepared {len(documents)} documents for database storage")
        
        # Count document types
        text_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'text')
        table_docs = sum(1 for doc in documents if doc['metadata']['doc_type'] == 'table')
        print(f"[Processing Summary] Document types - Text: {text_docs}, Tables: {table_docs}")
        
        return documents


# ====================== ChromaDB Integration ======================
def add_to_chroma_db(documents: List[Dict[str, Any]], collection):
    """
    Add processed documents to ChromaDB collection.
    """
    ids = [doc["id"] for doc in documents]
    contents = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    
    print(f"\n[Database] Adding {len(documents)} documents to ChromaDB collection...")
    
    # Print sample of what's being added to the database
    print(f"[Database Sample] First document content (first 200 chars): {contents[0][:200]}...")
    print(f"[Database Sample] First document metadata keys: {list(metadatas[0].keys())}")
    
    collection.add(
        ids=ids,
        documents=contents,
        metadatas=metadatas
    )
    
    print(f"[Database] Successfully added {len(documents)} documents to the collection")
    
    return len(documents)