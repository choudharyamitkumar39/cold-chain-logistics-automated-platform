import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("--- AVAILABLE MODELS FOR THIS KEY ---")
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        print(f"Model: {m.name} | Display: {m.display_name}")
