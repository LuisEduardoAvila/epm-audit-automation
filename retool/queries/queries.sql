-- Retool Resource Queries for EPM Audit Dashboard
-- Oracle Autonomous Database Connection

--------------------------------------------------------------------------------
-- 1. Dashboard Summary Cards
--------------------------------------------------------------------------------

-- Resource: Oracle DB - Connection Type
-- Query Name: getDashboardSummary
-- Transform: Table → Summary Cards

SELECT 
    source_system,
    total_artifacts,
    last_extraction,
    extraction_days,
    artifacts_last_24h,
    artifacts_last_7d,
    unique_artifacts
FROM EPM_AUDIT.V_DASHBOARD_SUMMARY;

-- Transform Results:
-- Map columns to card components in Retool
-- source_system: "FCCS" → Card Title
-- last_extraction: Date → Subtitle
-- artifacts_last_24h: Count → Main metric
-- unique_artifacts: Count → Secondary metric

--------------------------------------------------------------------------------
-- 2. Artifacts List (Filterable Table)
--------------------------------------------------------------------------------

-- Query Name: getArtifacts
-- Parameters:
--   {{source_system_filter}} (string): 'FCCS', 'PBCS', 'EDM', 'DE', 'ARCS', 'PCM', or 'ALL'
--   {{start_date}} (date): Filter start date
--   {{end_date}} (date): Filter end date
--   {{artifact_type_filter}} (string, optional): Filter by type
--   {{search_term}} (string, optional): Full-text search on artifact_name
-- Pagination: Server-side via OFFSET/FETCH

SELECT 
    a.artifact_id,
    a.source_system,
    a.artifact_type,
    a.artifact_name,
    a.extracted_date,
    a.content_hash,
    CASE 
        WHEN a.extracted_date > SYSDATE - 1 THEN 'NEW'
        WHEN EXISTS (
            SELECT 1 FROM EPM_AUDIT.ARTIFACTS a2 
            WHERE a2.source_system = a.source_system 
              AND a2.artifact_name = a.artifact_name
              AND a2.extracted_date < a.extracted_date
              AND a2.content_hash != a.content_hash
        ) THEN 'CHANGED'
        ELSE 'UNCHANGED'
    END as change_status,
    el.status as extraction_status,
    el.odi_session_id
FROM EPM_AUDIT.ARTIFACTS a
LEFT JOIN EPM_AUDIT.EXTRACTION_LOG el ON a.extraction_batch_id = el.batch_id
WHERE 
    ({{!source_system_filter}} OR a.source_system = {{source_system_filter}})
    AND a.extracted_date BETWEEN {{start_date}} AND {{end_date}}
    AND ({{!artifact_type_filter}} OR a.artifact_type = {{artifact_type_filter}})
    AND ({{!search_term}} OR LOWER(a.artifact_name) LIKE CONCAT('%', LOWER({{search_term}}), '%'))
ORDER BY a.extracted_date DESC
OFFSET {{(page_number - 1) * page_size}} ROWS
FETCH NEXT {{page_size}} ROWS ONLY;

--------------------------------------------------------------------------------
-- 3. Changed Artifacts Only
--------------------------------------------------------------------------------

-- Query Name: getChangedArtifacts
-- Useful for: Alert/Review workflow

SELECT 
    artifact_id,
    source_system,
    artifact_type,
    artifact_name,
    extracted_date,
    previous_extraction,
    change_status,
    DATEDIFF('hour', previous_extraction, extracted_date) as hours_since_previous
FROM EPM_AUDIT.V_CHANGED_ARTIFACTS
WHERE change_status IN ('NEW', 'CHANGED')
  AND ({{!source_system_filter}} OR source_system = {{source_system_filter}})
  AND extracted_date >= {{start_date}}
ORDER BY extracted_date DESC;

--------------------------------------------------------------------------------
-- 4. Material Artifacts (High-Priority)
--------------------------------------------------------------------------------

-- Query Name: getMaterialArtifacts
-- Flags important artifacts based on change frequency

SELECT 
    source_system,
    artifact_name,
    change_events,
    last_changed,
    materiality_level,
    CASE materiality_level
        WHEN 'CRITICAL' THEN '#FF4444'
        WHEN 'HIGH' THEN '#FF8800'
        WHEN 'MEDIUM' THEN '#FFCC00'
    END as alert_color
FROM EPM_AUDIT.V_MATERIAL_ARTIFACTS
WHERE ({{!source_system_filter}} OR source_system = {{source_system_filter}})
ORDER BY change_events DESC;

--------------------------------------------------------------------------------
-- 5. Artifact Detail (for drill-down)
--------------------------------------------------------------------------------

-- Query Name: getArtifactDetail
-- Parameters: {{artifact_id}} (number)

SELECT 
    a.*,
    el.extraction_start,
    el.extraction_end,
    el.status,
    el.error_details
FROM EPM_AUDIT.ARTIFACTS a
LEFT JOIN EPM_AUDIT.EXTRACTION_LOG el ON a.extraction_batch_id = el.batch_id
WHERE a.artifact_id = {{artifact_id}};

-- Compare with previous version
-- Query Name: getArtifactPreviousVersion
-- Parameters: {{artifact_id}} (number), {{artifact_name}} (string), {{source_system}} (string)

SELECT 
    artifact_id,
    extracted_date,
    content_hash,
    artifact_content
FROM EPM_AUDIT.ARTIFACTS
WHERE source_system = {{source_system}}
  AND artifact_name = {{artifact_name}}
  AND extracted_date < (
      SELECT extracted_date FROM EPM_AUDIT.ARTIFACTS WHERE artifact_id = {{artifact_id}}
  )
