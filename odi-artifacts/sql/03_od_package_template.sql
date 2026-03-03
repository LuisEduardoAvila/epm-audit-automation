-- ODI Package: PKG_FCCS_EXTRACT
-- Orchestration with error handling and retry logic
-- This script is a template for creating the ODI Package in Studio

/*
ODI PACKAGE: PKG_FCCS_EXTRACT
Description: Extract all FCCS artifacts with error handling and retry

PACKAGE STEPS (in ODI Studio):
================================================================================
STEP 1: Initialize (ODI Procedure)
------------------------------------
Name: P_INIT_FCCS_EXTRACTION
Type: Procedure
Code:
    DECLARE
        v_batch_id NUMBER;
    BEGIN
        EPM_AUDIT.SP_LOG_EXTRACTION_START(
            p_source_system => 'FCCS',
            p_api_endpoint => '/epm/rest/v1/applications',
            p_batch_id => v_batch_id
        );
        
        -- Store batch_id in ODI variable for use in subsequent steps
        <%=odiRef.setVal("BATCH_ID", "v_batch_id")%>;
    END;

STEP 2: Extract FCCS Artifacts (ODI Mapping)
--------------------------------------------
Name: M_FCCS_ARTIFACTS
Type: Mapping
LKM: LKM HTTP to SQL
IKM: IKM SQL to Oracle
    - Use ODI variable #BATCH_ID for extraction_batch_id

STEP 3: Update Success (ODI Procedure)
--------------------------------------
Name: P_COMPLETE_SUCCESS
Type: Procedure
On Success Only
Code:
    BEGIN
        EPM_AUDIT.SP_LOG_EXTRACTION_COMPLETE(
            p_batch_id => <%=odiRef.getVal("BATCH_ID")%>,
            p_status => 'SUCCESS',
            p_records_extracted => <%=odiRef.getVal("NB_INSERT")%>,
            p_records_changed => 0,  -- Can calculate if needed
            p_odi_session_id => <%=odiRef.getSession("SESS_NO")%>
        );
    END;

STEP 4: Handle Error (ODI Procedure)  
-------------------------------------
Name: P_HANDLE_ERROR
Type: Procedure
On Error Only
Code:
    DECLARE
        v_error_msg VARCHAR2(4000);
    BEGIN
        v_error_msg := SQLERRM;
        
        EPM_AUDIT.SP_LOG_EXTRACTION_COMPLETE(
            p_batch_id => <%=odiRef.getVal("BATCH_ID")%>,
            p_status => 'FAILED',
            p_error_details => v_error_msg,
            p_odi_session_id => <%=odiRef.getSession("SESS_NO")%>,
            p_http_response_code => <%=odiRef.getVal("HTTP_STATUS")%>
        );
        
        -- Send alert
        -- (Can integrate with email/Slack via ODI tools)
    END;

================================================================================
ODI PACKAGE: PKG_MASTER (Runs all EPM extractions)
================================================================================
STEP 1: PKG_FCCS_EXTRACT
STEP 2: PKG_PBCS_EXTRACT
STEP 3: PKG_EDM_EXTRACT
STEP 4: PKG_DE_EXTRACT
STEP 5: PKG_ARCS_EXTRACT
STEP 6: PKG_PCM_EXTRACT

================================================================================
ODI SCENARIOS (Runnable executions)
================================================================================
- SCEN_FCCS_DAILY: Runs PKG_FCCS_EXTRACT
- SCEN_EPM_ALL: Runs PKG_MASTER
    - Schedule via ODI Agent or external scheduler

================================================================================
ODI VARIABLES
================================================================================
- BATCH_ID: Stores current extraction batch ID
- HTTP_STATUS: Stores HTTP response code
- RETRY_COUNT: Retry attempt counter
- START_DATE: For incremental extraction

================================================================================
RETRY LOGIC PATTERN
================================================================================
For APIs with rate limiting (429) or transient errors:

ODI Procedure P_RETRY_WRAPPER:
    DECLARE
        v_retry NUMBER := 0;
        v_max_retries NUMBER := 3;
        v_success BOOLEAN := FALSE;
    BEGIN
        WHILE v_retry < v_max_retries AND NOT v_success LOOP
            BEGIN
                -- Attempt extraction mapping
                <%=odiRef.callMapping("M_FCCS_ARTIFACTS")%>;
                v_success := TRUE;
                
            EXCEPTION
                WHEN OTHERS THEN
                    v_retry := v_retry + 1;
                    
                    IF v_retry >= v_max_retries THEN
                        RAISE_APPLICATION_ERROR(-20001, 'Max retries exceeded');
                    END IF;
                    
                    -- Exponential backoff: 2^retry seconds
                    DBMS_LOCK.SLEEP(POWER(2, v_retry));
            END;
        END LOOP;
    END;

================================================================================
*/

-- Additional helper procedures for error handling

-- Procedure to check for rate limiting and apply backoff
CREATE OR REPLACE PROCEDURE EPM_AUDIT.SP_CHECK_RATE_LIMIT (
    p_http_status IN NUMBER,
    p_retry_count IN OUT NUMBER,
    p_should_retry OUT BOOLEAN
) AS
BEGIN
    IF p_http_status IN (429, 500, 503) THEN
        -- Rate limited or server error - retry
        p_retry_count := p_retry_count + 1;
        
        IF p_retry_count <= 3 THEN
            p_should_retry := TRUE;
            -- Wait with exponential backoff
            DBMS_LOCK.SLEEP(POWER(2, p_retry_count));
        ELSE
            p_should_retry := FALSE;
        END IF;
    ELSE
        p_should_retry := FALSE;
    END IF;
END;
/

-- Procedure for incremental extraction (only changed artifacts)
CREATE OR REPLACE PROCEDURE EPM_AUDIT.SP_GET_INCREMENTAL_ARTIFACTS (
    p_source_system IN VARCHAR2,
    p_last_extract_date IN TIMESTAMP,
    p_results OUT SYS_REFCURSOR
) AS
BEGIN
    -- Return artifacts modified since last extraction
    -- This would be used by ODI to filter API calls
    OPEN p_results FOR
    SELECT DISTINCT artifact_name
    FROM EPM_AUDIT.ARTIFACTS
    WHERE source_system = p_source_system
      AND extracted_date > NVL(p_last_extract_date, SYSTIMESTAMP - INTERVAL '1' DAY);
END;
/
