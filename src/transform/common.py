from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import duckdb


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
YEARS = (2008, 2009, 2010)

CHRONIC_CONDITIONS = {
    "alzheimers": "sp_alzhdmta",
    "heart_failure": "sp_chf",
    "kidney_disease": "sp_chrnkidn",
    "cancer": "sp_cncr",
    "copd": "sp_copd",
    "depression": "sp_depressn",
    "diabetes": "sp_diabetes",
    "ischemic_heart": "sp_ischmcht",
    "osteoporosis": "sp_osteoprs",
    "rheumatoid_arthritis": "sp_ra_oa",
    "stroke_tia": "sp_strketia",
}


def qident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(result and result[0])


def table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    if not table_exists(con, table_name):
        return set()
    rows = con.execute(f"PRAGMA table_info({qident(table_name)})").fetchall()
    return {row[1] for row in rows}


def raw_text(cols: set[str], column: str) -> str:
    if column not in cols:
        return "CAST(NULL AS VARCHAR)"
    return f"NULLIF(TRIM(CAST({qident(column)} AS VARCHAR)), '')"


def text_expr(cols: set[str], column: str, alias: str) -> str:
    return f"{raw_text(cols, column)} AS {qident(alias)}"


def int_expr(cols: set[str], column: str, alias: str) -> str:
    return f"TRY_CAST({raw_text(cols, column)} AS INTEGER) AS {qident(alias)}"


def double_expr(cols: set[str], column: str, alias: str) -> str:
    return f"TRY_CAST(REPLACE({raw_text(cols, column)}, ',', '') AS DOUBLE) AS {qident(alias)}"


def date_expr(cols: set[str], column: str, alias: str) -> str:
    raw = raw_text(cols, column)
    return f"""
    CAST(
        COALESCE(
            TRY_STRPTIME({raw}, '%Y%m%d'),
            TRY_STRPTIME({raw}, '%Y-%m-%d'),
            TRY_STRPTIME({raw}, '%m/%d/%Y')
        ) AS DATE
    ) AS {qident(alias)}
    """


def flag_expr(cols: set[str], column: str, alias: str) -> str:
    raw = raw_text(cols, column)
    return f"""
    CASE
        WHEN UPPER({raw}) IN ('1', 'Y', 'YES', 'TRUE') THEN 1
        ELSE 0
    END AS {qident(alias)}
    """


def numbered_text_exprs(
    cols: set[str],
    source_prefix: str,
    alias_prefix: str,
    count: int,
) -> list[str]:
    return [
        text_expr(cols, f"{source_prefix}_{idx}", f"{alias_prefix}_{idx}")
        for idx in range(1, count + 1)
    ]


def create_empty_table(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    schema: Sequence[tuple[str, str]],
) -> None:
    columns_sql = ",\n        ".join(f"{qident(name)} {dtype}" for name, dtype in schema)
    con.execute(f"CREATE OR REPLACE TABLE {qident(table_name)} (\n        {columns_sql}\n    )")


def beneficiary_schema() -> list[tuple[str, str]]:
    return [
        ("beneficiary_id", "VARCHAR"),
        ("year", "INTEGER"),
        ("birth_date", "DATE"),
        ("death_date", "DATE"),
        ("age", "INTEGER"),
        ("sex_code", "VARCHAR"),
        ("race_code", "VARCHAR"),
        ("state_code", "VARCHAR"),
        ("county_code", "VARCHAR"),
        ("esrd_indicator", "VARCHAR"),
        ("hi_coverage_months", "INTEGER"),
        ("smi_coverage_months", "INTEGER"),
        ("hmo_coverage_months", "INTEGER"),
        ("part_d_coverage_months", "INTEGER"),
        ("medicare_ip_reimbursement", "DOUBLE"),
        ("beneficiary_ip_responsibility", "DOUBLE"),
        ("primary_payer_ip_payment", "DOUBLE"),
        ("medicare_op_reimbursement", "DOUBLE"),
        ("beneficiary_op_responsibility", "DOUBLE"),
        ("primary_payer_op_payment", "DOUBLE"),
        ("medicare_carrier_reimbursement", "DOUBLE"),
        ("beneficiary_carrier_responsibility", "DOUBLE"),
        ("primary_payer_carrier_payment", "DOUBLE"),
        *[(name, "INTEGER") for name in CHRONIC_CONDITIONS],
        ("chronic_condition_count", "INTEGER"),
    ]


