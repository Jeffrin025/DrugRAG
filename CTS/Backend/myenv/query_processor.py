import os
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except Exception:
    genai = None

class QueryProcessor:
    """Generate answers from retrieved chunks with Gemini (if available) or fallback."""

    def __init__(self, gemini_api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.use_gemini = False
        self.model = None
        if gemini_api_key and genai:
            try:
                genai.configure(api_key=gemini_api_key)
                self.model = genai.GenerativeModel(model_name)
                self.use_gemini = True
            except Exception as e:
                print(f"Gemini disabled (init failed): {e}")

    def analyze_query(self, query: str) -> Dict[str, Any]:
        ql = query.lower()
        drug_keywords = {'orencia', 'simponi', 'aria', 'humira', 'enbrel', 'remicade', 'keytruda'}
        mentioned = [d for d in drug_keywords if d in ql]

        medical_keywords = {'dose','dosage','side effect','adverse','warning','contraindication',
                            'interaction','administration','treatment','safety','efficacy',
                            'pharmacokinetics','indication'}
        is_medical = any(k in ql for k in medical_keywords)

        return {
            "mentioned_drugs": mentioned,
            "is_medical_query": is_medical,
            "pdf_filter_contains": mentioned[0] if mentioned else None,
            "is_fda_specific": is_medical,
        }

    def format_retrieved_info(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant information found in the documents."
        out = []
        for i, c in enumerate(chunks, 1):
            citation = f"Source: [PDF: {c['pdf_name']}"
            if c.get('is_fda'):
                citation += f", Section: {c.get('section','')}"
            ps = c.get('page_start'); pe = c.get('page_end')
            if ps and pe:
                citation += f", Pages {ps}-{pe}]"
            else:
                citation += "]"
            out.append(f"{i}. {citation}\n{c['chunk_text']}")
        return "\n\n".join(out)

    def answer(self, user_query: str, retrieved_info: str) -> str:
        if not self.use_gemini:
            # Fallback: deterministic, grounded answer from retrieved info only.
            if "No relevant information" in retrieved_info:
                return "Not found in prescribing information."
            return (
                f"Answer (from retrieved documents only):\n\n"
                f"{retrieved_info}\n\n"
                f"(Note: This answer is compiled directly from the retrieved label text above.)"
            )

        prompt = f"""
You are a medical information specialist. Answer ONLY using the retrieved information below.

USER QUESTION:
{user_query}

RETRIEVED INFORMATION (WITH CITATIONS):
{retrieved_info}

REQUIREMENTS:
- Use only the retrieved information. Do not add outside facts.
- Be precise and concise.
- Every factual statement must be backed by the included citations, keeping the format intact.
- If the info is not present, reply exactly: "Not found in prescribing information."

ANSWER:
"""
        try:
            resp = self.model.generate_content(prompt)
            return resp.text or "Not found in prescribing information."
        except Exception as e:
            return f"Error generating response (Gemini): {e}"
