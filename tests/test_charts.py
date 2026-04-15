"""Tests for src.charts module."""

import pandas as pd
import plotly.graph_objects as go

from src.calculations import (
    compute_burn_rate,
    compute_partner_payments,
    compute_disbursement_timeline,
    compute_category_summary,
)
from src.charts import (
    budget_vs_actuals_chart,
    burn_rate_chart,
    disbursement_timeline_chart,
    partner_payment_chart,
    category_pie_chart,
    utilization_gauge,
)


class TestBudgetVsActualsChart:
    def test_returns_figure(self, sample_df: pd.DataFrame) -> None:
        fig = budget_vs_actuals_chart(sample_df)
        assert isinstance(fig, go.Figure)

    def test_has_three_traces(self, sample_df: pd.DataFrame) -> None:
        fig = budget_vs_actuals_chart(sample_df)
        assert len(fig.data) == 3

    def test_trace_names(self, sample_df: pd.DataFrame) -> None:
        fig = budget_vs_actuals_chart(sample_df)
        names = {trace.name for trace in fig.data}
        assert names == {"Budget", "Disbursed", "Spent"}


class TestBurnRateChart:
    def test_returns_figure(self, sample_df: pd.DataFrame) -> None:
        burn = compute_burn_rate(sample_df)
        fig = burn_rate_chart(burn)
        assert isinstance(fig, go.Figure)


class TestDisbursementTimelineChart:
    def test_returns_figure(self, sample_df: pd.DataFrame) -> None:
        timeline = compute_disbursement_timeline(sample_df)
        fig = disbursement_timeline_chart(timeline)
        assert isinstance(fig, go.Figure)


class TestPartnerPaymentChart:
    def test_returns_figure(self, sample_df: pd.DataFrame) -> None:
        partners = compute_partner_payments(sample_df)
        fig = partner_payment_chart(partners)
        assert isinstance(fig, go.Figure)

    def test_has_two_traces(self, sample_df: pd.DataFrame) -> None:
        partners = compute_partner_payments(sample_df)
        fig = partner_payment_chart(partners)
        assert len(fig.data) == 2


class TestCategoryPieChart:
    def test_returns_figure(self, sample_df: pd.DataFrame) -> None:
        category = compute_category_summary(sample_df)
        fig = category_pie_chart(category)
        assert isinstance(fig, go.Figure)


class TestUtilizationGauge:
    def test_returns_figure(self) -> None:
        fig = utilization_gauge(75.0)
        assert isinstance(fig, go.Figure)

    def test_gauge_value(self) -> None:
        fig = utilization_gauge(42.5)
        assert fig.data[0].value == 42.5
