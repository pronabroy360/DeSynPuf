-- Silver layer model specification.
--
-- Production implementation:
--   src/transform/common.py
--
-- Why Python generates this SQL:
--   CMS DE-SynPUF files can include optional fields and split carrier files.
--   The production transformer checks available columns before creating each
--   SELECT expression, which makes the pipeline more tolerant of file variants.

-- ---------------------------------------------------------------------------
-- silver_beneficiaries
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per beneficiary_id and beneficiary summary year.
--
-- Sources:
--   bronze_beneficiary_2008
--   bronze_beneficiary_2009
--   bronze_beneficiary_2010
--
-- Core transformations:
--   - DESYNPUF_ID -> beneficiary_id
--   - beneficiary year is inferred from the source file
--   - CMS dates are parsed into DATE
--   - age is calculated at year end
--   - chronic-condition indicators are normalized to 0/1
--   - chronic_condition_count sums normalized chronic-condition flags

-- Representative SQL shape:
WITH beneficiary_union AS (
    SELECT
        desynpuf_id AS beneficiary_id,
        2008 AS year,
        TRY_CAST(TRY_STRPTIME(bene_birth_dt, '%Y%m%d') AS DATE) AS birth_date,
        TRY_CAST(TRY_STRPTIME(bene_death_dt, '%Y%m%d') AS DATE) AS death_date,
        bene_sex_ident_cd AS sex_code,
        bene_race_cd AS race_code,
        sp_state_code AS state_code,
        bene_county_cd AS county_code,
        CASE WHEN sp_diabetes = '1' THEN 1 ELSE 0 END AS diabetes,
        CASE WHEN sp_chf = '1' THEN 1 ELSE 0 END AS heart_failure
    FROM bronze_beneficiary_2008
)
SELECT
    beneficiary_id,
    year,
    birth_date,
    death_date,
    DATE_DIFF('year', birth_date, CAST(CAST(year AS VARCHAR) || '-12-31' AS DATE))::INTEGER AS age,
    sex_code,
    race_code,
    state_code,
    county_code,
    diabetes,
    heart_failure,
    diabetes + heart_failure AS chronic_condition_count
FROM beneficiary_union;

-- ---------------------------------------------------------------------------
-- silver_inpatient_claims / silver_outpatient_claims / silver_carrier_claims
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per claim record.
--
-- Core transformations:
--   - DESYNPUF_ID -> beneficiary_id
--   - CLM_ID -> claim_id
--   - CLM_FROM_DT / CLM_THRU_DT parsed into DATE
--   - claim_year extracted from claim_start_date
--   - CLM_PMT_AMT cast to payment_amount
--   - diagnosis, procedure, and HCPCS columns standardized by position
--   - carrier A/B files are unioned into silver_carrier_claims

-- ---------------------------------------------------------------------------
-- silver_prescription_events
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per Part D prescription drug event.
--
-- Core transformations:
--   - DESYNPUF_ID -> beneficiary_id
--   - PDE_ID -> event_id
--   - SRVC_DT parsed into service_date
--   - service_year extracted from service_date
--   - TOT_RX_CST_AMT cast to total_rx_cost

-- ---------------------------------------------------------------------------
-- silver_diagnosis_codes / silver_procedure_codes
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per non-null diagnosis/procedure code position per claim.
--
-- Purpose:
--   These long-format tables support feature engineering such as unique
--   diagnosis-code counts and unique procedure-code counts by patient-year.
