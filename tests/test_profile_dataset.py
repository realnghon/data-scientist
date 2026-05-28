from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from profile_dataset import build_profile  # noqa: E402


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
