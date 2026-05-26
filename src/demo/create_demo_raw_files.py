from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("data/raw/demo_sample")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def beneficiary_rows(year: int) -> list[dict[str, object]]:
    return [
        {
            "DESYNPUF_ID": "DEMO_BENE_001",
            "BENE_BIRTH_DT": "19350101",
            "BENE_DEATH_DT": "",
            "BENE_SEX_IDENT_CD": "1",
            "BENE_RACE_CD": "1",
            "SP_STATE_CODE": "10",
            "BENE_COUNTY_CD": "001",
            "BENE_ESRD_IND": "0",
            "BENE_HI_CVRAGE_TOT_MONS": 12,
            "BENE_SMI_CVRAGE_TOT_MONS": 12,
            "BENE_HMO_CVRAGE_TOT_MONS": 0,
            "PLAN_CVRG_MOS_NUM": 12,
            "MEDREIMB_IP": 1500 if year == 2008 else 5000,
            "BENRES_IP": 150,
            "PPPYMT_IP": 0,
            "MEDREIMB_OP": 300,
            "BENRES_OP": 30,
            "PPPYMT_OP": 0,
            "MEDREIMB_CAR": 400,
            "BENRES_CAR": 40,
            "PPPYMT_CAR": 0,
            "SP_ALZHDMTA": 0,
            "SP_CHF": 1,
            "SP_CHRNKIDN": 0,
            "SP_CNCR": 0,
            "SP_COPD": 1,
            "SP_DEPRESSN": 0,
            "SP_DIABETES": 1,
            "SP_ISCHMCHT": 1,
            "SP_OSTEOPRS": 0,
            "SP_RA_OA": 0,
            "SP_STRKETIA": 0,
        },
        {
            "DESYNPUF_ID": "DEMO_BENE_002",
            "BENE_BIRTH_DT": "19420101",
            "BENE_DEATH_DT": "",
            "BENE_SEX_IDENT_CD": "2",
            "BENE_RACE_CD": "2",
            "SP_STATE_CODE": "20",
            "BENE_COUNTY_CD": "003",
            "BENE_ESRD_IND": "0",
            "BENE_HI_CVRAGE_TOT_MONS": 12,
            "BENE_SMI_CVRAGE_TOT_MONS": 12,
            "BENE_HMO_CVRAGE_TOT_MONS": 0,
            "PLAN_CVRG_MOS_NUM": 12,
            "MEDREIMB_IP": 0,
            "BENRES_IP": 0,
            "PPPYMT_IP": 0,
            "MEDREIMB_OP": 200,
            "BENRES_OP": 20,
            "PPPYMT_OP": 0,
            "MEDREIMB_CAR": 250,
            "BENRES_CAR": 25,
            "PPPYMT_CAR": 0,
            "SP_ALZHDMTA": 0,
            "SP_CHF": 0,
            "SP_CHRNKIDN": 0,
            "SP_CNCR": 0,
            "SP_COPD": 0,
            "SP_DEPRESSN": 1,
            "SP_DIABETES": 0,
            "SP_ISCHMCHT": 0,
            "SP_OSTEOPRS": 0,
            "SP_RA_OA": 0,
            "SP_STRKETIA": 0,
        },
        {
            "DESYNPUF_ID": "DEMO_BENE_003",
            "BENE_BIRTH_DT": "19500101",
            "BENE_DEATH_DT": "",
            "BENE_SEX_IDENT_CD": "1",
            "BENE_RACE_CD": "1",
            "SP_STATE_CODE": "30",
            "BENE_COUNTY_CD": "005",
            "BENE_ESRD_IND": "0",
            "BENE_HI_CVRAGE_TOT_MONS": 12,
            "BENE_SMI_CVRAGE_TOT_MONS": 12,
            "BENE_HMO_CVRAGE_TOT_MONS": 0,
            "PLAN_CVRG_MOS_NUM": 6,
            "MEDREIMB_IP": 0,
            "BENRES_IP": 0,
            "PPPYMT_IP": 0,
            "MEDREIMB_OP": 100,
            "BENRES_OP": 10,
            "PPPYMT_OP": 0,
            "MEDREIMB_CAR": 100,
            "BENRES_CAR": 10,
            "PPPYMT_CAR": 0,
            "SP_ALZHDMTA": 0,
            "SP_CHF": 0,
            "SP_CHRNKIDN": 0,
            "SP_CNCR": 0,
            "SP_COPD": 0,
            "SP_DEPRESSN": 0,
            "SP_DIABETES": 0,
            "SP_ISCHMCHT": 0,
            "SP_OSTEOPRS": 0,
            "SP_RA_OA": 0,
            "SP_STRKETIA": 0,
        },
    ]


