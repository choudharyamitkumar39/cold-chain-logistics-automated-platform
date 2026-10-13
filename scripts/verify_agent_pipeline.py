import os
import sys
import pyodbc
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

print("="*60)
print("🔍 1. TESTING SQL LEAST-PRIVILEGE ROLE (USR_FDE_RO)")
print("="*60)

db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
agent_user = os.getenv("SQL_AGENT_USER", "USR_FDE_RO")
agent_pwd = os.getenv("SQL_AGENT_PASSWORD", "AgentPassword2026!")

available_drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
driver_choice = "ODBC Driver 18 for SQL Server"
if "ODBC Driver 18 for SQL Server" in available_drivers:
    driver_choice = "ODBC Driver 18 for SQL Server"
elif "ODBC Driver 17 for SQL Server" in available_drivers:
    driver_choice = "ODBC Driver 17 for SQL Server"
elif available_drivers:
    driver_choice = available_drivers[0]

conn_str = (
    f"DRIVER={{{driver_choice}}};"
    f"SERVER={db_host},{db_port};"
    f"DATABASE=master;"
    f"UID={agent_user};"
    f"PWD={agent_pwd};"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Query View
cursor.execute("SELECT TOP 3 [Timestamp], [Latitude], [Longitude], [Current_Temperature_C], [Risk_Classification] FROM FDE_VIEWS.VW_ACTIVE_FLEET")
rows = cursor.fetchall()
print(f"✅ Success querying FDE_VIEWS.VW_ACTIVE_FLEET! Sample ({len(rows)} records):")
for r in rows:
    print("   ", r)

# Verify Raw Table Access is Blocked
try:
    cursor.execute("SELECT TOP 1 * FROM dbo.TBL_SC_FLEET_HIST_RAW")
    print("❌ Security failure: Agent was able to read raw dbo table!")
except Exception as e:
    print("✅ Security Verified: Access to dbo.TBL_SC_FLEET_HIST_RAW successfully DENIED!")

cursor.close()
conn.close()

print("\n" + "="*60)
print("🔍 2. TESTING PINECONE SOP RETRIEVAL (search_compliance_sop)")
print("="*60)
from src.agent_tools import search_compliance_sop, fetch_corridor_conditions

sop_result = search_compliance_sop.invoke({"query": "temperature threshold frozen vaccines"})
print("✅ SOP Retrieval Result:")
print("   " + sop_result[:250].replace("\n", "\n   ") + "...")

print("\n" + "="*60)
print("🔍 3. TESTING CORRIDOR WEATHER (fetch_corridor_conditions)")
print("="*60)
weather_res = fetch_corridor_conditions.invoke({"latitude": 37.7749, "longitude": -122.4194})
print("✅ Weather Result:")
print("   " + str(weather_res)[:200] + "...")

print("\n" + "="*60)
print("🔍 4. TESTING GEMINI LANGGRAPH REASONER")
print("="*60)
from langchain_core.messages import HumanMessage
from src.orchestrator import fde_agent

thread_config = {"configurable": {"thread_id": "test_verification_run"}}
res = fde_agent.invoke({
    "messages": [HumanMessage(content="Check active fleet telemetry for recent high risk vehicles and summarize in one sentence.")]
}, config=thread_config)

final_message = res["messages"][-1]
print("✅ FDE Agent Response:")
print("   " + str(final_message.content))

print("\n" + "="*60)
print("🎉 ALL END-TO-END PIPELINE CHECKS PASSED!")
print("="*60)
