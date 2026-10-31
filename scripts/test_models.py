import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

candidate_models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.5-pro",
    "gemini-3.8-flash"
]

print("--- TESTING GEMINI MODELS ---")
for m in candidate_models:
    try:
        t0 = time.time()
        res = client.models.generate_content(model=m, contents="Say OK in one word")
        elapsed = time.time() - t0
        print(f"✅ {m}: SUCCESS ({elapsed:.2f}s) -> {res.text.strip()}")
    except Exception as e:
        print(f"❌ {m}: FAILED -> {type(e).__name__}: {str(e)[:120]}")
