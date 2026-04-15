"""Plotly chart builders for NbS Financial Tracker."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def budget_vs_actuals_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing budget, disbursed, and spent per project."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Budget",
        x=df["project_name"],
        y=df["budget_usd"],
        marker_color="#2563eb",
    ))
    fig.add_trace(go.Bar(
        name="Disbursed",
        x=df["project_name"],
        y=df["disbursed_usd"],
        marker_color="#16a34a",
    ))
    fig.add_trace(go.Bar(
        name="Spent",
        x=df["project_name"],
        y=df["spent_usd"],
        marker_color="#dc2626",
    ))
    fig.update_layout(
        barmode="group",
        title="Budget vs Actuals by Project",
        xaxis_title="Project",
        yaxis_title="Amount (USD)",
        xaxis_tickangle=-45,
        height=500,
        template="plotly_white",
    )
    return fig


def burn_rate_chart(burn_df: pd.DataFrame) -> go.Figure:
    """Line chart showing burn rate by category over time."""
    fig = px.line(
        burn_df,
        x="month_str",
        y="total_spent",
        color="category",
        markers=True,
        title="Burn Rate by Category (Monthly)",
        labels={"month_str": "Month", "total_spent": "Spent (USD)", "category": "Category"},
        template="plotly_white",
    )
    fig.update_layout(height=450)
    return fig


def disbursement_timeline_chart(timeline_df: pd.DataFrame) -> go.Figure:
    """Area chart of cumulative disbursements over time."""
    fig = px.area(
        timeline_df,
        x="disbursement_date",
        y="cumulative_disbursed",
        title="Cumulative Disbursement Timeline",
        labels={
            "disbursement_date": "Date",
            "cumulative_disbursed": "Cumulative Disbursed (USD)",
        },
        template="plotly_white",
    )
    fig.update_layout(height=400)
    return fig


def partner_payment_chart(partner_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of partner payment status."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Disbursed",
        y=partner_df["partner"],
        x=partner_df["total_disbursed"],
        orientation="h",
        marker_color="#16a34a",
    ))
    fig.add_trace(go.Bar(
        name="Pending",
        y=partner_df["partner"],
        x=partner_df["pending_disbursement"],
        orientation="h",
        marker_color="#f59e0b",
    ))
    fig.update_layout(
        barmode="stack",
        title="Partner Payment Status",
        xaxis_title="Amount (USD)",
        yaxis_title="Partner",
        height=max(400, len(partner_df) * 35),
        template="plotly_white",
    )
    return fig


def category_pie_chart(category_df: pd.DataFrame) -> go.Figure:
    """Pie chart of budget allocation by category."""
    fig = px.pie(
        category_df,
        values="total_budget",
        names="category",
        title="Budget Allocation by Category",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(height=400)
    return fig


def utilization_gauge(utilization_pct: float) -> go.Figure:
    """Gauge chart showing overall budget utilization."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=utilization_pct,
        title={"text": "Overall Budget Utilization (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#2563eb"},
            "steps": [
                {"range": [0, 50], "color": "#dcfce7"},
                {"range": [50, 80], "color": "#fef9c3"},
                {"range": [80, 100], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#dc2626", "width": 4},
                "thickness": 0.75,
                "value": 90,
            },
        },
    ))
    fig.update_layout(height=300)
    return fig
