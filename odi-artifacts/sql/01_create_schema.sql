-- Oracle Autonomous Database Schema for EPM Audit
-- Migration from Python scripts to ODI → Autonomous DB → Retool
-- Created: 2026-03-03

-- Create audit schema
CREATE USER EPM_AUDIT IDENTIFIED BY "ChangeMe_StrongPassword123!"
DEFAULT TABLESPACE DATA
QUOTA UNLIMITED ON DATA
ACCOUNT UNLOCK;

GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, 
    CREATE PROCEDURE, CREATE SEQUENCE, CREATE TRIGGER,
    CREATE TYPE, CREATE SYNONYM TO EPM_AUDIT;

ALTER USER EPM_AUDIT QUOTA UNLIMITED ON DATA;

-- Switch to EPM_AUDIT schema
CONNECT EPM_AUDIT/ChangeMe_StrongPassword123!

--------------------------------------------------------------------------------
-- 1. Core Artifacts Table (unified for all EPM systems)
--------------------------------------------------------------------------------

CREATE TABLE EPM_AUDIT.ARTIFACTS (
    artifact_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system VARCHAR2(10) NOT NULL 
        CHECK (source_system IN ('FCCS','PBCS','EDM','DE','ARCS','PCM')),
    artifact_type VARCHAR2(50) NOT NULL,
    artifact_name VARCHAR2(500) NOT NULL,
    artifact_content CLOB,
    content_hash VARCHAR2(64) NOT NULL,  -- SHA-256 for change detection
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    extraction_batch_id NUMBER,
    created_by VARCHAR2(100) DEFAULT USER,
    CONSTRAINT uk_artifact_source_name UNIQUE (source_system, artifact_name, extraction_batch_id)
)
TABLESPACE DATA;

COMMENT ON TABLE EPM_AUDIT.ARTIFACTS IS 'Stores extracted EPM artifacts from all systems';
COMMENT ON COLUMN EPM_AUDIT.ARTIFACTS.source_system IS 'EPM application code: FCCS, PBCS, EDM, DE, ARCS, PCM';
COMMENT ON COLUMN EPM_AUDIT.ARTIFACTS.content_hash IS 'SHA-256 hash for detecting changes between versions';
COMMENT ON COLUMN EPM_AUDIT.ARTIFACTS.extraction_batch_id IS 'Foreign key to EXTRACTION_LOG for traceability';

-- Indexes for query performance
CREATE INDEX EPM_AUDIT.IX_ARTIFACTS_SOURCE_DATE 
    ON EPM_AUDIT.ARTIFACTS(source_system, extracted_date) 
    TABLESPACE DATA;

CREATE INDEX EPM_AUDIT.IX_ARTIFACTS_HASH 
    ON EPM_AUDIT.ARTIFACTS(content_hash) 
    TABLESPACE DATA;

CREATE INDEX EPM_AUDIT.IX_ARTIFACTS_BATCH 
    ON EPM_AUDIT.ARTIFACTS(extraction_batch_id) 
    TABLESPACE DATA;

--------------------------------------------------------------------------------
-- 2. Extraction Log (SOX audit trail)
--------------------------------------------------------------------------------

