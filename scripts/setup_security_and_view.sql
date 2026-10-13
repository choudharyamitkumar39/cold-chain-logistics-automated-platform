-- ====================================================================
-- FDE ENTERPRISE SECURITY, SEMANTIC LAYER & AUDIT TRAIL SCRIPT
-- Purpose: Protect the legacy DB from LLM hallucinations & mutations,
--          provide clean English semantic mapping, and enable audit logging.
-- ====================================================================

USE master;
GO

-- 1. Create a dedicated schema for our clean AI views and audit tables
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'FDE_VIEWS')
BEGIN
    EXEC('CREATE SCHEMA FDE_VIEWS;');
END
GO

-- 2. Create or alter the Semantic View (Translating legacy junk to clean English)
CREATE OR ALTER VIEW FDE_VIEWS.VW_ACTIVE_FLEET AS
SELECT 
    TS_UTC AS [Timestamp],
    V_LAT AS [Latitude],
    V_LON AS [Longitude],
    CAST(IOT_TEMP_VAL_C AS FLOAT) AS [Current_Temperature_C],
    CGO_COND_CD AS [Cargo_Condition_Code],
    RISK_CLS_TXT AS [Risk_Classification],
    DELAY_PROB_DEC AS [Delay_Probability],
    PRT_CNG_LVL AS [Port_Congestion_Level],
    RT_RSK_IDX AS [Route_Risk_Index]
FROM dbo.TBL_SC_FLEET_HIST_RAW;
GO

-- 3. Create the Enterprise Agent Audit Log Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AgentAuditLog' AND schema_id = SCHEMA_ID('FDE_VIEWS'))
BEGIN
    CREATE TABLE FDE_VIEWS.AgentAuditLog (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        Timestamp DATETIME DEFAULT GETDATE(),
        SessionID VARCHAR(50),
        NodeExecuted VARCHAR(50),
        ToolName VARCHAR(100),
        Content NVARCHAR(MAX)
    );
END
GO

-- 4. Create a strict Login and User for the AI Agent
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'USR_FDE_RO')
BEGIN
    CREATE LOGIN USR_FDE_RO WITH PASSWORD = 'AgentPassword2026!';
END
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'USR_FDE_RO')
BEGIN
    CREATE USER USR_FDE_RO FOR LOGIN USR_FDE_RO;
END
GO

-- 5. Grant access ONLY to the semantic view and audit log insert, explicitly denying raw access
GRANT SELECT ON FDE_VIEWS.VW_ACTIVE_FLEET TO USR_FDE_RO;
GRANT INSERT ON FDE_VIEWS.AgentAuditLog TO USR_FDE_RO;
DENY SELECT ON dbo.TBL_SC_FLEET_HIST_RAW TO USR_FDE_RO;
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::dbo TO USR_FDE_RO;
GO
