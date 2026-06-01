import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from profile_dataset import (  # noqa: E402
    build_profile,
    clean_value,
    detect_delimiter,
    main,
    normalize_sheet,
    read_table,
)


def test_profile_dataset_reports_manifest_roles_and_risks(tmp_path):
    dataset = tmp_path / "manufacturing.csv"
    dataset.write_text(
        "\n".join(
            [
                "serial_id,machine,timestamp,temp_setpoint,yield_rate",
                "S1,M1,2026-05-01 08:00,180,0.98",
                "S2,M2,2026-05-01 09:00,185,0.91",
            ]
        ),
        encoding="utf-8",
    )

    profile = build_profile(dataset, sheet=None, sample_rows=100)

    assert profile["status"] == "ok"
    assert profile["manifest"]["columns"] == [
        "serial_id",
        "machine",
        "timestamp",
        "temp_setpoint",
        "yield_rate",
    ]
    roles = {(item["column"], item["role"]) for item in profile["role_candidates"]}
    assert ("yield_rate", "target_y") in roles
    assert ("timestamp", "time") in roles
    assert ("machine", "group") in roles
    assert ("temp_setpoint", "process_parameter") in roles
    assert profile["sample_records"][0]["serial_id"] == "S1"


def test_profile_dataset_returns_sample_risk_when_not_full_file(tmp_path):
    dataset = tmp_path / "sample.csv"
    dataset.write_text("id,yield_rate\n1,0.9\n2,0.8\n3,0.7\n", encoding="utf-8")

    profile = build_profile(dataset, sheet=None, sample_rows=1)

    assert "profile is based on a row sample, not full data" in profile["data_risks"]


def test_clean_value_normalizes_nan_and_datetime_values() -> None:
    assert clean_value(None) is None
    assert clean_value(float("nan")) is None
    assert clean_value(float("inf")) is None
    assert clean_value(pd.Timestamp("2026-01-02")) == "2026-01-02T00:00:00"
    assert clean_value("kept") == "kept"


def test_normalize_sheet_converts_numeric_strings() -> None:
    assert normalize_sheet(None) is None
    assert normalize_sheet("0") == 0
    assert normalize_sheet("Sheet1") == "Sheet1"


def test_detect_delimiter_handles_tsv_and_sniffer_fallback(tmp_path) -> None:
    tsv = tmp_path / "data.tsv"
    tsv.write_text("a\tb\n1\t2\n", encoding="utf-8")
    one_column = tmp_path / "one.csv"
    one_column.write_text("a\n1\n2\n", encoding="utf-8")

    assert detect_delimiter(tsv) == "\t"
    assert detect_delimiter(one_column) == ","


def test_read_table_supports_json_and_jsonl(tmp_path) -> None:
    json_file = tmp_path / "records.json"
    json_file.write_text(json.dumps([{"a": 1}, {"a": 2}]), encoding="utf-8")
    jsonl_file = tmp_path / "records.jsonl"
    jsonl_file.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")

    json_df, json_meta = read_table(json_file, sheet=None, sample_rows=1)
    jsonl_df, jsonl_meta = read_table(jsonl_file, sheet=None, sample_rows=1)

    assert json_meta["format"] == "json"
    assert jsonl_meta["format"] == "jsonl"
    assert len(json_df) == 1
    assert len(jsonl_df) == 1


def test_read_table_supports_excel_and_parquet_when_dependencies_present(tmp_path) -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    excel_file = tmp_path / "records.xlsx"
    parquet_file = tmp_path / "records.parquet"

    pytest.importorskip("openpyxl")
    df.to_excel(excel_file, sheet_name="Data", index=False)
    excel_df, excel_meta = read_table(excel_file, sheet="Data", sample_rows=1)
    assert excel_meta["selected_sheet"] == "Data"
    assert excel_meta["sheets"] == ["Data"]
    assert len(excel_df) == 1

    pytest.importorskip("pyarrow")
    df.to_parquet(parquet_file, index=False)
    parquet_df, parquet_meta = read_table(parquet_file, sheet=None, sample_rows=1)
    assert parquet_meta["estimated_rows"] == 2
    assert len(parquet_df) == 1


def test_build_profile_rejects_missing_directory_and_unknown_extension(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        build_profile(tmp_path / "missing.csv", sheet=None, sample_rows=10)
    with pytest.raises(ValueError, match="not a file"):
        build_profile(tmp_path, sheet=None, sample_rows=10)

    unsupported = tmp_path / "data.unsupported"
    unsupported.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file extension"):
        build_profile(unsupported, sheet=None, sample_rows=10)


def test_profile_main_writes_output_and_reports_errors(tmp_path, capsys) -> None:
    dataset = tmp_path / "data.csv"
    output = tmp_path / "profile.json"
    dataset.write_text("id,value\n1,2\n", encoding="utf-8")

    assert main([str(dataset), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "ok"

    assert main([str(tmp_path / "missing.csv")]) == 1
    err = capsys.readouterr().err
    assert "Dataset not found" in err


def test_profile_main_prints_payload_to_stdout(tmp_path, capsys) -> None:
    dataset = tmp_path / "data.csv"
    dataset.write_text("id,value\n1,2\n", encoding="utf-8")

    assert main([str(dataset)]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["status"] == "ok"
