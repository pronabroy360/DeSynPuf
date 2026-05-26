-- Reference SQL for the Silver layer.
-- The production Silver build is dynamic Python/DuckDB SQL in src/transform/common.py
-- because CMS files may include optional columns and split files.

CREATE OR REPLACE TABLE silver_beneficiaries AS
SELECT
    desynpuf_id AS beneficiary_id,
    2008 AS year,
    TRY_CAST(TRY_STRPTIME(bene_birth_dt, '%Y%m%d') AS DATE) AS birth_date,
    bene_sex_ident_cd AS sex_code,
    bene_race_cd AS race_code,
    sp_state_code AS state_code
FROM bronze_beneficiary_2008;

-- See src/transform/common.py for the full Silver implementation.
