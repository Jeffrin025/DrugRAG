import re
import uuid
from typing import List, Dict, Any
import PyPDF2

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
            r'^\s*(' + '|'.join(re.escape(s) for s in self.fda_sections) + r')\s*$',
            re.IGNORECASE | re.MULTILINE
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file with robust error handling"""
        text = ""
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text += f"--- Page {i+1} ---\n{page_text}\n\n"
                    else:
                        text += f"--- Page {i+1} ---\n[Content not extractable]\n\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""
        return text

    def is_fda_format(self, text: str) -> bool:
        fda_section_count = sum(1 for s in self.fda_sections if s.upper() in text.upper())
        return fda_section_count >= 3

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
                m = re.match(r"--- Page (\d+) ---", line)
                if m:
                    page_num = int(m.group(1))
                continue

            header_match = None
            if is_fda:
                header_match = self.fda_section_pattern.match(line.upper())
            else:
                header_match = (re.match(r'^\s*([A-Z][A-Z\s\-]+[:.]?)\s*$', line)
                                and len(line.strip()) < 100
                                and not line.strip().isdigit())

            if header_match:
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

    def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
        chunks = []
        words = content.split()
        if len(words) <= chunk_size:
            return [{"content": content, "chunk_id": "chunk_0"}]

        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            piece = " ".join(words[i:i + chunk_size]).strip()
            if piece:
                chunks.append({"content": piece, "chunk_id": f"chunk_{i//chunk_size}"})
        return chunks

    def _classify_content_type(self, content: str) -> str:
        txt = content.lower()
        medical = {'dose', 'dosage', 'mg', 'injection', 'infusion', 'treatment',
                   'side effects', 'adverse', 'contraindications', 'warnings',
                   'patient', 'clinical', 'studies', 'efficacy', 'safety', 'medical'}
        tabular = {'table', 'figure', 'chart', 'graph', 'data', 'results'}
        if any(k in txt for k in medical):
            return "medical"
        if any(k in txt for k in tabular):
            return "tabular"
        if len(txt.split()) < 50:
            return "metadata"
        return "general"

    def prepare_documents_for_db(self, pdf_name: str, pdf_index: int, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        docs = []
        for section in sections:
            for chunk in section.get("chunks", []):
                docs.append({
                    "id": str(uuid.uuid4()),
                    "content": chunk["content"],
                    "metadata": {
                        "pdf_index": pdf_index,
                        "pdf_name": pdf_name,
                        "pdf_name_lc": pdf_name.lower(),
                        "section": section["section"],
                        "page_start": section["page_start"],
                        "page_end": section["page_end"],
                        "is_fda": section.get("is_fda", False),
                        "content_type": self._classify_content_type(chunk["content"])
                    }
                })
        return docs
