"""Tests for src.export module."""

from io import BytesIO

import pandas as pd
import pytest

from src.calculations import (
    compute_budget_vs_actuals,
    compute_partner_payments,
    compute_category_summary,
)
from src.export import export_to_excel, dataframe_to_csv_bytes


class TestExportToExcel:
    def test_returns_bytes(self, sample_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(sample_df)
        partners = compute_partner_payments(sample_df)
        category = compute_category_summary(sample_df)
        result = export_to_excel(sample_df, bva, partners, category)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_contains_all_sheets(self, sample_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(sample_df)
        partners = compute_partner_payments(sample_df)
        category = compute_category_summary(sample_df)
        result = export_to_excel(sample_df, bva, partners, category)

        xl = pd.ExcelFile(BytesIO(result))
        assert "Raw Data" in xl.sheet_names
        assert "Budget vs Actuals" in xl.sheet_names
        assert "Partner Payments" in xl.sheet_names
        assert "Category Summary" in xl.sheet_names

    def test_raw_data_sheet_row_count(self, sample_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(sample_df)
        partners = compute_partner_payments(sample_df)
        category = compute_category_summary(sample_df)
        result = export_to_excel(sample_df, bva, partners, category)

        xl = pd.ExcelFile(BytesIO(result))
        raw = xl.parse("Raw Data")
        assert len(raw) == len(sample_df)


class TestDataframeToCsvBytes:
    def test_returns_bytes(self, sample_df: pd.DataFrame) -> None:
        result = dataframe_to_csv_bytes(sample_df)
        assert isinstance(result, bytes)

    def test_csv_content(self, sample_df: pd.DataFrame) -> None:
        result = dataframe_to_csv_bytes(sample_df)
        text = result.decode("utf-8")
        assert "project_id" in text
        assert "NBS-001" in text

    def test_does_not_include_index(self, sample_df: pd.DataFrame) -> None:
        result = dataframe_to_csv_bytes(sample_df)
        lines = result.decode("utf-8").strip().split("\n")
        header = lines[0]
        assert header.startswith("project_id")
