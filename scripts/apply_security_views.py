import re
import os
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

sql_file = project_root / "scripts" / "setup_security_and_view.sql"

db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
db_user = os.getenv("SQL_ADMIN_USER", "sa")
db_password = os.getenv("SQL_ADMIN_PASSWORD", "FdeEnterprisePass123!")

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
    f"UID={db_user};"
    f"PWD={db_password};"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes;"
)

print(f"Connecting to MSSQL at {db_host}:{db_port} as {db_user}...")
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()

with open(sql_file, "r", encoding="utf-8") as f:
    sql_text = f.read()

# Split statements by GO on its own line
statements = re.split(r"^\s*GO\s*$", sql_text, flags=re.MULTILINE | re.IGNORECASE)

for stmt in statements:
    clean_stmt = stmt.strip()
    if clean_stmt:
        print(f"Executing batch:\n{clean_stmt[:80]}...\n")
        cursor.execute(clean_stmt)

print("✅ Security views, roles, and audit table successfully applied!")
cursor.close()
conn.close()
