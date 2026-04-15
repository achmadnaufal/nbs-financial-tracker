"""Tests for src.calculations module."""

import pandas as pd
import pytest

from src.calculations import (
    compute_budget_vs_actuals,
    compute_burn_rate,
    compute_partner_payments,
    compute_disbursement_timeline,
    compute_category_summary,
    compute_kpi_metrics,
)


class TestBudgetVsActuals:
    def test_columns_present(self, sample_df: pd.DataFrame) -> None:
        result = compute_budget_vs_actuals(sample_df)
        assert "remaining_usd" in result.columns
        assert "utilization_pct" in result.columns

    def test_remaining_calculation(self, sample_df: pd.DataFrame) -> None:
        result = compute_budget_vs_actuals(sample_df)
        row = result[result["project_id"] == "NBS-001"].iloc[0]
        assert row["remaining_usd"] == 150000 - 95000

    def test_utilization_percentage(self, sample_df: pd.DataFrame) -> None:
        result = compute_budget_vs_actuals(sample_df)
        row = result[result["project_id"] == "NBS-002"].iloc[0]
        expected = round(170000 / 200000 * 100, 1)
        assert row["utilization_pct"] == expected

    def test_does_not_mutate(self, sample_df: pd.DataFrame) -> None:
        cols_before = list(sample_df.columns)
        compute_budget_vs_actuals(sample_df)
        assert list(sample_df.columns) == cols_before


class TestBurnRate:
    def test_has_month_column(self, sample_df: pd.DataFrame) -> None:
        result = compute_burn_rate(sample_df)
        assert "month_str" in result.columns

    def test_groups_by_category(self, sample_df: pd.DataFrame) -> None:
        result = compute_burn_rate(sample_df)
        assert "category" in result.columns
        assert len(result) >= 1


class TestPartnerPayments:
    def test_aggregation(self, sample_df: pd.DataFrame) -> None:
        result = compute_partner_payments(sample_df)
        assert len(result) == 3
        assert "pending_disbursement" in result.columns

    def test_pending_calculation(self, sample_df: pd.DataFrame) -> None:
        result = compute_partner_payments(sample_df)
        row = result[result["partner"] == "Yayasan A"].iloc[0]
        assert row["pending_disbursement"] == 150000 - 120000

    def test_sorted_by_budget(self, sample_df: pd.DataFrame) -> None:
        result = compute_partner_payments(sample_df)
        budgets = result["total_budget"].tolist()
        assert budgets == sorted(budgets, reverse=True)


class TestDisbursementTimeline:
    def test_cumulative_column(self, sample_df: pd.DataFrame) -> None:
        result = compute_disbursement_timeline(sample_df)
        assert "cumulative_disbursed" in result.columns

    def test_cumulative_is_increasing(self, sample_df: pd.DataFrame) -> None:
        result = compute_disbursement_timeline(sample_df)
        cumulative = result["cumulative_disbursed"].tolist()
        assert cumulative == sorted(cumulative)

    def test_final_cumulative_equals_total(self, sample_df: pd.DataFrame) -> None:
        result = compute_disbursement_timeline(sample_df)
        assert result["cumulative_disbursed"].iloc[-1] == sample_df["disbursed_usd"].sum()


class TestCategorySummary:
    def test_unique_categories(self, sample_df: pd.DataFrame) -> None:
        result = compute_category_summary(sample_df)
        assert len(result) == 3

    def test_utilization_pct(self, sample_df: pd.DataFrame) -> None:
        result = compute_category_summary(sample_df)
        assert all(0 <= pct <= 100 for pct in result["utilization_pct"])


class TestKpiMetrics:
    def test_keys_present(self, sample_df: pd.DataFrame) -> None:
        metrics = compute_kpi_metrics(sample_df)
        expected_keys = {
            "total_budget", "total_disbursed", "total_spent",
            "total_remaining", "overall_burn_rate", "disbursement_rate",
            "project_count",
        }
        assert set(metrics.keys()) == expected_keys

    def test_total_budget(self, sample_df: pd.DataFrame) -> None:
        metrics = compute_kpi_metrics(sample_df)
        assert metrics["total_budget"] == 150000 + 200000 + 85000

    def test_remaining(self, sample_df: pd.DataFrame) -> None:
        metrics = compute_kpi_metrics(sample_df)
        assert metrics["total_remaining"] == metrics["total_budget"] - metrics["total_spent"]

    def test_project_count(self, sample_df: pd.DataFrame) -> None:
        metrics = compute_kpi_metrics(sample_df)
        assert metrics["project_count"] == 3

    def test_zero_budget_no_division_error(self) -> None:
        df = pd.DataFrame({
            "project_id": ["X"],
            "project_name": ["X"],
            "partner": ["X"],
            "location": ["X"],
            "budget_usd": [0],
            "disbursed_usd": [0],
            "spent_usd": [0],
            "category": ["X"],
            "disbursement_date": pd.to_datetime(["2025-01-01"]),
            "status": ["Active"],
        })
        metrics = compute_kpi_metrics(df)
        assert metrics["overall_burn_rate"] == 0.0
        assert metrics["disbursement_rate"] == 0.0
