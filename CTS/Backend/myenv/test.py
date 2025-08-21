# Install requirements first:
# pip install langchain langchain-community chromadb sentence-transformers

import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceHub  # (optional if you want local LLM)

# -------------------------
# 1. Parsed JSON data
# -------------------------
parsed_data = {
  "drug_name": "Rinvoq (Upadacitinib)",
  "indications": {
    "rheumatoid_arthritis": "Adults with moderately to severely active RA with inadequate TNF blocker response",
    "crohns_disease": "Adults with moderately to severely active Crohn’s disease",
    "atopic_dermatitis": "Adults & pediatric patients (≥12 yrs) with refractory, moderate-to-severe AD"
  },
  "dosage": {
    "rheumatoid_arthritis": "15 mg once daily",
    "crohns_disease_induction": "45 mg once daily for 12 weeks",
    "crohns_disease_maintenance": "15 mg once daily (30 mg for severe cases)"
  },
  "contraindications": [
    "Known hypersensitivity to upadacitinib",
    "Severe hepatic impairment"
  ],
  "warnings": [
    "Serious infections (TB, herpes zoster, fungal infections)",
    "Malignancies (lymphoma, lung cancers)",
    "Cardiovascular events (MACE)",
    "Thrombosis"
  ],
  "adverse_reactions": {
    "rheumatoid_arthritis": ["URTI (13.5%)", "Nausea (3.5%)", "Cough (2.2%)"],
    "giant_cell_arteritis": ["Headache (≥5%)", "Fatigue", "Peripheral edema"]
  },
  "drug_interactions": {
    "strong_cyp3a4_inhibitors": "Dosage modifications required",
    "strong_cyp3a4_inducers": "Not recommended"
  }
}

# -------------------------
# 2. Flatten JSON into docs
# -------------------------
docs = []
ids = []

for section, content in parsed_data.items():
    if isinstance(content, dict):
        for k, v in content.items():
            docs.append(f"{section} - {k}: {v}")
            ids.append(f"{section}_{k}")
    elif isinstance(content, list):
        for idx, v in enumerate(content):
            docs.append(f"{section}[{idx}]: {v}")
            ids.append(f"{section}_{idx}")
    else:
        docs.append(f"{section}: {content}")
        ids.append(section)

# -------------------------
# 3. Embeddings + Chroma DB
# -------------------------
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = Chroma.from_texts(
    texts=docs,
    embedding=embeddings,
    ids=ids,
    collection_name="drug_info",
    persist_directory="./chroma_store"
)

vectorstore.persist()

# -------------------------
# 4. Retriever (RAG pipeline)
# -------------------------
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# For now, we’ll just print retrieved docs instead of calling an LLM
def rag_query(query: str):
    results = retriever.get_relevant_documents(query)
    print(f"\nQ: {query}")
    for i, doc in enumerate(results, 1):
        print(f" -> {i}. {doc.page_content}")

# -------------------------
# 5. Example Queries
# -------------------------
rag_query("What is the dosage for rheumatoid_arthritis?")
rag_query("What warnings should be given to patients?")
rag_query("What are the contraindications of Rinvoq?")
