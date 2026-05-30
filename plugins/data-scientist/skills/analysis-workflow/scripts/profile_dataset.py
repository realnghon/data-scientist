#!/usr/bin/env python
"""Profile structured data files for the data-scientist skill.

The script intentionally performs shallow, analysis-safe inspection. It does not
mutate source files, run statistical tests, or infer business conclusions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".txt", ".tsv", ".xlsx", ".xls", ".parquet", ".json", ".jsonl"}


@dataclass(frozen=True)
class RoleCandidate:
    column: str
    role: str
    confidence: float
    evidence: list[str]


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def normalize_sheet(sheet: str | None) -> str | int | None:
    if sheet is None:
        return None
    return int(sheet) if sheet.isdigit() else sheet


def detect_delimiter(path: Path) -> str:
    if path.suffix.lower() == ".tsv":
        return "\t"
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        sample = handle.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","


def estimate_csv_rows(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except OSError:
        return None


def read_table(path: Path, sheet: str | int | None, sample_rows: int | None) -> tuple[pd.DataFrame, dict[str, Any]]:
    suffix = path.suffix.lower()
    read_meta: dict[str, Any] = {"format": suffix.lstrip(".")}

    if suffix in [".csv", ".txt", ".tsv"]:
        delimiter = detect_delimiter(path)
        read_meta["delimiter"] = delimiter
        read_meta["estimated_rows"] = estimate_csv_rows(path)
        return pd.read_csv(path, sep=delimiter, nrows=sample_rows), read_meta

    if suffix in [".xlsx", ".xls"]:
        excel = pd.ExcelFile(path)
        selected_sheet = sheet if sheet is not None else excel.sheet_names[0]
        read_meta["sheets"] = excel.sheet_names
        read_meta["selected_sheet"] = selected_sheet
        return pd.read_excel(path, sheet_name=selected_sheet, nrows=sample_rows), read_meta

    if suffix == ".parquet":
        df = pd.read_parquet(path)
        read_meta["estimated_rows"] = int(len(df))
        return df.head(sample_rows) if sample_rows else df, read_meta

    if suffix in [".json", ".jsonl"]:
        lines = suffix == ".jsonl"
        df = pd.read_json(path, lines=lines)
        read_meta["estimated_rows"] = int(len(df))
        return df.head(sample_rows) if sample_rows else df, read_meta

    raise ValueError(f"Unsupported file extension: {suffix}. Supported: {sorted(SUPPORTED_EXTENSIONS)}")


def coerce_datetime_if_likely(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    if pd.api.types.is_numeric_dtype(series):
        return series
    sample = series.dropna().astype(str).head(100)
    if sample.empty:
        return series
    # This is a best-effort, mixed-format heuristic across unknown columns, so
    # silence pandas' "could not infer format" notice rather than guess a format.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() >= 0.8:
            return pd.to_datetime(series, errors="coerce")
    return series


def series_profile(series: pd.Series) -> dict[str, Any]:
    series = coerce_datetime_if_likely(series)
    non_null = series.dropna()
    profile: dict[str, Any] = {
        "dtype": str(series.dtype),
        "non_null": int(series.notna().sum()),
        "missing": int(series.isna().sum()),
        "missing_rate": round(float(series.isna().mean()), 6),
        "unique": int(series.nunique(dropna=True)),
        "unique_rate": round(float(series.nunique(dropna=True) / len(series)), 6) if len(series) else 0.0,
        "sample_values": [clean_value(v) for v in non_null.head(5).tolist()],
    }

    if pd.api.types.is_numeric_dtype(series):
        desc = series.describe(percentiles=[0.25, 0.5, 0.75])
        for key in ["mean", "std", "min", "25%", "50%", "75%", "max"]:
            if key in desc:
                profile[key] = clean_value(float(desc[key]))
    elif pd.api.types.is_datetime64_any_dtype(series):
        profile["min"] = clean_value(non_null.min()) if len(non_null) else None
        profile["max"] = clean_value(non_null.max()) if len(non_null) else None
    else:
        counts = non_null.astype(str).value_counts().head(10)
        profile["top_values"] = {str(index): int(value) for index, value in counts.items()}

    return profile


def add_role(
    candidates: list[RoleCandidate],
    *,
    column: str,
    role: str,
    confidence: float,
    evidence: str,
) -> None:
    candidates.append(
        RoleCandidate(
            column=column,
            role=role,
            confidence=round(float(max(0.0, min(confidence, 1.0))), 2),
            evidence=[evidence],
        )
    )


def infer_roles(df: pd.DataFrame) -> list[dict[str, Any]]:
    candidates: list[RoleCandidate] = []
    target_keywords = {
        "yield",
        "defect",
        "fail",
        "pass",
        "scrap",
        "rework",
        "quality",
        "rate",
        "cycle",
        "throughput",
        "downtime",
        "oee",
        "target",
        "label",
    }
    time_keywords = {"time", "date", "datetime", "timestamp"}
    id_keywords = {"id", "sn", "serial", "lot", "batch", "work_order", "order"}
    group_keywords = {
        "machine",
        "equipment",
        "line",
        "station",
        "tool",
        "shift",
        "operator",
        "supplier",
        "material",
        "recipe",
        "product",
        "part",
        "plant",
    }
    parameter_keywords = {
        "temp",
        "temperature",
        "pressure",
        "speed",
        "torque",
        "flow",
        "humidity",
        "voltage",
        "current",
        "setpoint",
        "actual",
    }

    for column in df.columns:
        col = str(column)
        name = col.lower()
        series = df[column]
        profile = series_profile(series)
        unique_rate = float(profile.get("unique_rate", 0.0))
        unique = int(profile.get("unique", 0))
        is_numeric = pd.api.types.is_numeric_dtype(series)
        likely_datetime = pd.api.types.is_datetime64_any_dtype(coerce_datetime_if_likely(series))

        if any(keyword in name for keyword in target_keywords):
            add_role(candidates, column=col, role="target_y", confidence=0.86, evidence="name matches target/outcome keyword")
        if likely_datetime or any(keyword in name for keyword in time_keywords):
            add_role(candidates, column=col, role="time", confidence=0.9 if likely_datetime else 0.75, evidence="datetime-like values or time keyword")
        if any(keyword in name for keyword in id_keywords) or unique_rate > 0.9:
            add_role(candidates, column=col, role="entity_id", confidence=0.78 if unique_rate > 0.9 else 0.7, evidence="id keyword or high uniqueness")
        if any(keyword in name for keyword in group_keywords):
            add_role(candidates, column=col, role="group", confidence=0.82, evidence="name matches manufacturing/group keyword")
        elif not is_numeric and 1 < unique <= min(100, max(20, len(df) // 10)):
            add_role(candidates, column=col, role="group", confidence=0.58, evidence="categorical column with moderate cardinality")
        if is_numeric and any(keyword in name for keyword in parameter_keywords):
            add_role(candidates, column=col, role="process_parameter", confidence=0.82, evidence="numeric column matches process parameter keyword")

    return [asdict(item) for item in sorted(candidates, key=lambda item: (-item.confidence, item.role, item.column))]


def data_risks(df: pd.DataFrame, read_meta: dict[str, Any]) -> list[str]:
    risks: list[str] = []
    if df.empty:
        risks.append("sample is empty")
    if len(df.columns) == 0:
        risks.append("no columns detected")
    duplicate_columns = pd.Index(df.columns).duplicated()
    if duplicate_columns.any():
        risks.append("duplicate column names detected")
    if read_meta.get("estimated_rows") is not None and read_meta["estimated_rows"] > len(df):
        risks.append("profile is based on a row sample, not full data")
    high_missing = [str(col) for col in df.columns if df[col].isna().mean() > 0.5]
    if high_missing:
        risks.append(f"columns with >50% missing values: {high_missing[:10]}")
    return risks


def build_profile(path: Path, sheet: str | int | None, sample_rows: int | None) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    if not path.is_file():
        raise ValueError(f"Dataset path is not a file: {path}")

    df, read_meta = read_table(path, sheet, sample_rows)
    column_profiles = {str(column): series_profile(df[column]) for column in df.columns}
    return {
        "status": "ok",
        "manifest": {
            "source": str(path),
            "file_size_bytes": path.stat().st_size,
            "read_metadata": read_meta,
            "sampled_rows": int(len(df)),
            "columns": [str(column) for column in df.columns],
            "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        },
        "role_candidates": infer_roles(df),
        "column_profiles": column_profiles,
        "sample_records": [
            {str(key): clean_value(value) for key, value in row.items()}
            for row in df.head(10).to_dict(orient="records")
        ],
        "data_risks": data_risks(df, read_meta),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a structured data profile for agent analysis.")
    parser.add_argument("path", type=Path, help="CSV, TSV, Excel, Parquet, JSON, or JSONL file.")
    parser.add_argument("--sheet", default=None, help="Excel sheet name or zero-based index.")
    parser.add_argument("--sample-rows", type=int, default=5000, help="Maximum rows to inspect.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        profile = build_profile(args.path, normalize_sheet(args.sheet), args.sample_rows)
        payload = json.dumps(profile, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0
    except Exception as exc:
        error_payload = {
            "status": "error",
            "source": str(args.path),
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
