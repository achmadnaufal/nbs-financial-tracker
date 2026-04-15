"""Data loading and validation for NbS Financial Tracker."""

from pathlib import Path
from typing import Optional

import pandas as pd


REQUIRED_COLUMNS: tuple[str, ...] = (
    "project_id",
    "project_name",
    "partner",
    "location",
    "budget_usd",
    "disbursed_usd",
    "spent_usd",
    "category",
    "disbursement_date",
    "status",
)

NUMERIC_COLUMNS: tuple[str, ...] = ("budget_usd", "disbursed_usd", "spent_usd")


class DataValidationError(Exception):
    """Raised when uploaded data fails validation."""


def validate_columns(df: pd.DataFrame) -> list[str]:
    """Return list of missing required columns."""
    return [col for col in REQUIRED_COLUMNS if col not in df.columns]


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file and return a validated DataFrame."""
    df = pd.read_csv(path)
    missing = validate_columns(df)
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}")
    return _coerce_types(df)


def load_uploaded_file(uploaded_file: object) -> pd.DataFrame:
    """Load a Streamlit UploadedFile and return a validated DataFrame."""
    df = pd.read_csv(uploaded_file)
    missing = validate_columns(df)
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}")
    return _coerce_types(df)


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce column types without mutating the original DataFrame."""
    df = df.copy()
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["disbursement_date"] = pd.to_datetime(df["disbursement_date"], errors="coerce")
    return df


def get_sample_data_path() -> Path:
    """Return the path to the bundled sample CSV."""
    return Path(__file__).resolve().parent.parent / "demo" / "sample_data.csv"


def filter_dataframe(
    df: pd.DataFrame,
    categories: Optional[list[str]] = None,
    partners: Optional[list[str]] = None,
    locations: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Return a filtered copy of the DataFrame."""
    result = df.copy()
    if categories:
        result = result[result["category"].isin(categories)]
    if partners:
        result = result[result["partner"].isin(partners)]
    if locations:
        result = result[result["location"].isin(locations)]
    return result
