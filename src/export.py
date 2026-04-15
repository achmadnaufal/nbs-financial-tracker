"""Excel export utilities for NbS Financial Tracker."""

from io import BytesIO

import pandas as pd


def export_to_excel(
    raw_data: pd.DataFrame,
    budget_vs_actuals: pd.DataFrame,
    partner_payments: pd.DataFrame,
    category_summary: pd.DataFrame,
) -> bytes:
    """Export multiple DataFrames to a multi-sheet Excel workbook.

    Returns raw bytes suitable for Streamlit download button.
    """
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        raw_data.to_excel(writer, sheet_name="Raw Data", index=False)
        budget_vs_actuals.to_excel(writer, sheet_name="Budget vs Actuals", index=False)
        partner_payments.to_excel(writer, sheet_name="Partner Payments", index=False)
        category_summary.to_excel(writer, sheet_name="Category Summary", index=False)
    return buffer.getvalue()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")
