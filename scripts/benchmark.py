import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

print("--- STARTING TIMED BENCHMARK ---")

# Step 1: SQL
t0 = time.time()
import pyodbc
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;DATABASE=master;"
    "UID=USR_FDE_RO;PWD=AgentPassword2026!;"
    "Encrypt=no;TrustServerCertificate=yes;"
)
cur = conn.cursor()
cur.execute("SELECT TOP 3 * FROM FDE_VIEWS.VW_ACTIVE_FLEET")
rows = cur.fetchall()
cur.close()
conn.close()
print(f"✅ 1. SQL Query Time: {time.time()-t0:.2f}s (Fetched {len(rows)} rows)")

# Step 2: Weather API
t1 = time.time()
from src.agent_tools import fetch_corridor_conditions
w = fetch_corridor_conditions.invoke({"latitude": 37.77, "longitude": -122.41})
print(f"✅ 2. Weather REST API Time: {time.time()-t1:.2f}s")

# Step 3: Pinecone RAG
t2 = time.time()
from src.agent_tools import search_compliance_sop
p = search_compliance_sop.invoke({"query": "temperature threshold frozen vaccines"})
print(f"✅ 3. Pinecone Vector Retrieval Time: {time.time()-t2:.2f}s")

# Step 4: Gemini LLM Direct
t3 = time.time()
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
res = llm.invoke("Reply with 'READY'")
print(f"✅ 4. Gemini Direct Call Time: {time.time()-t3:.2f}s (Response: {res.content[:20]})")

# Step 5: Full LangGraph Orchestrator
t4 = time.time()
from src.orchestrator import fde_agent
from langchain_core.messages import HumanMessage
thread_config = {"configurable": {"thread_id": "benchmark_run"}}
agent_res = fde_agent.invoke({
    "messages": [HumanMessage(content="Check telemetry for one high risk vehicle and summarize.")]
}, config=thread_config)
print(f"✅ 5. Full LangGraph End-to-End Time: {time.time()-t4:.2f}s")

print("--- BENCHMARK COMPLETE ---")