def claim_schema(max_diagnoses: int, max_procedures: int, max_hcpcs: int = 0) -> list[tuple[str, str]]:
    schema = [
        ("beneficiary_id", "VARCHAR"),
        ("claim_id", "VARCHAR"),
        ("claim_type", "VARCHAR"),
        ("claim_start_date", "DATE"),
        ("claim_end_date", "DATE"),
        ("claim_year", "INTEGER"),
        ("payment_amount", "DOUBLE"),
        ("primary_payer_amount", "DOUBLE"),
        ("provider_number", "VARCHAR"),
        ("source_split", "VARCHAR"),
        ("admission_date", "DATE"),
        ("discharge_date", "DATE"),
        ("utilization_days", "INTEGER"),
        ("drg_code", "VARCHAR"),
    ]
    schema.extend((f"diagnosis_code_{idx}", "VARCHAR") for idx in range(1, max_diagnoses + 1))
    schema.extend((f"procedure_code_{idx}", "VARCHAR") for idx in range(1, max_procedures + 1))
    schema.extend((f"hcpcs_code_{idx}", "VARCHAR") for idx in range(1, max_hcpcs + 1))
    return schema


def prescription_schema() -> list[tuple[str, str]]:
    return [
        ("beneficiary_id", "VARCHAR"),
        ("event_id", "VARCHAR"),
        ("service_date", "DATE"),
        ("service_year", "INTEGER"),
        ("product_service_id", "VARCHAR"),
        ("quantity_dispensed", "DOUBLE"),
        ("days_supply", "INTEGER"),
        ("patient_pay_amount", "DOUBLE"),
        ("total_rx_cost", "DOUBLE"),
    ]


