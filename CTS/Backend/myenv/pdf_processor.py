import os
import re
import pdfplumber
import camelot
from typing import List, Dict, Any
import uuid

class PDFProcessor:
    """Optimized PDF processor for text and table extraction, handling both bordered & borderless tables, avoiding false positives."""

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

    # ====================== Table Heuristic ======================
    def _is_probably_table(self, rows: List[List[str]]) -> bool:
        """
        Heuristic check to avoid misclassifying paragraphs as tables.
        """
        if not rows or len(rows) < 2:
            return False  # too small to be a table

        # Count non-empty columns in each row
        col_counts = [len([c for c in row if c.strip()]) for row in rows]
        avg_cols = sum(col_counts) / len(col_counts)

        # Rule 1: must have at least 2 average columns
        if avg_cols < 2:
            return False

        # Rule 2: at least half rows should share similar column count
        most_common = max(set(col_counts), key=col_counts.count)
        if col_counts.count(most_common) < len(rows) / 2:
            return False

        return True

    # ====================== PDF Extraction ======================
    def extract_text_and_tables(self, pdf_path: str, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Extract text (two-column aware) and tables from PDF.
        Handles both bordered (pdfplumber) and borderless (camelot stream) tables.
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
                                table_dict = {
                                    "table_id": f"{page_num}_{t_idx + 1}",
                                    "citation": f"Page {page_num}, Table {t_idx + 1}",
                                    "rows": formatted_rows
                                }
                                page_data["tables"].append(table_dict)
                                added_table = True

                                # ---- DISPLAY TABLE ----
                                print(f"\n[Extracted Table] {table_dict['citation']}")
                                for row in formatted_rows:
                                    print(row)
                            else:
                                # Treat as paragraph text
                                joined_text = " ".join(row[0] for row in formatted_rows if row and row[0])
                                page_data["text"] += "\n" + joined_text

                # --- Fallback: Try Camelot (borderless) ---
                if not added_table:
                    try:
                        camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor="stream")
                        for c_idx, c_table in enumerate(camelot_tables):
                            df = c_table.df  # pandas DataFrame
                            formatted_rows = df.values.tolist()
                            if self._is_probably_table(formatted_rows):
                                table_dict = {
                                    "table_id": f"{page_num}_c{c_idx + 1}",
                                    "citation": f"Page {page_num}, Camelot Table {c_idx + 1}",
                                    "rows": formatted_rows
                                }
                                page_data["tables"].append(table_dict)

                                # ---- DISPLAY TABLE ----
                                print(f"\n[Extracted Table - Camelot] {table_dict['citation']}")
                                for row in formatted_rows:
                                    print(row)
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

    def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        documents_batch = []
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
                        "has_tables": "TABLES:" in chunk["content"]
                    }
                })
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
