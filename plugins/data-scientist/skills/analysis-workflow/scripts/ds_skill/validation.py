"""Input validation utilities for ds_skill modules.

Provides common validation patterns to prevent injection attacks,
path traversal, and other security issues when processing user data.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_dataframe(df: Any, *, min_rows: int = 1, min_cols: int = 1) -> pd.DataFrame:
    """Validate that input is a non-empty DataFrame.

    Args:
        df: Input to validate
        min_rows: Minimum number of rows required
        min_cols: Minimum number of columns required

    Returns:
        The validated DataFrame

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(df, pd.DataFrame):
        raise ValidationError(f"Expected pandas DataFrame, got {type(df).__name__}")

    if len(df) < min_rows:
        raise ValidationError(f"DataFrame has {len(df)} rows, need at least {min_rows}")

    if len(df.columns) < min_cols:
        raise ValidationError(f"DataFrame has {len(df.columns)} columns, need at least {min_cols}")

    return df


def validate_column_name(df: pd.DataFrame, column: str) -> str:
    """Validate that a column exists in the DataFrame.

    Args:
        df: DataFrame to check
        column: Column name to validate

    Returns:
        The validated column name

    Raises:
        ValidationError: If column doesn't exist
    """
    if column not in df.columns:
        raise ValidationError(
            f"Column '{column}' not found. Available: {list(df.columns)}"
        )
    return column


def validate_column_names(df: pd.DataFrame, columns: list[str]) -> list[str]:
    """Validate that multiple columns exist in the DataFrame.

    Args:
        df: DataFrame to check
        columns: Column names to validate

    Returns:
        The validated column names

    Raises:
        ValidationError: If any column doesn't exist
    """
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValidationError(
            f"Columns not found: {missing}. Available: {list(df.columns)}"
        )
    return columns


def validate_numeric_column(df: pd.DataFrame, column: str) -> str:
    """Validate that a column exists and is numeric.

    Args:
        df: DataFrame to check
        column: Column name to validate

    Returns:
        The validated column name

    Raises:
        ValidationError: If column doesn't exist or isn't numeric
    """
    validate_column_name(df, column)

    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValidationError(
            f"Column '{column}' must be numeric, got {df[column].dtype}"
        )

    return column


def validate_safe_filename(filename: str, *, allow_path: bool = False) -> str:
    """Validate that a filename is safe (no path traversal).

    Args:
        filename: Filename to validate
        allow_path: If True, allow directory separators

    Returns:
        The validated filename

    Raises:
        ValidationError: If filename contains unsafe characters
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")

    # Check for path traversal attempts
    if ".." in filename:
        raise ValidationError("Filename cannot contain '..'")

    # Check for absolute paths (cross-platform)
    # On Windows, Path('/etc/passwd').is_absolute() is False, so also check for leading /
    if Path(filename).is_absolute() or filename.startswith(("/", "\\")):
        raise ValidationError("Filename cannot be an absolute path")

    # If paths not allowed, check for directory separators
    if not allow_path:
        if "/" in filename or "\\" in filename:
            raise ValidationError("Filename cannot contain directory separators")

    # Check for null bytes
    if "\x00" in filename:
        raise ValidationError("Filename cannot contain null bytes")

    return filename


def validate_positive_int(value: Any, name: str = "value") -> int:
    """Validate that a value is a positive integer.

    Args:
        value: Value to validate
        name: Name of the parameter (for error messages)

    Returns:
        The validated integer

    Raises:
        ValidationError: If value is not a positive integer
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

    if int_value <= 0:
        raise ValidationError(f"{name} must be positive, got {int_value}")

    return int_value


def validate_probability(value: Any, name: str = "value") -> float:
    """Validate that a value is a valid probability (0 to 1).

    Args:
        value: Value to validate
        name: Name of the parameter (for error messages)

    Returns:
        The validated probability

    Raises:
        ValidationError: If value is not in [0, 1]
    """
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if not 0 <= float_value <= 1:
        raise ValidationError(f"{name} must be between 0 and 1, got {float_value}")

    return float_value


def sanitize_label(label: str, *, max_length: int = 100) -> str:
    """Sanitize a user-provided label for safe display.

    Removes control characters and limits length to prevent
    injection attacks in generated reports.

    Args:
        label: Label to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized label
    """
    # Remove control characters except newline/tab
    sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', label)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized
