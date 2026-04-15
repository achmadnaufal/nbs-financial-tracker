"""Shared test fixtures for NbS Financial Tracker."""

import pandas as pd
import pytest


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """Minimal DataFrame matching the expected schema."""
    return pd.DataFrame({
        "project_id": ["NBS-001", "NBS-002", "NBS-003"],
        "project_name": ["Mangrove Kalimantan", "Peatland Riau", "Agroforestry Sulawesi"],
        "partner": ["Yayasan A", "Komunitas B", "Koperasi C"],
        "location": ["Kalimantan Timur", "Riau", "Sulawesi Selatan"],
        "budget_usd": [150000, 200000, 85000],
        "disbursed_usd": [120000, 180000, 60000],
        "spent_usd": [95000, 170000, 45000],
        "category": ["Restoration", "Rewetting", "Agroforestry"],
        "disbursement_date": pd.to_datetime(["2025-01-15", "2025-02-01", "2025-03-10"]),
        "status": ["Active", "Active", "Active"],
    })


@pytest.fixture()
def single_row_df() -> pd.DataFrame:
    """Single-row DataFrame for edge case testing."""
    return pd.DataFrame({
        "project_id": ["NBS-099"],
        "project_name": ["Solo Project"],
        "partner": ["Partner X"],
        "location": ["Jakarta"],
        "budget_usd": [100000],
        "disbursed_usd": [50000],
        "spent_usd": [25000],
        "category": ["Urban"],
        "disbursement_date": pd.to_datetime(["2025-06-01"]),
        "status": ["Active"],
    })