def create_silver_beneficiaries(con: duckdb.DuckDBPyConnection) -> None:
    queries: list[str] = []
    for year in YEARS:
        source_table = f"bronze_beneficiary_{year}"
        cols = table_columns(con, source_table)
        if not cols:
            continue
        fields = [
            text_expr(cols, "desynpuf_id", "beneficiary_id"),
            f"{year} AS year",
            date_expr(cols, "bene_birth_dt", "birth_date"),
            date_expr(cols, "bene_death_dt", "death_date"),
            text_expr(cols, "bene_sex_ident_cd", "sex_code"),
            text_expr(cols, "bene_race_cd", "race_code"),
            text_expr(cols, "sp_state_code", "state_code"),
            text_expr(cols, "bene_county_cd", "county_code"),
            text_expr(cols, "bene_esrd_ind", "esrd_indicator"),
            int_expr(cols, "bene_hi_cvrage_tot_mons", "hi_coverage_months"),
            int_expr(cols, "bene_smi_cvrage_tot_mons", "smi_coverage_months"),
            int_expr(cols, "bene_hmo_cvrage_tot_mons", "hmo_coverage_months"),
            int_expr(cols, "plan_cvrg_mos_num", "part_d_coverage_months"),
            double_expr(cols, "medreimb_ip", "medicare_ip_reimbursement"),
            double_expr(cols, "benres_ip", "beneficiary_ip_responsibility"),
            double_expr(cols, "pppymt_ip", "primary_payer_ip_payment"),
            double_expr(cols, "medreimb_op", "medicare_op_reimbursement"),
            double_expr(cols, "benres_op", "beneficiary_op_responsibility"),
            double_expr(cols, "pppymt_op", "primary_payer_op_payment"),
            double_expr(cols, "medreimb_car", "medicare_carrier_reimbursement"),
            double_expr(cols, "benres_car", "beneficiary_carrier_responsibility"),
            double_expr(cols, "pppymt_car", "primary_payer_carrier_payment"),
        ]
        fields.extend(flag_expr(cols, source, alias) for alias, source in CHRONIC_CONDITIONS.items())
        queries.append(f"SELECT\n            {', '.join(fields)}\n        FROM {qident(source_table)}")

    if not queries:
        create_empty_table(con, "silver_beneficiaries", beneficiary_schema())
        return

    chronic_sum = " + ".join(f"COALESCE({qident(name)}, 0)" for name in CHRONIC_CONDITIONS)
    union_sql = "\n        UNION ALL\n        ".join(queries)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver_beneficiaries AS
        SELECT
            beneficiary_id,
            year,
            birth_date,
            death_date,
            CASE
                WHEN birth_date IS NULL THEN NULL
                ELSE DATE_DIFF('year', birth_date, CAST(CAST(year AS VARCHAR) || '-12-31' AS DATE))::INTEGER
            END AS age,
            sex_code,
            race_code,
            state_code,
            county_code,
            esrd_indicator,
            hi_coverage_months,
            smi_coverage_months,
            hmo_coverage_months,
            part_d_coverage_months,
            medicare_ip_reimbursement,
            beneficiary_ip_responsibility,
            primary_payer_ip_payment,
            medicare_op_reimbursement,
            beneficiary_op_responsibility,
            primary_payer_op_payment,
            medicare_carrier_reimbursement,
            beneficiary_carrier_responsibility,
            primary_payer_carrier_payment,
            {', '.join(qident(name) for name in CHRONIC_CONDITIONS)},
            ({chronic_sum})::INTEGER AS chronic_condition_count
        FROM (
            {union_sql}
        ) beneficiaries
        WHERE beneficiary_id IS NOT NULL
        """
    )


def _create_silver_claims(
    con: duckdb.DuckDBPyConnection,
    target_table: str,
    sources: Sequence[tuple[str, str]],
    claim_type: str,
    max_diagnoses: int,
    max_procedures: int,
    max_hcpcs: int,
    diagnosis_prefix: str = "icd9_dgns_cd",
    procedure_prefix: str = "icd9_prcdr_cd",
    hcpcs_prefix: str = "hcpcs_cd",
) -> None:
    queries: list[str] = []
    for source_table, source_split in sources:
        cols = table_columns(con, source_table)
        if not cols:
            continue
        fields = [
            text_expr(cols, "desynpuf_id", "beneficiary_id"),
            text_expr(cols, "clm_id", "claim_id"),
            f"{sql_literal(claim_type)} AS claim_type",
            date_expr(cols, "clm_from_dt", "claim_start_date"),
            date_expr(cols, "clm_thru_dt", "claim_end_date"),
            double_expr(cols, "clm_pmt_amt", "payment_amount"),
            double_expr(cols, "nch_prmry_pyr_clm_pd_amt", "primary_payer_amount"),
            text_expr(cols, "prvdr_num", "provider_number"),
            f"{sql_literal(source_split)} AS source_split",
            date_expr(cols, "clm_admsn_dt", "admission_date"),
            date_expr(cols, "nch_bene_dschrg_dt", "discharge_date"),
            int_expr(cols, "clm_utlztn_day_cnt", "utilization_days"),
            text_expr(cols, "clm_drg_cd", "drg_code"),
            *numbered_text_exprs(cols, diagnosis_prefix, "diagnosis_code", max_diagnoses),
            *numbered_text_exprs(cols, procedure_prefix, "procedure_code", max_procedures),
            *numbered_text_exprs(cols, hcpcs_prefix, "hcpcs_code", max_hcpcs),
        ]
        queries.append(
            f"""
            SELECT
                *,
                EXTRACT(YEAR FROM claim_start_date)::INTEGER AS claim_year
            FROM (
                SELECT
                    {', '.join(fields)}
                FROM {qident(source_table)}
            ) raw_claims
            WHERE beneficiary_id IS NOT NULL
            """
        )

    if not queries:
        create_empty_table(con, target_table, claim_schema(max_diagnoses, max_procedures, max_hcpcs))
        return

    union_sql = "\n        UNION ALL\n        ".join(queries)
    ordered_columns = [name for name, _ in claim_schema(max_diagnoses, max_procedures, max_hcpcs)]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {qident(target_table)} AS
        SELECT {', '.join(qident(name) for name in ordered_columns)}
        FROM (
            {union_sql}
        ) claims
        """
    )


