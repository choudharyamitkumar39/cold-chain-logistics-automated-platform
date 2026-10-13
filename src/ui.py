import os
import sys
import uuid
import json
import urllib
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import pyodbc
from langchain_core.messages import HumanMessage, ToolMessage

# ==========================================
# 1. IMMEDIATE PATH & ENVIRONMENT RESOLUTION
# ==========================================
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.orchestrator import fde_agent

# ==========================================
# 2. SQL CREDENTIALS & AUDIT LOGGING ENGINE
# ==========================================
db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
db_user = os.getenv("SQL_AGENT_USER", "USR_FDE_RO")
db_password = os.getenv("SQL_AGENT_PASSWORD", "AgentPassword2026!")

# Detect available SQL driver
available_drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
driver_choice = "ODBC Driver 18 for SQL Server"
if "ODBC Driver 18 for SQL Server" in available_drivers:
    driver_choice = "ODBC Driver 18 for SQL Server"
elif "ODBC Driver 17 for SQL Server" in available_drivers:
    driver_choice = "ODBC Driver 17 for SQL Server"
elif available_drivers:
    driver_choice = available_drivers[0]

connection_string = (
    f"DRIVER={{{driver_choice}}};"
    f"SERVER={db_host},{db_port};"
    f"DATABASE=master;"
    f"UID={db_user};"
    f"PWD={db_password};"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes;"
)

log_params = urllib.parse.quote_plus(connection_string)
log_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={log_params}")

