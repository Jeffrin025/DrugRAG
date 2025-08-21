import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
env_path = "C:/project/cognizant/DrugRAG/.env"
load_dotenv(env_path)

# Get the API key
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found")
    exit()

print("GOOGLE_API_KEY found! Length:", len(api_key))

# Configure the client
genai.configure(api_key=api_key)

# List available models
print("Available models:")
for model in genai.list_models():  # iterate over Model objects
    print("-", model.name)
