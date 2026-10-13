# Cold-Chain Logistics FDE Platform - Complete Implementation Guide

## Phase 0: Database Provisioning & Telemetry Ingestion

### 1. Spin up the Legacy MSSQL Container
Make sure Docker Desktop (or the Docker daemon) is running.
Run the official Microsoft SQL Server 2022 container with persistent storage:
```bash
docker run -v mssql_data:/var/opt/mssql \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
  -p 1433:1433 \
  --name legacy-mssql \
  --restart always \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

### 2. Ingest Legacy Telemetry Data
Run the ingestion script to map and load the 32,000+ logistics rows from `data/raw/dynamic_supply_chain_logistics_dataset.csv` into `dbo.TBL_SC_FLEET_HIST_RAW`:
```bash
python scripts/ingest_legacy_data.py
```

---

## Phase 1: Security, Semantic Views & Audit Trail

### 1. Apply Security Layer & Semantic View
Execute `scripts/setup_security_and_view.sql` using VS Code (SQL Server Extension), Azure Data Studio, or via Python / sqlcmd:
* Creates schema `FDE_VIEWS`
* Builds view `FDE_VIEWS.VW_ACTIVE_FLEET`
* Creates audit table `FDE_VIEWS.AgentAuditLog`
* Creates user `USR_FDE_RO` with least-privilege permissions

### 2. Verify Least-Privilege Access
Test with user `USR_FDE_RO`:
```sql
-- This MUST succeed:
SELECT TOP 5 * FROM FDE_VIEWS.VW_ACTIVE_FLEET;

-- This MUST fail (Permission Denied):
SELECT TOP 5 * FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

---

## Phase 2: Vector Database Ingestion (Pinecone + Gemini)

1. Ensure `GOOGLE_API_KEY` and `PINECONE_API_KEY` are populated in your `.env`.
2. Run the ingestion pipeline:
```bash
python scripts/ingest_sop_pinecone.py
```
This automatically:
* Connects to Pinecone (AWS `us-east-1` serverless)
* Creates index `fde-sop-index-gemini` (dimension 768 for `models/text-embedding-004`)
* Chunks and upserts `data/policy/Cold_Chain_Incident_SOP_v2.md`
* Caches file hashes in `data/cache/ingestion_hash_cache.json`

---

## Phase 3: Agent Orchestrator Verification

Test the LangGraph multi-tool loop via CLI:
```bash
python src/orchestrator.py
```
Sample test query:
> *"Find active shipments near Los Angeles (Latitude ~33.8, Longitude ~-118.1). Check the local weather there and tell me if the current cargo temperature violates the SOP for fresh perishables."*

---

## Phase 4: Launching the Dispatch Console

Launch the Streamlit web dashboard:
```bash
streamlit run src/ui.py
```
Access the console at `http://localhost:8501`.
* **Dispatch Console:** Interactive chat, tool execution traces, and structured operational reports.
* **Security & Audit Logs:** Admin view showing execution records stored in `FDE_VIEWS.AgentAuditLog`.

---

## Phase 5: Production Deployment on AWS EC2

1. Launch an EC2 instance:
   * **AMI:** Ubuntu Server 22.04 / 24.04 LTS
   * **Type:** `t3.medium` or `c7i-flex.large`
   * **Storage:** 30 GB gp3
   * **Security Group:** Inbound TCP 22 (SSH), TCP 1433 (MSSQL), TCP 8501 (Streamlit).
2. SSH into your instance:
   ```bash
   ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
   ```
3. Run the automated provisioning script:
   ```bash
   chmod +x deploy/setup_ec2.sh
   ./deploy/setup_ec2.sh
   ```
4. Configure systemd service:
   ```bash
   sudo cp deploy/streamlit.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable streamlit
   sudo systemctl start streamlit
   ```
