import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

load_dotenv()

@tool
def sample_tool(arg: str) -> str:
    """A test tool"""
    return f"tool result for {arg}"

models_to_test = [
    "gemini-flash-latest",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]

print("--- TESTING GEMINI CHAT MODELS WITH TOOL BINDING ---")
for m in models_to_test:
    try:
        t0 = time.time()
        llm = ChatGoogleGenerativeAI(
            model=m,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        llm_with_tool = llm.bind_tools([sample_tool])
        res = llm_with_tool.invoke("Call sample_tool with arg 'hello'")
        elapsed = time.time() - t0
        print(f"✅ {m}: SUCCESS ({elapsed:.2f}s) -> tool_calls: {len(getattr(res, 'tool_calls', []))}")
    except Exception as e:
        print(f"❌ {m}: FAILED -> {type(e).__name__}: {str(e)[:100]}")
