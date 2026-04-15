"""Integration tests for end-to-end data pipeline."""

import pandas as pd
import pytest

from src.data_loader import load_csv, get_sample_data_path, filter_dataframe
from src.calculations import (
    compute_budget_vs_actuals,
    compute_burn_rate,
    compute_partner_payments,
    compute_disbursement_timeline,
    compute_category_summary,
    compute_kpi_metrics,
)
from src.charts import (
    budget_vs_actuals_chart,
    burn_rate_chart,
    partner_payment_chart,
    disbursement_timeline_chart,
    category_pie_chart,
)
from src.export import export_to_excel


class TestFullPipeline:
    """Test the complete data flow from CSV through calculations to charts."""

    @pytest.fixture()
    def full_df(self) -> pd.DataFrame:
        return load_csv(get_sample_data_path())

    def test_load_and_compute_all(self, full_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(full_df)
        assert len(bva) == len(full_df)

        burn = compute_burn_rate(full_df)
        assert len(burn) > 0

        partners = compute_partner_payments(full_df)
        assert len(partners) > 0

        timeline = compute_disbursement_timeline(full_df)
        assert len(timeline) == len(full_df)

    def test_filter_then_compute(self, full_df: pd.DataFrame) -> None:
        filtered = filter_dataframe(full_df, categories=["Restoration"])
        metrics = compute_kpi_metrics(filtered)
        assert metrics["project_count"] > 0
        assert metrics["total_budget"] > 0

    def test_charts_from_real_data(self, full_df: pd.DataFrame) -> None:
        fig1 = budget_vs_actuals_chart(full_df)
        assert fig1 is not None

        burn = compute_burn_rate(full_df)
        fig2 = burn_rate_chart(burn)
        assert fig2 is not None

        partners = compute_partner_payments(full_df)
        fig3 = partner_payment_chart(partners)
        assert fig3 is not None

    def test_export_from_real_data(self, full_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(full_df)
        partners = compute_partner_payments(full_df)
        category = compute_category_summary(full_df)
        excel_bytes = export_to_excel(full_df, bva, partners, category)
        assert len(excel_bytes) > 1000

    def test_all_categories_present(self, full_df: pd.DataFrame) -> None:
        categories = full_df["category"].unique()
        assert len(categories) >= 5

    def test_financial_consistency(self, full_df: pd.DataFrame) -> None:
        """Spent should never exceed budget for well-formed data."""
        assert all(full_df["spent_usd"] <= full_df["budget_usd"])
        assert all(full_df["disbursed_usd"] <= full_df["budget_usd"])

    def test_single_row_pipeline(self, single_row_df: pd.DataFrame) -> None:
        bva = compute_budget_vs_actuals(single_row_df)
        assert len(bva) == 1
        metrics = compute_kpi_metrics(single_row_df)
        assert metrics["project_count"] == 1
