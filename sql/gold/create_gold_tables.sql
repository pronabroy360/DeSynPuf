-- Reference SQL for the Gold layer.
-- The production Gold build is dynamic Python/DuckDB SQL in src/transform/common.py.

-- Core grain:
--   one row per beneficiary_id and year.

-- Core measure logic:
--   total_synthetic_cost =
--       inpatient_total_paid
--     + outpatient_total_paid
--     + carrier_total_paid
--     + prescription_total_cost

-- Core modeling label:
--   high_cost_next_year = 1 when next-year total_synthetic_cost is at or above
--   that target year's 90th percentile.