ORDER BY extracted_date DESC
FETCH FIRST 1 ROW ONLY;

--------------------------------------------------------------------------------
-- 6. Extraction Log / Monitoring
--------------------------------------------------------------------------------

-- Query Name: getExtractionLog
-- Parameters:
--   {{status_filter}} (optional): 'SUCCESS', 'FAILED', 'PARTIAL', 'RUNNING'
--   {{source_system_filter}} (optional)
--   {{date_range}} (number): Days back to search

SELECT 
    batch_id,
    source_system,
    extraction_start,
    extraction_end,
    ROUND(EXTRACT(SECOND FROM (extraction_end - extraction_start))) as duration_seconds,
    records_extracted,
    records_changed,
    status,
    error_details,
    retry_count,
    CASE status
        WHEN 'SUCCESS' THEN '✅'
        WHEN 'FAILED' THEN '❌'
        WHEN 'PARTIAL' THEN '⚠️'
        WHEN 'RUNNING' THEN '⏳'
    END as status_emoji
FROM EPM_AUDIT.EXTRACTION_LOG
WHERE extraction_start >= SYSTIMESTAMP - INTERVAL '{{date_range}}' DAY
  AND ({{!status_filter}} OR status = {{status_filter}})
  AND ({{!source_system_filter}} OR source_system = {{source_system_filter}})
ORDER BY extraction_start DESC;

-- Failed extractions (for alerting)
-- Query Name: getFailedExtractions
-- Trigger: Scheduled query (every 15 min)

SELECT 
    batch_id,
    source_system,
    extraction_start,
    status,
    error_details,
    http_response_code,
    odi_session_id
FROM EPM_AUDIT.EXTRACTION_LOG
WHERE status = 'FAILED'
  AND extraction_start >= SYSTIMESTAMP - INTERVAL '1' HOUR
ORDER BY extraction_start DESC;

--------------------------------------------------------------------------------
-- 7. Export / Report Generation
--------------------------------------------------------------------------------

-- Query Name: exportArtifactsSQL
-- For: Export to CSV/Excel
-- Note: Retool can export query results directly

SELECT 
    a.source_system,
    a.artifact_type,
    a.artifact_name,
    a.extracted_date,
    CASE 
        WHEN a.content_hash != LAG(a.content_hash) OVER (
            PARTITION BY a.source_system, a.artifact_name 
            ORDER BY a.extracted_date
        ) THEN 'CHANGED'
        ELSE 'UNCHANGED'
    END as change_status,
    el.status as extraction_status
FROM EPM_AUDIT.ARTIFACTS a
LEFT JOIN EPM_AUDIT.EXTRACTION_LOG el ON a.extraction_batch_id = el.batch_id
WHERE a.extracted_date BETWEEN {{export_start_date}} AND {{export_end_date}}
  AND ({{!source_system_filter}} OR a.source_system = {{source_system_filter}})
ORDER BY a.source_system, a.artifact_type, a.artifact_name, a.extracted_date;

--------------------------------------------------------------------------------
-- 8. Statistics / Analytics
--------------------------------------------------------------------------------

-- Query Name: getExtractionStats
-- Dashboard: Charts

SELECT 
    source_system,
    TRUNC(extracted_date) as extraction_date,
    COUNT(*) as artifact_count,
    COUNT(DISTINCT artifact_name) as unique_artifacts,
    COUNT(CASE WHEN content_hash != LAG(content_hash) OVER (
        PARTITION BY source_system, artifact_name 
        ORDER BY extracted_date
    ) THEN 1 END) as changed_count
FROM EPM_AUDIT.ARTIFACTS
WHERE extracted_date >= SYSDATE - INTERVAL '30' DAY
GROUP BY source_system, TRUNC(extracted_date)
ORDER BY extraction_date;

-- Materiality stats
-- Query Name: getMaterialityStats

SELECT 
    source_system,
    COUNT(CASE WHEN materiality_level = 'CRITICAL' THEN 1 END) as critical_count,
    COUNT(CASE WHEN materiality_level = 'HIGH' THEN 1 END) as high_count,
    COUNT(CASE WHEN materiality_level = 'MEDIUM' THEN 1 END) as medium_count
FROM EPM_AUDIT.V_MATERIAL_ARTIFACTS
GROUP BY source_system;

--------------------------------------------------------------------------------
-- 9. Filter Options (for dropdowns)
--------------------------------------------------------------------------------

-- Query Name: getSourceSystems
SELECT DISTINCT source_system as value, source_system as label 
FROM EPM_AUDIT.ARTIFACTS 
ORDER BY source_system;

-- Query Name: getArtifactTypes
-- Parameters: {{source_system}} (optional)
SELECT DISTINCT artifact_type as value, artifact_type as label 
FROM EPM_AUDIT.ARTIFACTS 
WHERE ({{!source_system}} OR source_system = {{source_system}})
ORDER BY artifact_type;

--------------------------------------------------------------------------------
-- 10. Insert/Update Operations (if enabled in Retool)
--------------------------------------------------------------------------------

-- Note: Typically read-only for audit data
-- If you need write operations, create separate secured queries

-- Example: Mark artifact as reviewed
-- Query Name: markArtifactReviewed
-- Requires: UPDATE permission

/*
UPDATE EPM_AUDIT.ARTIFACTS 
SET reviewed_by = {{current_user.email}},
    reviewed_date = SYSTIMESTAMP,
    review_notes = {{notes}}
WHERE artifact_id = {{artifact_id}};

-- Requires table modification:
ALTER TABLE EPM_AUDIT.ARTIFACTS ADD (
    reviewed_by VARCHAR2(100),
    reviewed_date TIMESTAMP,
    review_notes VARCHAR2(1000)
);
*/