def create_demo_raw_files(output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    beneficiary_fields = list(beneficiary_rows(2008)[0].keys())
    for year in (2008, 2009, 2010):
        write_csv(
            output_dir / f"DE1_0_2008_to_2010_Beneficiary_Summary_File_Sample_1_{year}.csv",
            beneficiary_fields,
            beneficiary_rows(year),
        )

    claim_fields = [
        "DESYNPUF_ID",
        "CLM_ID",
        "CLM_FROM_DT",
        "CLM_THRU_DT",
        "CLM_PMT_AMT",
        "NCH_PRMRY_PYR_CLM_PD_AMT",
        "PRVDR_NUM",
        "CLM_ADMSN_DT",
        "NCH_BENE_DSCHRG_DT",
        "CLM_UTLZTN_DAY_CNT",
        "CLM_DRG_CD",
        "ICD9_DGNS_CD_1",
        "ICD9_PRCDR_CD_1",
        "HCPCS_CD_1",
    ]
    write_csv(
        output_dir / "DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv",
        claim_fields,
        [
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "CLM_ID": "IP_001",
                "CLM_FROM_DT": "20080110",
                "CLM_THRU_DT": "20080113",
                "CLM_PMT_AMT": 2500,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "PRVDR_NUM": "PRV001",
                "CLM_ADMSN_DT": "20080110",
                "NCH_BENE_DSCHRG_DT": "20080113",
                "CLM_UTLZTN_DAY_CNT": 3,
                "CLM_DRG_CD": "470",
                "ICD9_DGNS_CD_1": "25000",
                "ICD9_PRCDR_CD_1": "8154",
                "HCPCS_CD_1": "",
            },
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "CLM_ID": "IP_002",
                "CLM_FROM_DT": "20090201",
                "CLM_THRU_DT": "20090204",
                "CLM_PMT_AMT": 7000,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "PRVDR_NUM": "PRV002",
                "CLM_ADMSN_DT": "20090201",
                "NCH_BENE_DSCHRG_DT": "20090204",
                "CLM_UTLZTN_DAY_CNT": 3,
                "CLM_DRG_CD": "291",
                "ICD9_DGNS_CD_1": "4280",
                "ICD9_PRCDR_CD_1": "3722",
                "HCPCS_CD_1": "",
            },
        ],
    )

    write_csv(
        output_dir / "DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv",
        claim_fields,
        [
            {
                "DESYNPUF_ID": "DEMO_BENE_002",
                "CLM_ID": "OP_001",
                "CLM_FROM_DT": "20080601",
                "CLM_THRU_DT": "20080601",
                "CLM_PMT_AMT": 300,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "PRVDR_NUM": "OP001",
                "CLM_ADMSN_DT": "",
                "NCH_BENE_DSCHRG_DT": "",
                "CLM_UTLZTN_DAY_CNT": 1,
                "CLM_DRG_CD": "",
                "ICD9_DGNS_CD_1": "4019",
                "ICD9_PRCDR_CD_1": "",
                "HCPCS_CD_1": "99213",
            },
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "CLM_ID": "OP_002",
                "CLM_FROM_DT": "20090402",
                "CLM_THRU_DT": "20090402",
                "CLM_PMT_AMT": 500,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "PRVDR_NUM": "OP002",
                "CLM_ADMSN_DT": "",
                "NCH_BENE_DSCHRG_DT": "",
                "CLM_UTLZTN_DAY_CNT": 1,
                "CLM_DRG_CD": "",
                "ICD9_DGNS_CD_1": "496",
                "ICD9_PRCDR_CD_1": "",
                "HCPCS_CD_1": "93000",
            },
        ],
    )

    carrier_fields = [
        "DESYNPUF_ID",
        "CLM_ID",
        "CLM_FROM_DT",
        "CLM_THRU_DT",
        "CLM_PMT_AMT",
        "NCH_PRMRY_PYR_CLM_PD_AMT",
        "LINE_ICD9_DGNS_CD_1",
        "LINE_HCPCS_CD_1",
    ]
    write_csv(
        output_dir / "DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv",
        carrier_fields,
        [
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "CLM_ID": "CAR_001",
                "CLM_FROM_DT": "20080301",
                "CLM_THRU_DT": "20080301",
                "CLM_PMT_AMT": 200,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "LINE_ICD9_DGNS_CD_1": "25000",
                "LINE_HCPCS_CD_1": "99214",
            },
            {
                "DESYNPUF_ID": "DEMO_BENE_002",
                "CLM_ID": "CAR_002",
                "CLM_FROM_DT": "20090301",
                "CLM_THRU_DT": "20090301",
                "CLM_PMT_AMT": 150,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "LINE_ICD9_DGNS_CD_1": "311",
                "LINE_HCPCS_CD_1": "99213",
            },
        ],
    )
    write_csv(
        output_dir / "DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv",
        carrier_fields,
        [
            {
                "DESYNPUF_ID": "DEMO_BENE_003",
                "CLM_ID": "CAR_003",
                "CLM_FROM_DT": "20080501",
                "CLM_THRU_DT": "20080501",
                "CLM_PMT_AMT": 75,
                "NCH_PRMRY_PYR_CLM_PD_AMT": 0,
                "LINE_ICD9_DGNS_CD_1": "V700",
                "LINE_HCPCS_CD_1": "G0438",
            }
        ],
    )

    pde_fields = [
        "DESYNPUF_ID",
        "PDE_ID",
        "SRVC_DT",
        "PROD_SRVC_ID",
        "QTY_DSPNSD_NUM",
        "DAYS_SUPLY_NUM",
        "PTNT_PAY_AMT",
        "TOT_RX_CST_AMT",
    ]
    write_csv(
        output_dir / "DE1_0_2008_to_2010_Prescription_Drug_Events_Sample_1.csv",
        pde_fields,
        [
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "PDE_ID": "RX_001",
                "SRVC_DT": "20080401",
                "PROD_SRVC_ID": "00000000001",
                "QTY_DSPNSD_NUM": 30,
                "DAYS_SUPLY_NUM": 30,
                "PTNT_PAY_AMT": 5,
                "TOT_RX_CST_AMT": 80,
            },
            {
                "DESYNPUF_ID": "DEMO_BENE_001",
                "PDE_ID": "RX_002",
                "SRVC_DT": "20090401",
                "PROD_SRVC_ID": "00000000002",
                "QTY_DSPNSD_NUM": 30,
                "DAYS_SUPLY_NUM": 30,
                "PTNT_PAY_AMT": 5,
                "TOT_RX_CST_AMT": 120,
            },
            {
                "DESYNPUF_ID": "DEMO_BENE_002",
                "PDE_ID": "RX_003",
                "SRVC_DT": "20090501",
                "PROD_SRVC_ID": "00000000003",
                "QTY_DSPNSD_NUM": 30,
                "DAYS_SUPLY_NUM": 30,
                "PTNT_PAY_AMT": 8,
                "TOT_RX_CST_AMT": 60,
            },
        ],
    )

    print(f"Demo CMS-like raw CSV files written to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create tiny CMS-like demo raw CSV files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    create_demo_raw_files(args.output_dir)


if __name__ == "__main__":
    main()
