"""Tests for src.data_loader module."""

import pandas as pd
import pytest

from src.data_loader import (
    validate_columns,
    load_csv,
    get_sample_data_path,
    filter_dataframe,
    DataValidationError,
    REQUIRED_COLUMNS,
    _coerce_types,
)


class TestValidateColumns:
    def test_all_columns_present(self, sample_df: pd.DataFrame) -> None:
        assert validate_columns(sample_df) == []

    def test_missing_single_column(self, sample_df: pd.DataFrame) -> None:
        df = sample_df.drop(columns=["budget_usd"])
        assert validate_columns(df) == ["budget_usd"]

    def test_missing_multiple_columns(self) -> None:
        df = pd.DataFrame({"project_id": [1], "project_name": ["x"]})
        missing = validate_columns(df)
        assert "partner" in missing
        assert "budget_usd" in missing

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame()
        assert len(validate_columns(df)) == len(REQUIRED_COLUMNS)


class TestLoadCsv:
    def test_load_sample_data(self) -> None:
        path = get_sample_data_path()
        df = load_csv(path)
        assert len(df) >= 20
        assert list(df.columns[:4]) == ["project_id", "project_name", "partner", "location"]

    def test_numeric_columns_are_numeric(self) -> None:
        df = load_csv(get_sample_data_path())
        assert pd.api.types.is_numeric_dtype(df["budget_usd"])
        assert pd.api.types.is_numeric_dtype(df["spent_usd"])

    def test_date_column_is_datetime(self) -> None:
        df = load_csv(get_sample_data_path())
        assert pd.api.types.is_datetime64_any_dtype(df["disbursement_date"])

    def test_invalid_path_raises(self) -> None:
        from pathlib import Path
        with pytest.raises(FileNotFoundError):
            load_csv(Path("/nonexistent/path.csv"))


class TestCoerceTypes:
    def test_does_not_mutate_original(self, sample_df: pd.DataFrame) -> None:
        original_budget = sample_df["budget_usd"].tolist()
        _coerce_types(sample_df)
        assert sample_df["budget_usd"].tolist() == original_budget

    def test_handles_non_numeric_gracefully(self) -> None:
        df = pd.DataFrame({
            "project_id": ["A"],
            "project_name": ["X"],
            "partner": ["P"],
            "location": ["L"],
            "budget_usd": ["not_a_number"],
            "disbursed_usd": [100],
            "spent_usd": [50],
            "category": ["C"],
            "disbursement_date": ["invalid-date"],
            "status": ["Active"],
        })
        result = _coerce_types(df)
        assert result["budget_usd"].iloc[0] == 0
        assert pd.isna(result["disbursement_date"].iloc[0])


class TestFilterDataframe:
    def test_filter_by_category(self, sample_df: pd.DataFrame) -> None:
        result = filter_dataframe(sample_df, categories=["Restoration"])
        assert len(result) == 1
        assert result.iloc[0]["project_id"] == "NBS-001"

    def test_filter_by_partner(self, sample_df: pd.DataFrame) -> None:
        result = filter_dataframe(sample_df, partners=["Komunitas B"])
        assert len(result) == 1

    def test_filter_by_location(self, sample_df: pd.DataFrame) -> None:
        result = filter_dataframe(sample_df, locations=["Riau"])
        assert len(result) == 1

    def test_no_filters_returns_all(self, sample_df: pd.DataFrame) -> None:
        result = filter_dataframe(sample_df)
        assert len(result) == len(sample_df)

    def test_filter_does_not_mutate(self, sample_df: pd.DataFrame) -> None:
        original_len = len(sample_df)
        filter_dataframe(sample_df, categories=["Restoration"])
        assert len(sample_df) == original_len

    def test_combined_filters(self, sample_df: pd.DataFrame) -> None:
        result = filter_dataframe(
            sample_df,
            categories=["Restoration", "Rewetting"],
            locations=["Kalimantan Timur"],
        )
        assert len(result) == 1
