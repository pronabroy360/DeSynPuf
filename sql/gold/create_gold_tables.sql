-- Gold layer model specification.
--
-- Production implementation:
--   src/transform/common.py

-- ---------------------------------------------------------------------------
-- gold_patient_year_summary
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per beneficiary_id and year.
--
-- Purpose:
--   Main analytics and modeling feature table. It combines beneficiary-year
--   demographics, chronic-condition indicators, utilization counts, costs,
--   diagnosis-code breadth, and procedure-code breadth.

-- Representative SQL shape:
CREATE OR REPLACE TABLE gold_patient_year_summary AS
WITH person_years AS (
    SELECT beneficiary_id, year
    FROM silver_beneficiaries
    UNION
    SELECT beneficiary_id, claim_year AS year
    FROM silver_inpatient_claims
    UNION
    SELECT beneficiary_id, claim_year AS year
    FROM silver_outpatient_claims
    UNION
    SELECT beneficiary_id, claim_year AS year
    FROM silver_carrier_claims
    UNION
    SELECT beneficiary_id, service_year AS year
    FROM silver_prescription_events
),
claim_rollup AS (
    SELECT
        beneficiary_id,
        claim_year AS year,
        COUNT(*) FILTER (WHERE claim_type = 'inpatient') AS inpatient_claims_count,
        COUNT(*) FILTER (WHERE claim_type = 'outpatient') AS outpatient_claims_count,
        COUNT(*) FILTER (WHERE claim_type = 'carrier') AS carrier_claims_count,
        SUM(CASE WHEN claim_type = 'inpatient' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS inpatient_total_paid,
        SUM(CASE WHEN claim_type = 'outpatient' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS outpatient_total_paid,
        SUM(CASE WHEN claim_type = 'carrier' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS carrier_total_paid
    FROM (
        SELECT beneficiary_id, claim_year, claim_type, payment_amount FROM silver_inpatient_claims
        UNION ALL
        SELECT beneficiary_id, claim_year, claim_type, payment_amount FROM silver_outpatient_claims
        UNION ALL
        SELECT beneficiary_id, claim_year, claim_type, payment_amount FROM silver_carrier_claims
    )
    GROUP BY beneficiary_id, claim_year
),
rx_rollup AS (
    SELECT
        beneficiary_id,
        service_year AS year,
        COUNT(*) AS prescription_events_count,
        SUM(COALESCE(total_rx_cost, 0)) AS prescription_total_cost
    FROM silver_prescription_events
    GROUP BY beneficiary_id, service_year
)
SELECT
    py.beneficiary_id,
    py.year,
    b.age,
    b.sex_code,
    b.race_code,
    b.state_code,
    b.county_code,
    b.chronic_condition_count,
    COALESCE(c.inpatient_claims_count, 0) AS inpatient_claims_count,
    COALESCE(c.outpatient_claims_count, 0) AS outpatient_claims_count,
    COALESCE(c.carrier_claims_count, 0) AS carrier_claims_count,
    COALESCE(rx.prescription_events_count, 0) AS prescription_events_count,
    COALESCE(c.inpatient_total_paid, 0) AS inpatient_total_paid,
    COALESCE(c.outpatient_total_paid, 0) AS outpatient_total_paid,
    COALESCE(c.carrier_total_paid, 0) AS carrier_total_paid,
    COALESCE(rx.prescription_total_cost, 0) AS prescription_total_cost,
    COALESCE(c.inpatient_total_paid, 0)
        + COALESCE(c.outpatient_total_paid, 0)
        + COALESCE(c.carrier_total_paid, 0)
        + COALESCE(rx.prescription_total_cost, 0) AS total_synthetic_cost
FROM person_years py
LEFT JOIN silver_beneficiaries b
    ON py.beneficiary_id = b.beneficiary_id
   AND py.year = b.year
LEFT JOIN claim_rollup c
    ON py.beneficiary_id = c.beneficiary_id
   AND py.year = c.year
LEFT JOIN rx_rollup rx
    ON py.beneficiary_id = rx.beneficiary_id
   AND py.year = rx.year
WHERE py.year BETWEEN 2008 AND 2010;

-- ---------------------------------------------------------------------------
-- gold_patient_utilization_summary
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per year.
--
-- Measures:
--   total beneficiaries, claim/event counts, and average utilization per
--   beneficiary-year.

-- ---------------------------------------------------------------------------
-- gold_patient_cost_summary
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per year.
--
-- Measures:
--   total, average, median, and p90 synthetic cost plus cost by claim type.

-- ---------------------------------------------------------------------------
-- gold_patient_chronic_condition_summary
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per year and chronic-condition flag.
--
-- Measures:
--   beneficiaries with the flag and average cost with/without the flag.

-- ---------------------------------------------------------------------------
-- gold_high_cost_prediction_dataset
-- ---------------------------------------------------------------------------
-- Grain:
--   one row per beneficiary_id, input_year, and target_year.
--
-- Label:
--   high_cost_next_year = 1 when next-year total_synthetic_cost is at or above
--   that target year's 90th percentile.

-- Representative label SQL:
CREATE OR REPLACE TABLE gold_high_cost_prediction_dataset AS
WITH thresholds AS (
    SELECT
        year,
        QUANTILE_CONT(total_synthetic_cost, 0.90) AS high_cost_threshold
    FROM gold_patient_year_summary
    GROUP BY year
),
target_years AS (
    SELECT
        g.beneficiary_id,
        g.year AS target_year,
        g.total_synthetic_cost AS target_total_synthetic_cost,
        t.high_cost_threshold,
        CASE
            WHEN g.total_synthetic_cost >= t.high_cost_threshold THEN 1
            ELSE 0
        END AS high_cost_next_year
    FROM gold_patient_year_summary g
    INNER JOIN thresholds t
        ON g.year = t.year
)
SELECT
    current_year.*,
    current_year.year AS input_year,
    target_years.target_year,
    target_years.target_total_synthetic_cost,
    target_years.high_cost_threshold AS target_high_cost_threshold,
    target_years.high_cost_next_year
FROM gold_patient_year_summary current_year
INNER JOIN target_years
    ON current_year.beneficiary_id = target_years.beneficiary_id
   AND current_year.year + 1 = target_years.target_year;
