from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")

from src.transform.common import run_gold_transforms, run_silver_transforms


def build_tiny_database(tmp_path):
    db_path = tmp_path / "tiny.duckdb"
    con = duckdb.connect(str(db_path))
    for year in (2008, 2009):
        con.execute(
            f"""
            CREATE TABLE bronze_beneficiary_{year} AS
            SELECT * FROM (
                VALUES
                    ('B1', '19350101', '1', '1', '10', '001', '1', '1'),
                    ('B2', '19400101', '2', '2', '10', '003', '2', '2')
            ) AS t(
                desynpuf_id,
                bene_birth_dt,
                bene_sex_ident_cd,
                bene_race_cd,
                sp_state_code,
                bene_county_cd,
                sp_diabetes,
                sp_chf
            )
            """
        )
    con.execute(
        """
        CREATE TABLE bronze_inpatient_claims AS
        SELECT * FROM (
            VALUES
                ('B1', 'IP1', '20080110', '20080112', '2000', '25000', '9901'),
                ('B1', 'IP2', '20090201', '20090203', '5000', '25000', '9901')
        ) AS t(desynpuf_id, clm_id, clm_from_dt, clm_thru_dt, clm_pmt_amt, icd9_dgns_cd_1, icd9_prcdr_cd_1)
        """
    )
    con.execute(
        """
        CREATE TABLE bronze_outpatient_claims AS
        SELECT * FROM (
            VALUES
                ('B2', 'OP1', '20080601', '20080601', '100', '4019', 'A0428'),
                ('B2', 'OP2', '20090601', '20090601', '100', '4019', 'A0428')
        ) AS t(desynpuf_id, clm_id, clm_from_dt, clm_thru_dt, clm_pmt_amt, icd9_dgns_cd_1, hcpcs_cd_1)
        """
    )
    con.execute(
        """
        CREATE TABLE bronze_carrier_claims_a AS
        SELECT * FROM (
            VALUES
                ('B1', 'CR1', '20080301', '20080301', '200', '25000', '99213')
        ) AS t(desynpuf_id, clm_id, clm_from_dt, clm_thru_dt, clm_pmt_amt, line_icd9_dgns_cd_1, line_hcpcs_cd_1)
        """
    )
    con.execute(
        """
        CREATE TABLE bronze_prescription_drug_events AS
        SELECT * FROM (
            VALUES
                ('B1', 'RX1', '20080401', 'NDC1', '30', '30', '5', '50'),
                ('B2', 'RX2', '20080402', 'NDC2', '30', '30', '5', '20')
        ) AS t(desynpuf_id, pde_id, srvc_dt, prod_srvc_id, qty_dspnsd_num, days_suply_num, ptnt_pay_amt, tot_rx_cst_amt)
        """
    )
    run_silver_transforms(con)
    run_gold_transforms(con)
    return con


def test_gold_schema_contains_core_columns(tmp_path):
    con = build_tiny_database(tmp_path)
    columns = {
        row[1]
        for row in con.execute('PRAGMA table_info("gold_patient_year_summary")').fetchall()
    }
    assert "beneficiary_id" in columns
    assert "year" in columns
    assert "total_synthetic_cost" in columns
    assert "chronic_condition_count" in columns


def test_silver_code_tables_exist(tmp_path):
    con = build_tiny_database(tmp_path)
    diagnosis_rows = con.execute("SELECT COUNT(*) FROM silver_diagnosis_codes").fetchone()[0]
    procedure_rows = con.execute("SELECT COUNT(*) FROM silver_procedure_codes").fetchone()[0]
    assert diagnosis_rows >= 3
    assert procedure_rows >= 3
