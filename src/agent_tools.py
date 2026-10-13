import os
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import urllib
import requests
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pyodbc

from langchain_core.tools import tool
from langchain_pinecone import PineconeVectorStore

# ==========================================
# 1. ENVIRONMENT & VECTOR STORE SETUP
# ==========================================
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent  

load_dotenv(dotenv_path=project_root / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
EMBEDDINGS_MODEL_SETTING = os.getenv("EMBEDDINGS_MODEL", "GEMINI").strip().upper()

db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
db_user = os.getenv("SQL_AGENT_USER", "USR_FDE_RO")
db_password = os.getenv("SQL_AGENT_PASSWORD", "AgentPassword2026!")

# Configure embedding model based on active setting
if EMBEDDINGS_MODEL_SETTING == "GEMINI":
    google_key = os.getenv("GOOGLE_API_KEY")
    embedding_model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    print(f"✨ Tools Mode: Connecting to Gemini Index via [{embedding_model_name}]...")
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name, google_api_key=google_key)
    INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fde-sop-index-gemini")

elif EMBEDDINGS_MODEL_SETTING == "OPENAI":
    print("🤖 Tools Mode: Connecting to OpenAI Index (1536 Dim)...")
    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings()
    INDEX_NAME = "fde-sop-index-openai"

else:
    local_model_target = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3").strip()
    print(f"🤗 Tools Mode: Connecting to Local Index [{local_model_target}] (1024 Dim)...")
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=local_model_target, model_kwargs={'device': 'cpu'})
    INDEX_NAME = "fde-sop-index-local"

# Initialize Pinecone vector retriever if API key is present
retriever = None
if PINECONE_API_KEY:
    try:
        vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    except Exception as e:
        print(f"⚠️ Pinecone initialization note: {e}")

# ==========================================
# 2. CORE FDE AGENT TOOLS
# ==========================================

@tool
def query_telemetry_db(sql_query: str) -> str:
    """
    Executes a SQL SELECT query against the FDE_VIEWS.VW_ACTIVE_FLEET view.
    Columns available:
    Timestamp, Latitude, Longitude, Current_Temperature_C, Cargo_Condition_Code,
    Risk_Classification, Delay_Probability, Port_Congestion_Level, Route_Risk_Index.
    Always write standard T-SQL queries.
    """
    # Detect available SQL Server ODBC driver
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

    params = urllib.parse.quote_plus(connection_string)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    
    try:
        cleaned_query = sql_query.strip()
        if not cleaned_query.upper().startswith("SELECT"):
            return "SECURITY BLOCK: Only SELECT operations are authorized on this view."
            
        with engine.connect() as conn:
            cursor = conn.execute(text(cleaned_query))
            columns = list(cursor.keys())
            rows = cursor.fetchmany(10)
            
            if not rows:
                return "No records matched the query criteria."
                
            formatted_output = f"COLUMNS: {', '.join(columns)}\n"
            for row in rows:
                formatted_output += str(tuple(row)) + "\n"
                
            return formatted_output
    except Exception as e:
        return f"Database Error: {str(e)}"

@tool
def fetch_corridor_conditions(latitude: float, longitude: float) -> str:
    """
    Fetches real-time weather and corridor conditions from a live REST API for given GPS coordinates.
    Provides temperature, wind speed, and computed corridor congestion index.
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        headers = {"User-Agent": "ColdChainLogisticsPlatform/1.0"}
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        payload = response.json().get("current_weather", {})
        temp = payload.get("temperature", "N/A")
        wind = payload.get("windspeed", 0.0)
        
        congestion_index = 8.5 if wind > 10.0 else 2.5
        status_note = "High Transit Disruption" if wind > 10.0 else "Corridor Normal"
        
        return (
            f"--- LIVE CORRIDOR TELEMETRY ---\n"
            f"Target GPS: {latitude}, {longitude}\n"
            f"External Temp: {temp}°C | Wind Speed: {wind} km/h\n"
            f"Corridor Risk: {status_note} (Congestion Index: {congestion_index}/10)\n"
            f"-------------------------------"
        )
    except Exception as e:
        return f"Corridor API Communication Failure: {str(e)}"

@tool
def search_compliance_sop(query: str) -> str:
    """
    Searches enterprise Standard Operating Procedures (SOPs) indexed in the Pinecone Vector DB.
    Use this to retrieve regulatory thresholds, cold-chain breach mitigations, and rerouting rules.
    """
    if retriever is None:
        return "Vector Store Offline: Pinecone has not been initialized or active index not found."
    try:
        matched_docs = retriever.invoke(query)
        if not matched_docs:
            return "No matching compliance clauses found."
            
        formatted_context = "\n\n".join(
            [f"[Source: {doc.metadata.get('source_file', 'SOP')} | Format: {doc.metadata.get('file_format', 'RAW')}]\n{doc.page_content}" for doc in matched_docs]
        )
        return f"--- COMPLIANCE SOP CONTEXT ---\n{formatted_context}\n------------------------------"
    except Exception as e:
        return f"Vector Store Retrieval Error: {str(e)}"

# ==========================================
# 3. LOCAL VERIFICATION
# ==========================================
if __name__ == "__main__":
    print("\n--- Testing Tool 1: SQL Telemetry View ---")
    print(query_telemetry_db.invoke("SELECT TOP 2 Latitude, Longitude, Current_Temperature_C FROM FDE_VIEWS.VW_ACTIVE_FLEET"))
    
    print("\n--- Testing Tool 2: Live Corridor API ---")
    print(fetch_corridor_conditions.invoke({"latitude": 33.77, "longitude": -118.19}))
    
    print("\n--- Testing Tool 3: Pinecone Vector Retrieval ---")
    print(search_compliance_sop.invoke("What are the temperature rules for fresh perishables?"))