def create_silver_inpatient_claims(con: duckdb.DuckDBPyConnection) -> None:
    _create_silver_claims(
        con,
        target_table="silver_inpatient_claims",
        sources=[("bronze_inpatient_claims", "all")],
        claim_type="inpatient",
        max_diagnoses=10,
        max_procedures=6,
        max_hcpcs=0,
    )


def create_silver_outpatient_claims(con: duckdb.DuckDBPyConnection) -> None:
    _create_silver_claims(
        con,
        target_table="silver_outpatient_claims",
        sources=[("bronze_outpatient_claims", "all")],
        claim_type="outpatient",
        max_diagnoses=10,
        max_procedures=6,
        max_hcpcs=45,
    )


def create_silver_carrier_claims(con: duckdb.DuckDBPyConnection) -> None:
    _create_silver_claims(
        con,
        target_table="silver_carrier_claims",
        sources=[
            ("bronze_carrier_claims_a", "a"),
            ("bronze_carrier_claims_b", "b"),
        ],
        claim_type="carrier",
        max_diagnoses=13,
        max_procedures=13,
        max_hcpcs=0,
        diagnosis_prefix="line_icd9_dgns_cd",
        procedure_prefix="line_hcpcs_cd",
    )


def create_silver_prescription_events(con: duckdb.DuckDBPyConnection) -> None:
    source_table = "bronze_prescription_drug_events"
    cols = table_columns(con, source_table)
    if not cols:
        create_empty_table(con, "silver_prescription_events", prescription_schema())
        return

    fields = [
        text_expr(cols, "desynpuf_id", "beneficiary_id"),
        text_expr(cols, "pde_id", "event_id"),
        date_expr(cols, "srvc_dt", "service_date"),
        text_expr(cols, "prod_srvc_id", "product_service_id"),
        double_expr(cols, "qty_dspnsd_num", "quantity_dispensed"),
        int_expr(cols, "days_suply_num", "days_supply"),
        double_expr(cols, "ptnt_pay_amt", "patient_pay_amount"),
        double_expr(cols, "tot_rx_cst_amt", "total_rx_cost"),
    ]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver_prescription_events AS
        SELECT
            beneficiary_id,
            event_id,
            service_date,
            EXTRACT(YEAR FROM service_date)::INTEGER AS service_year,
            product_service_id,
            quantity_dispensed,
            days_supply,
            patient_pay_amount,
            total_rx_cost
        FROM (
            SELECT {', '.join(fields)}
            FROM {qident(source_table)}
        ) events
        WHERE beneficiary_id IS NOT NULL
        """
    )


def _code_columns(con: duckdb.DuckDBPyConnection, table_name: str, prefixes: Iterable[str]) -> list[str]:
    cols = table_columns(con, table_name)
    return sorted(
        [col for col in cols if any(col.startswith(prefix) for prefix in prefixes)],
        key=lambda value: (
            value.rsplit("_", 1)[0],
            int(value.rsplit("_", 1)[-1]) if value.rsplit("_", 1)[-1].isdigit() else 0,
        ),
    )


def create_silver_diagnosis_codes(con: duckdb.DuckDBPyConnection) -> None:
    queries: list[str] = []
    for table_name in ("silver_inpatient_claims", "silver_outpatient_claims", "silver_carrier_claims"):
        for column in _code_columns(con, table_name, ["diagnosis_code_"]):
            queries.append(
                f"""
                SELECT
                    beneficiary_id,
                    claim_id,
                    claim_type,
                    claim_year AS year,
                    {sql_literal(column)} AS code_position,
                    {qident(column)} AS diagnosis_code
                FROM {qident(table_name)}
                WHERE NULLIF(TRIM({qident(column)}), '') IS NOT NULL
                """
            )

    schema = [
        ("beneficiary_id", "VARCHAR"),
        ("claim_id", "VARCHAR"),
        ("claim_type", "VARCHAR"),
        ("year", "INTEGER"),
        ("code_position", "VARCHAR"),
        ("diagnosis_code", "VARCHAR"),
    ]
    if not queries:
        create_empty_table(con, "silver_diagnosis_codes", schema)
        return

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver_diagnosis_codes AS
        {' UNION ALL '.join(queries)}
        """
    )