CREATE TABLE EPM_AUDIT.EXTRACTION_LOG (
    batch_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system VARCHAR2(10) NOT NULL,
    extraction_start TIMESTAMP NOT NULL,
    extraction_end TIMESTAMP,
    records_extracted NUMBER DEFAULT 0,
    records_changed NUMBER DEFAULT 0,  -- New/changed vs last run
    status VARCHAR2(20) DEFAULT 'RUNNING' 
        CHECK (status IN ('RUNNING','SUCCESS','FAILED','PARTIAL')),
    error_details CLOB,
    odi_session_id VARCHAR2(100),
    executed_by VARCHAR2(100) DEFAULT USER,
    source_api_endpoint VARCHAR2(500),
    http_response_code NUMBER,
    retry_count NUMBER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
TABLESPACE DATA;

COMMENT ON TABLE EPM_AUDIT.EXTRACTION_LOG IS 'SOX-compliant audit trail of all extractions';

CREATE INDEX EPM_AUDIT.IX_LOG_STATUS 
    ON EPM_AUDIT.EXTRACTION_LOG(status, extraction_start) 
    TABLESPACE DATA;

CREATE INDEX EPM_AUDIT.IX_LOG_SYSTEM 
    ON EPM_AUDIT.EXTRACTION_LOG(source_system, extraction_start) 
    TABLESPACE DATA;

--------------------------------------------------------------------------------
-- 3. Materiality Rules Configuration
--------------------------------------------------------------------------------

CREATE TABLE EPM_AUDIT.MATERIALITY_RULES (
    rule_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_name VARCHAR2(100) NOT NULL,
    source_system VARCHAR2(10),
    artifact_type VARCHAR2(50),
    threshold_type VARCHAR2(20) NOT NULL 
        CHECK (threshold_type IN ('DOLLAR','PERCENT','COUNT','CUSTOM')),
    threshold_value NUMBER NOT NULL,
    threshold_currency VARCHAR2(3),  -- For DOLLAR type: USD, EUR, etc.
    comparison_field VARCHAR2(100),  -- Which field to compare: 'impact_amount', 'record_count'
    is_active CHAR(1) DEFAULT 'Y' NOT NULL 
        CHECK (is_active IN ('Y','N')),
    description VARCHAR2(500),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(100) DEFAULT USER,
    modified_date TIMESTAMP,
    modified_by VARCHAR2(100)
)
TABLESPACE DATA;

-- Default materiality rules
INSERT INTO EPM_AUDIT.MATERIALITY_RULES 
    (rule_name, source_system, artifact_type, threshold_type, threshold_value, description)
VALUES 
    ('High Dollar Impact', NULL, NULL, 'DOLLAR', 1000000, 'Artifacts impacting > $1M'),
    ('Consolidation Rules', 'FCCS', 'Consolidation_Rule', 'PERCENT', 10, 'FCCS rule changes > 10% impact'),
    ('Data Form Changes', NULL, 'Data_Form', 'COUNT', 100, 'Forms with > 100 field changes'),
    ('EDM Metadata', 'EDM', 'Dimension_Member', 'COUNT', 50, 'EDM changes affecting > 50 members');

COMMIT;

--------------------------------------------------------------------------------
-- 4. Views for Reporting
--------------------------------------------------------------------------------

-- Summary view for dashboard
CREATE OR REPLACE VIEW EPM_AUDIT.V_DASHBOARD_SUMMARY AS
SELECT 
    a.source_system,
    COUNT(*) as total_artifacts,
    MAX(a.extracted_date) as last_extraction,
    COUNT(DISTINCT TRUNC(a.extracted_date)) as extraction_days,
    SUM(CASE WHEN a.extracted_date > SYSDATE - 1 THEN 1 ELSE 0 END) as artifacts_last_24h,
    SUM(CASE WHEN a.extracted_date > SYSDATE - 7 THEN 1 ELSE 0 END) as artifacts_last_7d,
    COUNT(DISTINCT a.artifact_name) as unique_artifacts
FROM EPM_AUDIT.ARTIFACTS a
GROUP BY a.source_system;

-- Changed artifacts view (detects via hash comparison)
CREATE OR REPLACE VIEW EPM_AUDIT.V_CHANGED_ARTIFACTS AS
WITH ranked AS (
    SELECT 
        artifact_id,
        source_system,
        artifact_type,
        artifact_name,
        content_hash,
        extracted_date,
        extraction_batch_id,
        LAG(content_hash) OVER (
            PARTITION BY source_system, artifact_name 
            ORDER BY extracted_date
        ) as prev_hash,
        LAG(extracted_date) OVER (
            PARTITION BY source_system, artifact_name 
            ORDER BY extracted_date
        ) as prev_date
    FROM EPM_AUDIT.ARTIFACTS
)
SELECT 
    artifact_id,
    source_system,
    artifact_type,
    artifact_name,
    extracted_date,
    prev_date as previous_extraction,
    CASE 
        WHEN prev_hash IS NULL THEN 'NEW'
        WHEN content_hash != prev_hash THEN 'CHANGED'
        ELSE 'UNCHANGED'
    END as change_status,
    extraction_batch_id
FROM ranked
WHERE prev_hash IS NULL OR content_hash != prev_hash;

-- Material artifacts based on thresholds
CREATE OR REPLACE VIEW EPM_AUDIT.V_MATERIAL_ARTIFACTS AS
WITH change_counts AS (
    SELECT 
        a.source_system,
        a.artifact_name,
        COUNT(*) as change_events,
        MAX(a.extracted_date) as last_changed
    FROM EPM_AUDIT.V_CHANGED_ARTIFACTS a
    WHERE a.change_status IN ('NEW', 'CHANGED')
      AND a.extracted_date > SYSDATE - 30  -- Last 30 days
    GROUP BY a.source_system, a.artifact_name
    HAVING COUNT(*) >= 5  -- Changed 5+ times = material activity
)
SELECT 
    cc.*,
    CASE 
        WHEN cc.change_events >= 20 THEN 'CRITICAL'
        WHEN cc.change_events >= 10 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as materiality_level
FROM change_counts cc
ORDER BY cc.change_events DESC;

-- Extraction performance view
CREATE OR REPLACE VIEW EPM_AUDIT.V_EXTRACTION_PERFORMANCE AS
SELECT 
    source_system,
    TRUNC(extraction_start) as extraction_date,
    COUNT(*) as extraction_count,
    SUM(records_extracted) as total_records,
    AVG(EXTRACT(SECOND FROM (extraction_end - extraction_start))) as avg_duration_seconds,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_count
FROM EPM_AUDIT.EXTRACTION_LOG
WHERE extraction_start > SYSDATE - 90  -- Last 90 days
GROUP BY source_system, TRUNC(extraction_start)
ORDER BY extraction_date DESC;

--------------------------------------------------------------------------------
-- 5. Stored Procedures
--------------------------------------------------------------------------------

-- Log extraction start
CREATE OR REPLACE PROCEDURE EPM_AUDIT.SP_LOG_EXTRACTION_START (
    p_source_system IN VARCHAR2,
    p_api_endpoint IN VARCHAR2,
    p_batch_id OUT NUMBER
) AS
BEGIN
    INSERT INTO EPM_AUDIT.EXTRACTION_LOG (
        source_system, extraction_start, status, source_api_endpoint
    ) VALUES (
        p_source_system, SYSTIMESTAMP, 'RUNNING', p_api_endpoint
    ) RETURNING batch_id INTO p_batch_id;
    
    COMMIT;
END;
/

-- Log extraction completion
CREATE OR REPLACE PROCEDURE EPM_AUDIT.SP_LOG_EXTRACTION_COMPLETE (
    p_batch_id IN NUMBER,
    p_status IN VARCHAR2,
    p_records_extracted IN NUMBER DEFAULT 0,
    p_records_changed IN NUMBER DEFAULT 0,
    p_error_details IN CLOB DEFAULT NULL,
    p_odi_session_id IN VARCHAR2 DEFAULT NULL,
    p_http_response_code IN NUMBER DEFAULT NULL
) AS
BEGIN
    UPDATE EPM_AUDIT.EXTRACTION_LOG
    SET extraction_end = SYSTIMESTAMP,
        status = p_status,
        records_extracted = p_records_extracted,
        records_changed = p_records_changed,
        error_details = p_error_details,
        odi_session_id = p_odi_session_id,
        http_response_code = p_http_response_code
    WHERE batch_id = p_batch_id;
    
    COMMIT;
END;
/

-- Calculate content hash (wrapper for ODI to call)
CREATE OR REPLACE FUNCTION EPM_AUDIT.FN_CALCULATE_HASH (
    p_content IN CLOB
) RETURN VARCHAR2 AS
    v_hash VARCHAR2(64);
BEGIN
    SELECT LOWER(TO_CHAR(DBMS_CRYPTO.HASH(UTL_I18N.STRING_TO_RAW(p_content, 'AL32UTF8'), DBMS_CRYPTO.HASH_SH256)))
    INTO v_hash
    FROM DUAL;
    
    RETURN v_hash;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
/

-- Check if artifact has changed
CREATE OR REPLACE FUNCTION EPM_AUDIT.FN_HAS_ARTIFACT_CHANGED (
    p_source_system IN VARCHAR2,
    p_artifact_name IN VARCHAR2,
    p_new_hash IN VARCHAR2
) RETURN BOOLEAN AS
    v_last_hash VARCHAR2(64);
BEGIN
    SELECT content_hash
    INTO v_last_hash
    FROM (
        SELECT content_hash
        FROM EPM_AUDIT.ARTIFACTS
        WHERE source_system = p_source_system
          AND artifact_name = p_artifact_name
        ORDER BY extracted_date DESC
    )
    WHERE ROWNUM = 1;
    
    RETURN (v_last_hash IS NULL OR v_last_hash != p_new_hash);
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN TRUE;  -- New artifact
END;
/

--------------------------------------------------------------------------------
-- 6. Data Safe Configuration (Enable Unified Auditing)
--------------------------------------------------------------------------------

-- Enable fine-grained auditing on audit tables (audit the auditor)
BEGIN
    DBMS_FGA.ADD_POLICY(
        object_schema      => 'EPM_AUDIT',
        object_name        => 'ARTIFACTS',
        policy_name        => 'AUDIT_ARTIFACTS_ACCESS',
        statement_types    => 'SELECT,INSERT,UPDATE,DELETE'
    );
    
    DBMS_FGA.ADD_POLICY(
        object_schema      => 'EPM_AUDIT',
        object_name        => 'EXTRACTION_LOG',
        policy_name        => 'AUDIT_LOG_ACCESS',
        statement_types    => 'SELECT,INSERT,UPDATE,DELETE'
    );
END;
/

--------------------------------------------------------------------------------
-- 7. Sample Queries for Retool Integration
--------------------------------------------------------------------------------

-- Get dashboard summary
-- SELECT * FROM EPM_AUDIT.V_DASHBOARD_SUMMARY;

-- Get artifacts with filters
-- SELECT * FROM EPM_AUDIT.ARTIFACTS 
-- WHERE source_system = 'FCCS' 
--   AND extracted_date BETWEEN :start_date AND :end_date;

-- Get changed artifacts
-- SELECT * FROM EPM_AUDIT.V_CHANGED_ARTIFACTS 
-- WHERE source_system = :system
--   AND change_status = 'CHANGED';

-- Get material artifacts
-- SELECT * FROM EPM_AUDIT.V_MATERIAL_ARTIFACTS;

-- Get extraction history
-- SELECT * FROM EPM_AUDIT.EXTRACTION_LOG 
-- WHERE status = 'FAILED'
-- ORDER BY extraction_start DESC;

--------------------------------------------------------------------------------
-- 8. Grant Permissions (run as ADMIN)
--------------------------------------------------------------------------------

-- Grant read access to end users (Retool connection)
-- CREATE USER RETOOL_APP IDENTIFIED BY password;
-- GRANT CREATE SESSION TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.ARTIFACTS TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.EXTRACTION_LOG TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.V_DASHBOARD_SUMMARY TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.V_CHANGED_ARTIFACTS TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.V_MATERIAL_ARTIFACTS TO RETOOL_APP;
-- GRANT SELECT ON EPM_AUDIT.V_EXTRACTION_PERFORMANCE TO RETOOL_APP;

--------------------------------------------------------------------------------
-- END OF SCRIPT
--------------------------------------------------------------------------------

PROMPT Schema creation complete. Grant permissions to EPM_AUDIT and RETOOL_APP users as needed.