def write_audit_log(session_id, node_name, tool_name, content):
    """Silently writes agent execution traces to the SQL audit table."""
    try:
        with log_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO FDE_VIEWS.AgentAuditLog (SessionID, NodeExecuted, ToolName, Content)
                VALUES (:session_id, :node_name, :tool_name, :content)
            """), {
                "session_id": session_id,
                "node_name": node_name,
                "tool_name": tool_name,
                "content": str(content)
            })
            conn.commit()
    except Exception as e:
        # Fails silently if DB is not currently active
        pass

# ==========================================
# 3. PAGE CONFIGURATION & ENTERPRISE THEME
# ==========================================
st.set_page_config(
    page_title="Cold-Chain Dispatch Console",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    div[data-testid="stSidebar"] { background-color: #111622; border-right: 1px solid #1E293B; }
    .stMarkdown code { background-color: #1E293B !important; color: #38BDF8 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. MULTI-USER STATE & THREAD MANAGEMENT
# ==========================================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = []

thread_config = {"configurable": {"thread_id": st.session_state.thread_id}}

# ==========================================
# 5. SIDEBAR NAVIGATION & METADATA
# ==========================================
with st.sidebar:
    st.title("🧊 FDE Command Center")
    st.caption("AI Cold-Chain Incident Platform")
    
    app_mode = st.radio("System Mode", ["🧊 Dispatch Console", "🛡️ Security & Audit Logs"])
    
    st.markdown("---")
    st.caption(f"Session Token: `{st.session_state.thread_id[:8]}...`")
    st.markdown(f"**LLM Reasoner:** `{os.getenv('AGENT_LLM', 'GEMINI')}` ({os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')})")
    st.markdown(f"**Vector Store:** Pinecone (`{os.getenv('EMBEDDINGS_MODEL', 'GEMINI')}`)")
    st.markdown(f"**Database:** MSSQL on `{db_host}:{db_port}`")
    
    st.markdown("---")
    if st.button("🗑️ Reset Session", use_container_width=True):
        st.session_state.ui_messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

# ==========================================
# 6. VIEW ROUTING (DISPATCH VS AUDIT)
# ==========================================

if app_mode == "🧊 Dispatch Console":
    st.title("Cold-Chain Incident Control Dashboard")
    st.caption("Production Data Engineering Pipeline • Real-Time Decision Optimization Platform")

    for entry in st.session_state.ui_messages:
        with st.chat_message(entry["role"], avatar="👤" if entry["role"] == "user" else "🤖"):
            if "traces" in entry:
                for trace in entry["traces"]:
                    if trace["type"] == "tool_input":
                        st.markdown(f"**⚡ Intent Recognized:** `{trace['name']}`")
                        with st.expander(f"📥 View Generated Input ({trace['name']})", expanded=False):
                            st.json(trace["args"])
                    elif trace["type"] == "tool_output":
                        with st.expander(f"📤 View Raw Output ({trace['name']})", expanded=False):
                            st.code(trace["content"], language="text")
            st.markdown(entry["content"])

    if user_input := st.chat_input("Query fleet telemetry, corridor updates, or compliance thresholds..."):
        
        st.session_state.ui_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            final_response = ""
            current_traces = [] 
            
            with st.status("🧠 Initializing Core Reasoner Node...", expanded=True) as status:
                try:
                    events = fde_agent.stream(
                        {"messages": [HumanMessage(content=user_input)]}, 
                        config=thread_config,
                        stream_mode="updates"
                    )
                    
                    for event in events:
                        for node_name, node_state in event.items():
                            
                            if node_name == "reasoner":
                                latest_msg = node_state["messages"][-1]
                                
                                # A. Tool call requests
                                if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
                                    status.update(label="🧠 Agent generated tool parameters...")
                                    for tool_call in latest_msg.tool_calls:
                                        st.markdown(f"**⚡ Intent Recognized:** `{tool_call['name']}`")
                                        with st.expander(f"📥 View Generated Input ({tool_call['name']})", expanded=False):
                                            st.json(tool_call['args'])
                                        
                                        current_traces.append({
                                            "type": "tool_input",
                                            "name": tool_call['name'],
                                            "args": tool_call['args']
                                        })
                                        
                                        write_audit_log(
                                            session_id=st.session_state.thread_id,
                                            node_name="reasoner",
                                            tool_name=tool_call['name'],
                                            content=json.dumps(tool_call['args'])
                                        )
                                
                                # B. Final synthesis
                                if latest_msg.content:
                                    if isinstance(latest_msg.content, list):
                                        final_response = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in latest_msg.content])
                                    else:
                                        final_response = str(latest_msg.content)
                                    status.update(label="📝 Generating Operational Resolution Report...")
                                    
                                    write_audit_log(
                                        session_id=st.session_state.thread_id,
                                        node_name="reasoner_final",
                                        tool_name="LLM Text Synthesis",
                                        content=final_response
                                    )
                                    
                            elif node_name == "tools":
                                status.update(label="🔧 Executing Enterprise Subsystem Tools...")
                                for msg in node_state.get("messages", []):
                                    if isinstance(msg, ToolMessage):
                                        with st.expander(f"📤 View Raw Output ({msg.name})", expanded=False):
                                            st.code(msg.content, language="text")
                                            
                                        current_traces.append({
                                            "type": "tool_output",
                                            "name": msg.name,
                                            "content": msg.content
                                        })
                                        
                                        write_audit_log(
                                            session_id=st.session_state.thread_id,
                                            node_name="tools",
                                            tool_name=msg.name,
                                            content=msg.content
                                        )
                    
                    status.update(label="Incident Matrix Evaluation Complete", state="complete", expanded=False)
                    
                except Exception as e:
                    status.update(label="Execution Encountered Error", state="error", expanded=True)
                    st.error(f"Error during agent reasoning: {str(e)}")
                    final_response = f"⚠️ Operational Error: {str(e)}"
                
            if final_response:
                st.markdown(final_response)
                st.session_state.ui_messages.append({
                    "role": "assistant",
                    "content": final_response,
                    "traces": current_traces
                })


elif app_mode == "🛡️ Security & Audit Logs":
    st.title("🛡️ Enterprise Agent Audit Trail")
    st.caption("Secure database inspection of FDE_VIEWS.AgentAuditLog")
    
    st.markdown("### Database Authorization Gate")
    st.markdown("Enter administrator credentials (`SQL_ADMIN_USER`) to inspect execution audit trails.")
    
    with st.form("admin_auth_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_user = st.text_input("Admin Username", value=os.getenv("SQL_ADMIN_USER", "sa"))
        with col2:
            input_pass = st.text_input("Admin Password", type="password", value="")
            
        submit_admin = st.form_submit_button("Authenticate & Load Logs", use_container_width=True)

    if submit_admin:
        expected_admin_user = os.getenv("SQL_ADMIN_USER", "sa")
        expected_admin_pass = os.getenv("SQL_ADMIN_PASSWORD", "FdeEnterprisePass123!")
        
        if input_user == expected_admin_user and input_pass == expected_admin_pass:
            try:
                admin_params = urllib.parse.quote_plus(
                    f"DRIVER={{{driver_choice}}};"
                    f"SERVER={db_host},{db_port};"
                    f"DATABASE=master;"
                    f"UID={input_user};"
                    f"PWD={input_pass};"
                    f"Encrypt=no;"
                    f"TrustServerCertificate=yes;"
                )
                admin_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={admin_params}")
                
                with admin_engine.connect() as conn:
                    query = """
                        SELECT LogID, Timestamp, SessionID, NodeExecuted, ToolName, Content 
                        FROM FDE_VIEWS.AgentAuditLog 
                        ORDER BY Timestamp DESC
                    """
                    df = pd.read_sql(query, conn)
                
                st.success("✅ Authenticated successfully as Admin.")
                
                if not df.empty:
                    st.dataframe(
                        df,
                        column_config={
                            "LogID": st.column_config.NumberColumn("ID", format="%d"),
                            "Timestamp": st.column_config.DatetimeColumn("Execution Time", format="DD/MM/YYYY-h:mm a"),
                            "SessionID": "Session Token",
                            "NodeExecuted": "Graph Node",
                            "ToolName": "Tool Triggered",
                            "Content": "Raw Payload Data"
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=600
                    )
                else:
                    st.info("No audit logs found yet in the database. Run a query in the Dispatch Console first.")
                    
            except Exception as e:
                st.error(f"Database Query Failed: {e}")
        else:
            st.error("❌ Invalid Administrator Credentials.")