def create_silver_procedure_codes(con: duckdb.DuckDBPyConnection) -> None:
    queries: list[str] = []
    for table_name in ("silver_inpatient_claims", "silver_outpatient_claims", "silver_carrier_claims"):
        for column in _code_columns(con, table_name, ["procedure_code_", "hcpcs_code_"]):
            procedure_system = "HCPCS" if column.startswith("hcpcs_code_") else "ICD9_OR_HCPCS"
            queries.append(
                f"""
                SELECT
                    beneficiary_id,
                    claim_id,
                    claim_type,
                    claim_year AS year,
                    {sql_literal(column)} AS code_position,
                    {sql_literal(procedure_system)} AS procedure_system,
                    {qident(column)} AS procedure_code
                FROM {qident(table_name)}
                WHERE NULLIF(TRIM({qident(column)}), '') IS NOT NULL
                """
            )

    schema = [
        ("beneficiary_id", "VARCHAR"),
        ("claim_id", "VARCHAR"),
        ("claim_type", "VARCHAR"),
        ("year", "INTEGER"),
        ("code_position", "VARCHAR"),
        ("procedure_system", "VARCHAR"),
        ("procedure_code", "VARCHAR"),
    ]
    if not queries:
        create_empty_table(con, "silver_procedure_codes", schema)
        return

    con.execute(
        f"""
        CREATE OR REPLACE TABLE silver_procedure_codes AS
        {' UNION ALL '.join(queries)}
        """
    )


def run_silver_transforms(con: duckdb.DuckDBPyConnection) -> None:
    create_silver_beneficiaries(con)
    create_silver_inpatient_claims(con)
    create_silver_outpatient_claims(con)
    create_silver_carrier_claims(con)
    create_silver_prescription_events(con)
    create_silver_diagnosis_codes(con)
    create_silver_procedure_codes(con)


