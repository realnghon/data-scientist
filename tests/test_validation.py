"""Tests for ds_skill.validation module."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add ds_skill to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins/data-scientist/skills/analysis-workflow/scripts"))

from ds_skill.validation import (
    ValidationError,
    sanitize_label,
    validate_column_name,
    validate_column_names,
    validate_dataframe,
    validate_numeric_column,
    validate_positive_int,
    validate_probability,
    validate_safe_filename,
)


def test_validate_dataframe_success():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    result = validate_dataframe(df)
    assert result is df


def test_validate_dataframe_not_dataframe():
    with pytest.raises(ValidationError, match="Expected pandas DataFrame"):
        validate_dataframe([1, 2, 3])


def test_validate_dataframe_too_few_rows():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValidationError, match="has 1 rows, need at least 2"):
        validate_dataframe(df, min_rows=2)


def test_validate_dataframe_too_few_cols():
    df = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ValidationError, match="has 1 columns, need at least 2"):
        validate_dataframe(df, min_cols=2)


def test_validate_column_name_success():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = validate_column_name(df, "a")
    assert result == "a"


def test_validate_column_name_missing():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValidationError, match="Column 'x' not found"):
        validate_column_name(df, "x")


def test_validate_column_names_success():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    result = validate_column_names(df, ["a", "c"])
    assert result == ["a", "c"]


def test_validate_column_names_missing():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValidationError, match="Columns not found: \\['x', 'y'\\]"):
        validate_column_names(df, ["a", "x", "y"])


def test_validate_numeric_column_success():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = validate_numeric_column(df, "a")
    assert result == "a"


def test_validate_numeric_column_not_numeric():
    df = pd.DataFrame({"a": ["x", "y", "z"]})
    with pytest.raises(ValidationError, match="must be numeric"):
        validate_numeric_column(df, "a")


def test_validate_safe_filename_success():
    result = validate_safe_filename("report.md")
    assert result == "report.md"


def test_validate_safe_filename_with_path():
    result = validate_safe_filename("output/report.md", allow_path=True)
    assert result == "output/report.md"


def test_validate_safe_filename_path_traversal():
    with pytest.raises(ValidationError, match="cannot contain '..'"):
        validate_safe_filename("../etc/passwd")


def test_validate_safe_filename_absolute_path():
    with pytest.raises(ValidationError, match="cannot be an absolute path"):
        validate_safe_filename("/etc/passwd")


def test_validate_safe_filename_directory_separator():
    with pytest.raises(ValidationError, match="cannot contain directory separators"):
        validate_safe_filename("output/report.md", allow_path=False)


def test_validate_safe_filename_null_byte():
    with pytest.raises(ValidationError, match="cannot contain null bytes"):
        validate_safe_filename("report\x00.md")


def test_validate_positive_int_success():
    result = validate_positive_int(5)
    assert result == 5


def test_validate_positive_int_from_string():
    result = validate_positive_int("10")
    assert result == 10


def test_validate_positive_int_zero():
    with pytest.raises(ValidationError, match="must be positive"):
        validate_positive_int(0)


def test_validate_positive_int_negative():
    with pytest.raises(ValidationError, match="must be positive"):
        validate_positive_int(-5)


def test_validate_positive_int_not_int():
    with pytest.raises(ValidationError, match="must be an integer"):
        validate_positive_int("abc")


def test_validate_probability_success():
    result = validate_probability(0.5)
    assert result == 0.5


def test_validate_probability_zero():
    result = validate_probability(0)
    assert result == 0.0


def test_validate_probability_one():
    result = validate_probability(1)
    assert result == 1.0


def test_validate_probability_too_low():
    with pytest.raises(ValidationError, match="must be between 0 and 1"):
        validate_probability(-0.1)


def test_validate_probability_too_high():
    with pytest.raises(ValidationError, match="must be between 0 and 1"):
        validate_probability(1.5)


def test_validate_probability_not_number():
    with pytest.raises(ValidationError, match="must be a number"):
        validate_probability("abc")


def test_sanitize_label_clean():
    result = sanitize_label("Normal Label")
    assert result == "Normal Label"


def test_sanitize_label_control_chars():
    result = sanitize_label("Label\x00with\x01control\x1fchars")
    assert result == "Labelwithcontrolchars"


def test_sanitize_label_preserves_newline_tab():
    result = sanitize_label("Label\nwith\ttab")
    assert result == "Label\nwith\ttab"


def test_sanitize_label_truncate():
    long_label = "a" * 150
    result = sanitize_label(long_label, max_length=100)
    assert len(result) == 103  # 100 + "..."
    assert result.endswith("...")
