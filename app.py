"""NbS Project Financial Tracker — Streamlit web application."""

import streamlit as st
import pandas as pd

from src.data_loader import (
    load_csv,
    load_uploaded_file,
    get_sample_data_path,
    filter_dataframe,
    DataValidationError,
)
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
    disbursement_timeline_chart,
    partner_payment_chart,
    category_pie_chart,
    utilization_gauge,
)
from src.export import export_to_excel


def setup_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="NbS Financial Tracker",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🌿 NbS Project Financial Tracker")
    st.caption("Budget allocation, disbursement timeline, partner payments & burn rate")


def load_data() -> pd.DataFrame:
    """Load data from upload or sample file via sidebar."""
    st.sidebar.header("Data Source")
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded is not None:
        try:
            return load_uploaded_file(uploaded)
        except DataValidationError as exc:
            st.sidebar.error(str(exc))
            st.stop()
    else:
        st.sidebar.info("Using sample data. Upload a CSV to use your own.")
        return load_csv(get_sample_data_path())


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return filtered DataFrame."""
    st.sidebar.header("Filters")
    categories = st.sidebar.multiselect(
        "Category", options=sorted(df["category"].unique())
    )
    partners = st.sidebar.multiselect(
        "Partner", options=sorted(df["partner"].unique())
    )
    locations = st.sidebar.multiselect(
        "Location", options=sorted(df["location"].unique())
    )
    return filter_dataframe(
        df,
        categories=categories or None,
        partners=partners or None,
        locations=locations or None,
    )


def render_kpis(metrics: dict) -> None:
    """Render KPI metric cards."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Budget", f"${metrics['total_budget']:,.0f}")
    col2.metric("Total Disbursed", f"${metrics['total_disbursed']:,.0f}")
    col3.metric("Total Spent", f"${metrics['total_spent']:,.0f}")
    col4.metric("Projects", metrics["project_count"])

    col5, col6, col7 = st.columns(3)
    col5.metric("Remaining", f"${metrics['total_remaining']:,.0f}")
    col6.metric("Burn Rate", f"{metrics['overall_burn_rate']}%")
    col7.metric("Disbursement Rate", f"{metrics['disbursement_rate']}%")


def render_budget_tab(df: pd.DataFrame) -> None:
    """Render the Budget vs Actuals tab."""
    bva = compute_budget_vs_actuals(df)
    st.plotly_chart(budget_vs_actuals_chart(df), use_container_width=True)

    st.subheader("Budget vs Actuals Table")
    st.dataframe(
        bva.style.format({
            "budget_usd": "${:,.0f}",
            "spent_usd": "${:,.0f}",
            "remaining_usd": "${:,.0f}",
            "utilization_pct": "{:.1f}%",
        }),
        use_container_width=True,
    )


def render_burn_rate_tab(df: pd.DataFrame) -> None:
    """Render the Burn Rate tab."""
    burn = compute_burn_rate(df)
    st.plotly_chart(burn_rate_chart(burn), use_container_width=True)

    metrics = compute_kpi_metrics(df)
    st.plotly_chart(utilization_gauge(metrics["overall_burn_rate"]), use_container_width=True)


def render_partner_tab(df: pd.DataFrame) -> None:
    """Render the Partner Payments tab."""
    partners = compute_partner_payments(df)
    st.plotly_chart(partner_payment_chart(partners), use_container_width=True)

    st.subheader("Partner Payment Schedule")
    st.dataframe(
        partners.style.format({
            "total_budget": "${:,.0f}",
            "total_disbursed": "${:,.0f}",
            "total_spent": "${:,.0f}",
            "pending_disbursement": "${:,.0f}",
        }),
        use_container_width=True,
    )


def render_timeline_tab(df: pd.DataFrame) -> None:
    """Render the Disbursement Timeline tab."""
    timeline = compute_disbursement_timeline(df)
    st.plotly_chart(disbursement_timeline_chart(timeline), use_container_width=True)

    category = compute_category_summary(df)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(category_pie_chart(category), use_container_width=True)
    with col2:
        st.subheader("Category Summary")
        st.dataframe(
            category.style.format({
                "total_budget": "${:,.0f}",
                "total_spent": "${:,.0f}",
                "total_disbursed": "${:,.0f}",
                "utilization_pct": "{:.1f}%",
            }),
            use_container_width=True,
        )


def render_export_section(df: pd.DataFrame) -> None:
    """Render the export section."""
    st.subheader("📥 Export Data")
    bva = compute_budget_vs_actuals(df)
    partners = compute_partner_payments(df)
    category = compute_category_summary(df)

    excel_bytes = export_to_excel(df, bva, partners, category)
    st.download_button(
        label="Download Excel Report",
        data=excel_bytes,
        file_name="nbs_financial_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def main() -> None:
    """Application entry point."""
    setup_page()
    raw_df = load_data()
    filtered_df = render_filters(raw_df)

    render_kpis(compute_kpi_metrics(filtered_df))
    st.divider()

    tab_budget, tab_burn, tab_partner, tab_timeline = st.tabs([
        "📊 Budget vs Actuals",
        "🔥 Burn Rate",
        "🤝 Partner Payments",
        "📅 Disbursement Timeline",
    ])

    with tab_budget:
        render_budget_tab(filtered_df)
    with tab_burn:
        render_burn_rate_tab(filtered_df)
    with tab_partner:
        render_partner_tab(filtered_df)
    with tab_timeline:
        render_timeline_tab(filtered_df)

    st.divider()
    render_export_section(filtered_df)

    st.sidebar.divider()
    st.sidebar.caption("Built for PUR's NbS project management workflow")


if __name__ == "__main__":
    main()
