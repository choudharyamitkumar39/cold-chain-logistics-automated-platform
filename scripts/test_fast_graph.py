import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")
os.environ["GEMINI_MODEL"] = "gemini-flash-lite-latest"

print("--- TESTING FULL LANGGRAPH WITH gemini-flash-lite-latest ---")
t0 = time.time()
from src.orchestrator import fde_agent
from langchain_core.messages import HumanMessage

thread_config = {"configurable": {"thread_id": "test_fast_model"}}
agent_res = fde_agent.invoke({
    "messages": [HumanMessage(content="Check telemetry for recent high risk vehicles and summarize in one sentence.")]
}, config=thread_config)

elapsed = time.time() - t0
print(f"🎉 Full End-to-End LangGraph Time: {elapsed:.2f}s")
print("Response:")
latest_msg = agent_res["messages"][-1]
print(latest_msg.content)
