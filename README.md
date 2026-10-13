# 🧊 Cold-Chain Logistics Incident Control System
> **Forward Deployed Engineering (FDE) Platform for Real-Time Telemetry Decision Support**

[![Powered by Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%203.8%20Flash-blue.svg)](https://ai.google.dev/)
[![Vector DB](https://img.shields.io/badge/Vector%20Store-Pinecone-green.svg)](https://www.pinecone.io/)
[![Orchestration](https://img.shields.io/badge/Framework-LangGraph-purple.svg)](https://www.langchain.com/langgraph)
[![Database](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server-red.svg)](https://www.microsoft.com/sql-server)
[![Cloud](https://img.shields.io/badge/Deployment-AWS%20EC2%20(Live)-success.svg)](http://18.234.59.239:8501)

---

## 📌 1. Project Overview

In cold-chain supply chains, transporting perishable goods (produce, pharmaceuticals, frozen foods) requires strict thermal and transit monitoring. A single temperature spike beyond 4.0°C or an unexpected port congestion delay can cause severe spoilage, regulatory fines, and contractual SLA breaches.

This project delivers an **autonomous Forward Deployed Engineering (FDE) operational platform** that empowers logistics dispatchers and supply chain commanders to **"chat with their live data"**. The system continuously monitors vehicle IoT telemetry, correlates transit corridors with live atmospheric hazard data, and enforces company Standard Operating Procedures (SOPs) to recommend decisive mitigations.

### Key Capabilities:
* **Natural Language Fleet Analytics:** Dispatchers ask questions in plain English to inspect live shipments and telemetry anomalies.
* **Corridor Hazard Correlation:** Automatically queries live meteorological APIs (temperature, wind speeds, disruption indexes) for vehicles in transit.
* **SOP-Driven Compliance:** Semantic vector retrieval across enterprise Standard Operating Procedures to guide cooling adjustments and route diversions.
* **Semantic Layer Virtualization:** Abstracts legacy database schemas into clean business views while enforcing strict least-privilege security.
* **Dual-Interface Command Console:** Streamlit dispatch cockpit featuring live step-by-step agent reasoning traces and an enterprise administrative audit log viewer.

---

## 🏗️ 2. System Architecture

```mermaid
flowchart TD
    subgraph UI ["Client Layer (Streamlit)"]
        A["🧊 Dispatcher Console (src/ui.py)"]
        B["🛡️ Security & Audit Viewer"]
    end

    subgraph Orchestrator ["Agent Reasoner (LangGraph)"]
        C["StateGraph Orchestrator (src/orchestrator.py)"]
        D["Google Gemini LLM (gemini-2.0-flash)"]
        E["Memory Checkpointer (MemorySaver)"]
    end

    subgraph Tools ["Core Enterprise Subsystems (src/agent_tools.py)"]
        T1["query_telemetry_db"]
        T2["fetch_corridor_conditions"]
        T3["search_compliance_sop"]
    end

    subgraph Data ["Infrastructure & Storage"]
        DB[("MSSQL Docker Container<br/>FDE_VIEWS.VW_ACTIVE_FLEET")]
        API["Open-Meteo REST API<br/>Live Weather & Hazards"]
        VDB[("Pinecone Vector DB<br/>fde-sop-index-gemini")]
        LOGS[("Audit Table<br/>FDE_VIEWS.AgentAuditLog")]
    end

    A <--> C
    C <--> D
    C --- E
    C --> T1
    C --> T2
    C --> T3
    T1 <--> DB
    T2 <--> API
    T3 <--> VDB
    C -. Trace Payloads .-> LOGS
    B <--> LOGS
```

---

## 🔄 3. End-to-End Decision Pipeline

The diagram below illustrates how an incoming dispatcher query triggers a coordinated multi-step evaluation across telemetry, live weather, and compliance rules:

```mermaid
sequenceDiagram
    autonumber
    actor Dispatcher
    participant UI as Streamlit Console
    participant Agent as LangGraph (Gemini Reasoner)
    participant SQL as SQL Server (Semantic View)
    participant Weather as Open-Meteo API
    participant Pinecone as Pinecone Vector Store
    participant Audit as SQL Audit Log

    Dispatcher->>UI: "Check LA shipments near (33.8, -118.1) for temp violations"
    UI->>Agent: Forward User Query
    Agent->>Audit: Log Reasoner Intent

    Agent->>SQL: Execute query_telemetry_db (SELECT GPS & Temp)
    SQL-->>Agent: Returns Lat, Lon, Current_Temperature_C, Risk

    Agent->>Weather: Execute fetch_corridor_conditions (Lat, Lon)
    Weather-->>Agent: Returns Wind Speed, Temp, Corridor Congestion Index

    Agent->>Pinecone: Execute search_compliance_sop ("Perishables temp breach mitigation")
    Pinecone-->>Agent: Returns SOP Thresholds (Max 4.0°C, Divert to San Bernardino)

    Agent->>Agent: Synthesize Final Operational Resolution Report
    Agent->>Audit: Log Final Resolution Report
    Agent-->>UI: Structured Response (Executive Summary, Table, Action Plan)
    UI-->>Dispatcher: Display Resolution & Live Tool Traces
```

---

## 🛡️ 4. Data Security & Least-Privilege Architecture

Enterprises cannot expose production transactional databases directly to LLMs without guardrails. This project enforces a three-tier security and semantic layer:

```mermaid
graph LR
    subgraph RawLegacy ["Legacy Unprotected Tier"]
        RAW["dbo.TBL_SC_FLEET_HIST_RAW<br/>TS_UTC, V_LAT, IOT_TEMP_VAL_C"]
    end

    subgraph SemanticLayer ["Enterprise Semantic Layer"]
        VIEW["FDE_VIEWS.VW_ACTIVE_FLEET<br/>Timestamp, Latitude, Current_Temperature_C"]
    end

    subgraph SecurityRBAC ["Security Enforcement"]
        RO_USER["USR_FDE_RO (AI Agent)"]
    end

    RAW -->|Schema Masking & Casting| VIEW
    RO_USER -->|GRANT SELECT ONLY| VIEW
    RO_USER -.->|EXPLICIT DENY ALL| RAW
```

* **No Direct Raw Table Access:** `DENY SELECT, INSERT, UPDATE, DELETE ON dbo` ensures the LLM cannot mutate or read raw unvalidated tables.
* **Semantic Translation:** Cryptic column abbreviations (`PRT_CNG_LVL`, `RT_RSK_IDX`) are converted into human-intelligible fields (`Port_Congestion_Level`, `Route_Risk_Index`).
* **Audit Trail Governance:** Every reasoning step, parameter payload, and synthesized output is committed to `FDE_VIEWS.AgentAuditLog`.

---

## 📋 5. Implementation Plan

```mermaid
flowchart TD
    P0["Phase 0: Database Provisioning<br/>• Docker MSSQL 2022<br/>• 32k Row Telemetry Ingestion"]
    P1["Phase 1: Semantic Layer & Security<br/>• FDE_VIEWS Schema & View<br/>• USR_FDE_RO Least Privilege User<br/>• AgentAuditLog Table"]
    P2["Phase 2: SOP Vector Ingestion<br/>• Pinecone Provisioning (AWS us-east-1)<br/>• Gemini text-embedding-004<br/>• Hash Cache Synchronization"]
    P3["Phase 3: Agent Orchestration<br/>• LangGraph State Machine<br/>• Gemini 2.0 Flash Integration<br/>• Multi-Tool Binding & Verification"]
    P4["Phase 4: Streamlit UI Deployment<br/>• Dispatch Cockpit with Traces<br/>• Admin Audit Trail Portal"]
    P5["Phase 5: Cloud Infrastructure (AWS)<br/>• EC2 c7i-flex / t3.medium Setup<br/>• systemd Background Daemon<br/>• Automated GitHub Actions CI/CD"]

    P0 --> P1 --> P2 --> P3 --> P4 --> P5
```

---

## 🔑 6. Required API Keys & Setup Guide

To run or deploy this project, you need the following keys. Here is exactly how to acquire each:

### 1. Google Gemini API Key (`GOOGLE_API_KEY`)
* **Purpose:** Powers the core LLM reasoning engine (`gemini-2.0-flash`) and vector embeddings (`models/text-embedding-004`).
* **How to get it:**
  1. Visit [Google AI Studio](https://aistudio.google.com/).
  2. Sign in with your Google account.
  3. Click **"Get API key"** in the top left navigation.
  4. Click **"Create API key"** in a new or existing Google Cloud project.
  5. Copy your API key.

### 2. Pinecone API Key (`PINECONE_API_KEY`)
* **Purpose:** Hosts the serverless vector database index for Standard Operating Procedures.
* **How to get it:**
  1. Visit [Pinecone Console](https://app.pinecone.io/) and create a free account.
  2. In the left navigation, click on **API Keys**.
  3. Copy your default API key (or click **"Create API Key"**).
  * *Note:* The index `fde-sop-index-gemini` (dimension 768) is automatically created by `scripts/ingest_sop_pinecone.py` on AWS `us-east-1`.

### 3. AWS Credentials (For EC2 Deployment)
* **Purpose:** Hosts the Microsoft SQL Server container and runs the Streamlit production daemon.
* **Requirements:**
  1. An active [AWS Console](https://aws.amazon.com/) account.
  2. An EC2 instance running Ubuntu Server 22.04 / 24.04 (`t3.medium` or `c7i-flex.large`).
  3. Your EC2 SSH Key Pair (`.pem` file) and Public IPv4 address.
  4. Ensure your EC2 **Security Group** allows inbound traffic on:
     * Port `22` (SSH)
     * Port `1433` (MSSQL)
     * Port `8501` (Streamlit Web UI)

---

## ⚙️ 7. Quickstart Guide (Local Execution)

### Step 1: Clone or Navigate to the Folder
```bash
cd "C:\Users\ASUS\Desktop\AI Project"
```

### Step 2: Install Python Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Populate:
```env
GOOGLE_API_KEY=AIzaSy...
PINECONE_API_KEY=pcsk_...
AGENT_LLM=GEMINI
GEMINI_MODEL=gemini-3.8-flash
EMBEDDINGS_MODEL=GEMINI
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
```

### Step 4: Start SQL Server in Docker
Ensure Docker Desktop is running on your machine:
```bash
docker run -v mssql_data:/var/opt/mssql -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" -p 1433:1433 --name legacy-mssql --restart always -d mcr.microsoft.com/mssql/server:2022-latest
```

### Step 5: Ingest Telemetry Data
```bash
python scripts/ingest_legacy_data.py
```

### Step 6: Create Security & Semantic Views
Apply the enterprise security layer, semantic views, and audit log table:
```bash
python scripts/apply_security_views.py
```

### Step 7: Ingest SOPs to Pinecone
```bash
python scripts/ingest_sop_pinecone.py
```

### Step 8: Verify End-to-End Pipeline
Run the full verification suite testing database permissions, Pinecone vector search, weather REST API, and Gemini reasoning:
```bash
python scripts/verify_agent_pipeline.py
```

### Step 9: Launch the Dispatch Console
```bash
streamlit run src/ui.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ 8. Live AWS EC2 Cloud Deployment

The application is deployed on an **AWS EC2 Ubuntu 26.04** instance with Docker, SQL Server 2022, and a systemd background service:

* **Live URL:** [`http://18.234.59.239:8501`](http://18.234.59.239:8501)
* **Instance ID:** `i-07ceb9a6ab5cd74e6`
* **Public IPv4:** `18.234.59.239`
* **Architecture:** `t3.micro` + 4 GB Linux swap file + memory interception shim (`fake_meminfo.so`) for SQL Server 2022.
* **Service Status:** Systemd managed (`streamlit.service`), auto-restarting on reboot.
* **Admin Audit Portal Credentials:**
  * Username: `sa`
  * Password: `FdeEnterprisePass123!`

---

## 📂 8. Project File Structure

```
AI Project/
├── .github/
│   └── workflows/
│       └── deploy.yml              # Automated GitHub Actions deployment to EC2
├── .streamlit/
│   └── config.toml                 # Streamlit server & theme configuration
├── data/
│   ├── cache/
│   │   └── ingestion_hash_cache.json # MD5 vector ingestion hash tracker
│   ├── policy/
│   │   └── Cold_Chain_Incident_SOP_v2.md # Regulatory compliance SOPs
│   ├── raw/
│   │   └── dynamic_supply_chain_logistics_dataset.csv # 32k raw telemetry records
│   └── source/
│       └── data.txt                # Kaggle dataset reference link
├── deploy/
│   ├── setup_ec2.sh                # Automated AWS EC2 instance provisioning
│   └── streamlit.service           # systemd background daemon service unit
├── docs/
│   └── instructions.md             # Detailed phase-by-phase operational manual
├── scripts/
│   ├── ingest_legacy_data.py       # Loads raw dataset into MSSQL
│   ├── ingest_sop_pinecone.py      # Chunks & indexes SOPs into Pinecone with Gemini
│   └── setup_security_and_view.sql # Semantic views, audit table & RBAC rules
├── src/
│   ├── prompts/
│   │   └── system_prompt.txt       # Persona & structured business output template
│   ├── agent_tools.py              # Telemetry SQL, Weather REST, and SOP retriever
│   ├── orchestrator.py             # LangGraph state machine powered by Gemini
│   └── ui.py                       # Streamlit Dispatch Cockpit & Audit Portal
├── .env.example                    # Template environment variables
├── requirements.txt                # Project dependencies (LangChain, Gemini, etc.)
└── README.md                       # Comprehensive project documentation
```
