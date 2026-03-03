-- Sample ODI 12c Mapping: FCCS Artifacts
-- This SQL represents what the ODI mapping will execute
-- ODI Mapping: M_FCCS_ARTIFACTS

-- Step 1: Create staging table for JSON response
CREATE GLOBAL TEMPORARY TABLE ODI_STG_FCCS_RESPONSE (
    session_id VARCHAR2(100),
    response_json CLOB,
    http_status NUMBER,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ON COMMIT PRESERVE ROWS;

-- Step 2: Staging table for parsed artifacts
CREATE GLOBAL TEMPORARY TABLE ODI_STG_FCCS_ARTIFACTS (
    artifact_type VARCHAR2(50),
    artifact_name VARCHAR2(500),
    artifact_content CLOB,
    content_hash VARCHAR2(64),
    batch_id NUMBER
) ON COMMIT PRESERVE ROWS;

-- Step 3: ODI Mapping logic (pseudocode for ODI Studio implementation)
/*
ODI MAPPING: M_FCCS_ARTIFACTS
Source: HTTP Data Server (FCCS REST API)
    - URL: https://<pod>.oraclecloud.com/epm/rest/v1/applications
    - Method: GET
    - Headers: Authorization: Bearer <token>
    
Target: Autonomous DB (EPM_AUDIT.FCCS_ARTIFACTS)

Transformation Flow:
1. HTTP Call Step
   - Use ODI HTTP tool
   - Store response in ODI_STG_FCCS_RESPONSE
   
2. JSON Parsing Step
   INSERT INTO ODI_STG_FCCS_ARTIFACTS (artifact_type, artifact_name, artifact_content)
   SELECT 
       jt.artifact_type,
       jt.artifact_name,
       jt.artifact_content
   FROM ODI_STG_FCCS_RESPONSE r,
        JSON_TABLE(r.response_json, '$.items[*]'
            COLUMNS (
                artifact_type VARCHAR2(50) PATH '$.artifactType',
                artifact_name VARCHAR2(500) PATH '$.name',
                artifact_content CLOB FORMAT JSON PATH '$'
            )
        ) jt
   WHERE r.http_status = 200;

3. Hash Calculation Step
   UPDATE ODI_STG_FCCS_ARTIFACTS
   SET content_hash = LOWER(
       TO_CHAR(
           DBMS_CRYPTO.HASH(
               UTL_I18N.STRING_TO_RAW(artifact_content, 'AL32UTF8'),
               DBMS_CRYPTO.HASH_SH256
           )
       )
   );

4. Load to Target
   INSERT INTO EPM_AUDIT.ARTIFACTS (
       source_system,
       artifact_type,
       artifact_name,
       artifact_content,
       content_hash,
       extraction_batch_id
   )
   SELECT 
       'FCCS',
       artifact_type,
       artifact_name,
       artifact_content,
       content_hash,
       :batch_id
   FROM ODI_STG_FCCS_ARTIFACTS;

5. Cleanup
   TRUNCATE TABLE ODI_STG_FCCS_RESPONSE;
   TRUNCATE TABLE ODI_STG_FCCS_ARTIFACTS;
*/

-- Alternative: Single SQL approach for ODI Mapping
-- This can be used in ODI's "SELECT" clause of LKM

INSERT INTO EPM_AUDIT.ARTIFACTS (
    source_system,
    artifact_type,
    artifact_name,
    artifact_content,
    content_hash,
    extraction_batch_id
)
SELECT 
    'FCCS' as source_system,
    jt.artifact_type,
    jt.artifact_name,
    jt.artifact_content,
    LOWER(TO_CHAR(
        DBMS_CRYPTO.HASH(
            UTL_I18N.STRING_TO_RAW(jt.artifact_content, 'AL32UTF8'),
            DBMS_CRYPTO.HASH_SH256
        )
    )) as content_hash,
    :batch_id as extraction_batch_id
FROM (
    -- In ODI, this would be the HTTP response
    -- For now, using placeholder
    SELECT :http_response as response_json, 200 as http_status 
    FROM DUAL
) r,
JSON_TABLE(r.response_json, '$[*]'
    COLUMNS (
        artifact_type VARCHAR2(50) PATH '$.type',
        artifact_name VARCHAR2(500) PATH '$.name',
        artifact_content CLOB FORMAT JSON PATH '$'
    )
) jt
WHERE r.http_status = 200;

COMMIT;
