from __future__ import annotations

import argparse
import csv
import gzip
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb


DEFAULT_DB_PATH = Path("data/processed/desynpuf.duckdb")
DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_EXTRACT_DIR = Path("data/interim/extracted")


@dataclass(frozen=True)
class RawFile:
    path: Path
    bronze_table: str


def qident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def standardize_column_name(name: str) -> str:
    cleaned = name.strip().lstrip("\ufeff").lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "unnamed_column"
    if cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned


def unique_standard_names(header: Iterable[str]) -> list[tuple[str, str]]:
    seen: dict[str, int] = {}
    pairs: list[tuple[str, str]] = []
    for original in header:
        base = standardize_column_name(original)
        count = seen.get(base, 0) + 1
        seen[base] = count
        standardized = base if count == 1 else f"{base}_{count}"
        pairs.append((original.strip().lstrip("\ufeff"), standardized))
    return pairs


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", newline="", encoding="utf-8-sig", errors="replace")
    return path.open("r", newline="", encoding="utf-8-sig", errors="replace")


def read_header(path: Path) -> list[str]:
    with open_text(path) as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration as exc:
            raise ValueError(f"{path} is empty") from exc


def safe_extract_zip(zip_path: Path, extract_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    destination = extract_dir / zip_path.stem
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            member_name = Path(member).name
            if not member_name:
                continue
            if not member_name.lower().endswith((".csv", ".txt")):
                continue
            output_path = destination / member_name
            if not output_path.exists():
                with archive.open(member) as source, output_path.open("wb") as target:
                    target.write(source.read())
            extracted.append(output_path)
    return extracted


def infer_bronze_table(path: Path) -> str | None:
    name = standardize_column_name(path.name)

    if "beneficiary" in name or "bene" in name:
        year_match = re.search(r"(2008|2009|2010)", name)
        if year_match:
            return f"bronze_beneficiary_{year_match.group(1)}"

    if "inpatient" in name:
        return "bronze_inpatient_claims"

    if "outpatient" in name:
        return "bronze_outpatient_claims"

    if "carrier" in name:
        if re.search(r"(sample_?1b|claims_?b|carrier_?b|part_?b|_b(?:_|$))", name):
            return "bronze_carrier_claims_b"
        if re.search(r"(sample_?1a|claims_?a|carrier_?a|part_?a|_a(?:_|$))", name):
            return "bronze_carrier_claims_a"
        if re.search(r"(carrier.*_2(?:_|$)|_2(?:_|$))", name):
            return "bronze_carrier_claims_b"
        if re.search(r"(carrier.*_1(?:_|$)|_1(?:_|$))", name):
            return "bronze_carrier_claims_a"
        return "bronze_carrier_claims_a"

    if "prescription" in name or "pde" in name or "drug" in name:
        return "bronze_prescription_drug_events"

    return None


def discover_raw_files(raw_dir: Path, extract_dir: Path) -> list[RawFile]:
    paths: list[Path] = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_dir():
            continue
        lower_name = path.name.lower()
        if lower_name.endswith(".zip"):
            paths.extend(safe_extract_zip(path, extract_dir))
        elif lower_name.endswith((".csv", ".txt", ".csv.gz")):
            paths.append(path)

    raw_files: list[RawFile] = []
    skipped: list[Path] = []
    for path in paths:
        bronze_table = infer_bronze_table(path)
        if bronze_table is None:
            skipped.append(path)
            continue
        raw_files.append(RawFile(path=path, bronze_table=bronze_table))

    if skipped:
        print("Skipped unrecognized files:")
        for path in skipped:
            print(f"  - {path}")
    return raw_files


def ensure_load_log(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS etl_load_log (
            table_name VARCHAR,
            source_file VARCHAR,
            row_count BIGINT,
            loaded_at TIMESTAMP
        )
        """
    )


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


def load_csv_to_bronze(
    con: duckdb.DuckDBPyConnection,
    raw_file: RawFile,
    replace_existing: bool,
) -> int:
    header = read_header(raw_file.path)
    aliases = unique_standard_names(header)
    select_columns = ",\n            ".join(
        f"{qident(original)} AS {qident(standardized)}"
        for original, standardized in aliases
    )
    source_file = sql_literal(str(raw_file.path))
    csv_path = sql_literal(str(raw_file.path))
    table_name = qident(raw_file.bronze_table)

    read_sql = f"""
        SELECT
            {select_columns},
            {source_file} AS _source_file,
            CURRENT_TIMESTAMP AS _loaded_at
        FROM read_csv_auto(
            {csv_path},
            header = true,
            all_varchar = true,
            ignore_errors = true,
            union_by_name = true
        )
    """

    if replace_existing or not table_exists(con, raw_file.bronze_table):
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS {read_sql}")
    else:
        con.execute(f"INSERT INTO {table_name} BY NAME {read_sql}")

    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    con.execute(
        """
        INSERT INTO etl_load_log
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [raw_file.bronze_table, str(raw_file.path), row_count],
    )
    return int(row_count)


def load_raw_files(
    raw_dir: Path = DEFAULT_RAW_DIR,
    db_path: Path = DEFAULT_DB_PATH,
    extract_dir: Path = DEFAULT_EXTRACT_DIR,
    replace_existing: bool = True,
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    raw_files = discover_raw_files(raw_dir, extract_dir)
    if not raw_files:
        print(f"No recognized CMS CSV/ZIP files found in {raw_dir}.")
        print("Download DE1.0 Sample 1 files into data/raw, then rerun ingestion.")
        return

    con = duckdb.connect(str(db_path))
    ensure_load_log(con)

    for raw_file in raw_files:
        row_count = load_csv_to_bronze(con, raw_file, replace_existing=replace_existing)
        print(f"Loaded {raw_file.path.name} -> {raw_file.bronze_table}: {row_count:,} rows")

    print(f"Bronze ingestion complete: {db_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load CMS DE-SynPUF raw files into DuckDB Bronze tables.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--extract-dir", type=Path, default=DEFAULT_EXTRACT_DIR)
    parser.add_argument("--append", action="store_true", help="Append to existing Bronze tables instead of replacing them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_raw_files(
        raw_dir=args.raw_dir,
        db_path=args.db,
        extract_dir=args.extract_dir,
        replace_existing=not args.append,
    )


if __name__ == "__main__":
    main()