def create_gold_patient_year_summary(con: duckdb.DuckDBPyConnection) -> None:
    chronic_columns = ",\n            ".join(f"MAX({qident(name)}) AS {qident(name)}" for name in CHRONIC_CONDITIONS)
    chronic_select = ",\n            ".join(f"COALESCE(b.{qident(name)}, 0) AS {qident(name)}" for name in CHRONIC_CONDITIONS)
    chronic_sum = " + ".join(f"COALESCE(b.{qident(name)}, 0)" for name in CHRONIC_CONDITIONS)

    con.execute(
        f"""
        CREATE OR REPLACE TABLE gold_patient_year_summary AS
        WITH person_years AS (
            SELECT beneficiary_id, year
            FROM silver_beneficiaries
            WHERE beneficiary_id IS NOT NULL AND year IS NOT NULL
            UNION
            SELECT beneficiary_id, claim_year AS year
            FROM silver_inpatient_claims
            WHERE beneficiary_id IS NOT NULL AND claim_year IS NOT NULL
            UNION
            SELECT beneficiary_id, claim_year AS year
            FROM silver_outpatient_claims
            WHERE beneficiary_id IS NOT NULL AND claim_year IS NOT NULL
            UNION
            SELECT beneficiary_id, claim_year AS year
            FROM silver_carrier_claims
            WHERE beneficiary_id IS NOT NULL AND claim_year IS NOT NULL
            UNION
            SELECT beneficiary_id, service_year AS year
            FROM silver_prescription_events
            WHERE beneficiary_id IS NOT NULL AND service_year IS NOT NULL
        ),
        b AS (
            SELECT
                beneficiary_id,
                year,
                MAX(age) AS age,
                MAX(sex_code) AS sex_code,
                MAX(race_code) AS race_code,
                MAX(state_code) AS state_code,
                MAX(county_code) AS county_code,
                MAX(esrd_indicator) AS esrd_indicator,
                {chronic_columns},
                MAX(medicare_ip_reimbursement) AS beneficiary_summary_ip_reimbursement,
                MAX(medicare_op_reimbursement) AS beneficiary_summary_op_reimbursement,
                MAX(medicare_carrier_reimbursement) AS beneficiary_summary_carrier_reimbursement
            FROM silver_beneficiaries
            GROUP BY beneficiary_id, year
        ),
        claim_union AS (
            SELECT beneficiary_id, claim_year AS year, claim_id, claim_type, payment_amount
            FROM silver_inpatient_claims
            WHERE claim_year IS NOT NULL
            UNION ALL
            SELECT beneficiary_id, claim_year AS year, claim_id, claim_type, payment_amount
            FROM silver_outpatient_claims
            WHERE claim_year IS NOT NULL
            UNION ALL
            SELECT beneficiary_id, claim_year AS year, claim_id, claim_type, payment_amount
            FROM silver_carrier_claims
            WHERE claim_year IS NOT NULL
        ),
        claim_rollup AS (
            SELECT
                beneficiary_id,
                year,
                COUNT(*) FILTER (WHERE claim_type = 'inpatient') AS inpatient_claims_count,
                COUNT(*) FILTER (WHERE claim_type = 'outpatient') AS outpatient_claims_count,
                COUNT(*) FILTER (WHERE claim_type = 'carrier') AS carrier_claims_count,
                SUM(CASE WHEN claim_type = 'inpatient' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS inpatient_total_paid,
                SUM(CASE WHEN claim_type = 'outpatient' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS outpatient_total_paid,
                SUM(CASE WHEN claim_type = 'carrier' THEN COALESCE(payment_amount, 0) ELSE 0 END) AS carrier_total_paid
            FROM claim_union
            GROUP BY beneficiary_id, year
        ),
        rx_rollup AS (
            SELECT
                beneficiary_id,
                service_year AS year,
                COUNT(*) AS prescription_events_count,
                SUM(COALESCE(total_rx_cost, 0)) AS prescription_total_cost
            FROM silver_prescription_events
            WHERE service_year IS NOT NULL
            GROUP BY beneficiary_id, service_year
        ),
        dx_rollup AS (
            SELECT
                beneficiary_id,
                year,
                COUNT(DISTINCT diagnosis_code) AS unique_diagnosis_codes
            FROM silver_diagnosis_codes
            GROUP BY beneficiary_id, year
        ),
        proc_rollup AS (
            SELECT
                beneficiary_id,
                year,
                COUNT(DISTINCT procedure_code) AS unique_procedure_codes
            FROM silver_procedure_codes
            GROUP BY beneficiary_id, year
        )
        SELECT
            py.beneficiary_id,
            py.year,
            b.age,
            b.sex_code,
            b.race_code,
            b.state_code,
            b.county_code,
            b.esrd_indicator,
            {chronic_select},
            ({chronic_sum})::INTEGER AS chronic_condition_count,
            COALESCE(cr.inpatient_claims_count, 0)::INTEGER AS inpatient_claims_count,
            COALESCE(cr.outpatient_claims_count, 0)::INTEGER AS outpatient_claims_count,
            COALESCE(cr.carrier_claims_count, 0)::INTEGER AS carrier_claims_count,
            COALESCE(rx.prescription_events_count, 0)::INTEGER AS prescription_events_count,
            COALESCE(cr.inpatient_total_paid, 0) AS inpatient_total_paid,
            COALESCE(cr.outpatient_total_paid, 0) AS outpatient_total_paid,
            COALESCE(cr.carrier_total_paid, 0) AS carrier_total_paid,
            COALESCE(rx.prescription_total_cost, 0) AS prescription_total_cost,
            COALESCE(cr.inpatient_total_paid, 0)
                + COALESCE(cr.outpatient_total_paid, 0)
                + COALESCE(cr.carrier_total_paid, 0)
                + COALESCE(rx.prescription_total_cost, 0) AS total_synthetic_cost,
            COALESCE(dx.unique_diagnosis_codes, 0)::INTEGER AS unique_diagnosis_codes,
            COALESCE(proc.unique_procedure_codes, 0)::INTEGER AS unique_procedure_codes,
            CASE WHEN COALESCE(cr.inpatient_claims_count, 0) > 0 THEN 1 ELSE 0 END AS any_inpatient,
            CASE WHEN COALESCE(cr.inpatient_claims_count, 0) >= 2 THEN 1 ELSE 0 END AS repeated_inpatient,
            CURRENT_TIMESTAMP AS generated_at
        FROM person_years py
        LEFT JOIN b
            ON py.beneficiary_id = b.beneficiary_id
           AND py.year = b.year
        LEFT JOIN claim_rollup cr
            ON py.beneficiary_id = cr.beneficiary_id
           AND py.year = cr.year
        LEFT JOIN rx_rollup rx
            ON py.beneficiary_id = rx.beneficiary_id
           AND py.year = rx.year
        LEFT JOIN dx_rollup dx
            ON py.beneficiary_id = dx.beneficiary_id
           AND py.year = dx.year
        LEFT JOIN proc_rollup proc
            ON py.beneficiary_id = proc.beneficiary_id
           AND py.year = proc.year
        """
    )


