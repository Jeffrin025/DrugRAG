import os

# Load .env manually (optional if you're using python-dotenv in main.py)
from dotenv import load_dotenv
load_dotenv("C:/project/cognizant/DrugRAG/.env")

# Print the key and its length
print("GOOGLE_API_KEY:", os.environ.get("GOOGLE_API_KEY"))
print("Length of key:", len(os.environ.get("GOOGLE_API_KEY") or ""))