def create_gold_summaries(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE gold_patient_utilization_summary AS
        SELECT
            year,
            COUNT(DISTINCT beneficiary_id) AS beneficiaries,
            SUM(inpatient_claims_count) AS inpatient_claims,
            SUM(outpatient_claims_count) AS outpatient_claims,
            SUM(carrier_claims_count) AS carrier_claims,
            SUM(prescription_events_count) AS prescription_events,
            AVG(inpatient_claims_count) AS avg_inpatient_claims_per_beneficiary,
            AVG(outpatient_claims_count) AS avg_outpatient_claims_per_beneficiary,
            AVG(carrier_claims_count) AS avg_carrier_claims_per_beneficiary,
            AVG(prescription_events_count) AS avg_prescription_events_per_beneficiary
        FROM gold_patient_year_summary
        GROUP BY year
        ORDER BY year
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE gold_patient_cost_summary AS
        SELECT
            year,
            COUNT(DISTINCT beneficiary_id) AS beneficiaries,
            SUM(total_synthetic_cost) AS total_synthetic_cost,
            AVG(total_synthetic_cost) AS avg_synthetic_cost,
            MEDIAN(total_synthetic_cost) AS median_synthetic_cost,
            QUANTILE_CONT(total_synthetic_cost, 0.90) AS p90_synthetic_cost,
            SUM(inpatient_total_paid) AS inpatient_total_paid,
            SUM(outpatient_total_paid) AS outpatient_total_paid,
            SUM(carrier_total_paid) AS carrier_total_paid,
            SUM(prescription_total_cost) AS prescription_total_cost
        FROM gold_patient_year_summary
        GROUP BY year
        ORDER BY year
        """
    )

    chronic_queries = []
    for condition in CHRONIC_CONDITIONS:
        chronic_queries.append(
            f"""
            SELECT
                year,
                {sql_literal(condition)} AS condition_name,
                SUM({qident(condition)})::INTEGER AS beneficiaries_with_condition,
                AVG(total_synthetic_cost) FILTER (WHERE {qident(condition)} = 1) AS avg_cost_with_condition,
                AVG(total_synthetic_cost) FILTER (WHERE {qident(condition)} = 0) AS avg_cost_without_condition
            FROM gold_patient_year_summary
            GROUP BY year
            """
        )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE gold_patient_chronic_condition_summary AS
        {' UNION ALL '.join(chronic_queries)}
        """
    )


def create_high_cost_prediction_dataset(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
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
            c.*,
            c.year AS input_year,
            t.target_year,
            t.target_total_synthetic_cost,
            t.high_cost_threshold AS target_high_cost_threshold,
            t.high_cost_next_year
        FROM gold_patient_year_summary c
        INNER JOIN target_years t
            ON c.beneficiary_id = t.beneficiary_id
           AND c.year + 1 = t.target_year
        """
    )


def run_gold_transforms(con: duckdb.DuckDBPyConnection) -> None:
    create_gold_patient_year_summary(con)
    create_gold_summaries(con)
    create_high_cost_prediction_dataset(con)
