"""Tests for src/budget_variance_analyzer.py.

Covers happy path, edge cases (empty DataFrame, zero budget, negative values,
single row), determinism, and parametrized variance scenarios.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.budget_variance_analyzer import (
    FLAG_ON_TRACK,
    FLAG_OVER,
    FLAG_UNDER,
    VarianceSummary,
    build_variance_report,
    compute_category_variance,
    compute_project_variance,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def base_df() -> pd.DataFrame:
    """Three-project DataFrame with one over, one under, one on-track."""
    return pd.DataFrame(
        {
            "project_id": ["NBS-001", "NBS-002", "NBS-003"],
            "project_name": ["Mangrove A", "Peatland B", "Agroforestry C"],
            "category": ["Restoration", "Rewetting", "Agroforestry"],
            "budget_usd": [100_000.0, 200_000.0, 80_000.0],
            "spent_usd": [115_000.0, 185_000.0, 82_000.0],  # +15%, -7.5%, +2.5%
        }
    )


@pytest.fixture()
def same_category_df() -> pd.DataFrame:
    """Two projects in the same category for aggregation tests."""
    return pd.DataFrame(
        {
            "project_id": ["NBS-010", "NBS-011"],
            "project_name": ["Marine A", "Marine B"],
            "category": ["Marine", "Marine"],
            "budget_usd": [100_000.0, 100_000.0],
            "spent_usd": [120_000.0, 90_000.0],  # combined: +5 % → ON_TRACK at 10%
        }
    )


# ── compute_project_variance: happy path ─────────────────────────────────────


def test_project_variance_columns_present(base_df: pd.DataFrame) -> None:
    result = compute_project_variance(base_df)
    assert {"variance_usd", "variance_pct", "flag"}.issubset(result.columns)


def test_project_variance_does_not_mutate_input(base_df: pd.DataFrame) -> None:
    original_cols = list(base_df.columns)
    compute_project_variance(base_df)
    assert list(base_df.columns) == original_cols


def test_project_variance_over_budget_flag(base_df: pd.DataFrame) -> None:
    result = compute_project_variance(base_df, tolerance_pct=10.0)
    assert result.loc[result["project_id"] == "NBS-001", "flag"].iloc[0] == FLAG_OVER


def test_project_variance_under_budget_flag(base_df: pd.DataFrame) -> None:
    result = compute_project_variance(base_df, tolerance_pct=5.0)
    assert result.loc[result["project_id"] == "NBS-002", "flag"].iloc[0] == FLAG_UNDER


def test_project_variance_on_track_flag(base_df: pd.DataFrame) -> None:
    result = compute_project_variance(base_df, tolerance_pct=10.0)
    assert result.loc[result["project_id"] == "NBS-003", "flag"].iloc[0] == FLAG_ON_TRACK


def test_project_variance_usd_correct(base_df: pd.DataFrame) -> None:
    result = compute_project_variance(base_df)
    row = result.loc[result["project_id"] == "NBS-001"].iloc[0]
    assert row["variance_usd"] == pytest.approx(15_000.0)


def test_project_variance_is_deterministic(base_df: pd.DataFrame) -> None:
    r1 = compute_project_variance(base_df)
    r2 = compute_project_variance(base_df)
    pd.testing.assert_frame_equal(r1, r2)


# ── compute_project_variance: edge cases ─────────────────────────────────────


def test_project_variance_empty_dataframe() -> None:
    empty = pd.DataFrame(
        columns=["project_id", "project_name", "category", "budget_usd", "spent_usd"]
    )
    result = compute_project_variance(empty)
    assert result.empty
    assert "variance_usd" in result.columns


def test_project_variance_zero_budget() -> None:
    df = pd.DataFrame(
        {
            "project_id": ["NBS-Z"],
            "project_name": ["Zero Budget"],
            "category": ["Urban"],
            "budget_usd": [0.0],
            "spent_usd": [5_000.0],
        }
    )
    result = compute_project_variance(df)
    # variance_pct should be NaN (division by zero), flag should still be set
    assert pd.isna(result["variance_pct"].iloc[0])
    assert result["flag"].iloc[0] == FLAG_ON_TRACK


def test_project_variance_single_row() -> None:
    df = pd.DataFrame(
        {
            "project_id": ["NBS-S"],
            "project_name": ["Single"],
            "category": ["Forestry"],
            "budget_usd": [50_000.0],
            "spent_usd": [50_000.0],
        }
    )
    result = compute_project_variance(df)
    assert len(result) == 1
    assert result["flag"].iloc[0] == FLAG_ON_TRACK


def test_project_variance_negative_spent() -> None:
    """Negative spent (e.g. refund/credit) should produce UNDER_BUDGET flag."""
    df = pd.DataFrame(
        {
            "project_id": ["NBS-R"],
            "project_name": ["Refund"],
            "category": ["Marine"],
            "budget_usd": [100_000.0],
            "spent_usd": [-10_000.0],
        }
    )
    result = compute_project_variance(df, tolerance_pct=10.0)
    assert result["flag"].iloc[0] == FLAG_UNDER


# ── compute_project_variance: validation errors ───────────────────────────────


def test_project_variance_raises_on_wrong_type() -> None:
    with pytest.raises(TypeError, match="Expected pd.DataFrame"):
        compute_project_variance([1, 2, 3])  # type: ignore[arg-type]


def test_project_variance_raises_on_missing_column(base_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        compute_project_variance(base_df.drop(columns=["spent_usd"]))


def test_project_variance_raises_on_negative_tolerance(base_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_project_variance(base_df, tolerance_pct=-5.0)


# ── compute_category_variance ─────────────────────────────────────────────────


def test_category_variance_returns_list_of_summaries(base_df: pd.DataFrame) -> None:
    summaries = compute_category_variance(base_df)
    assert all(isinstance(s, VarianceSummary) for s in summaries)
    assert len(summaries) == 3  # one per category


def test_category_variance_aggregates_same_category(same_category_df: pd.DataFrame) -> None:
    summaries = compute_category_variance(same_category_df, tolerance_pct=10.0)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.total_budget_usd == pytest.approx(200_000.0)
    assert s.total_spent_usd == pytest.approx(210_000.0)
    assert s.variance_pct == pytest.approx(5.0)
    assert s.flag == FLAG_ON_TRACK  # 5 % < 10 % tolerance


def test_category_variance_empty_returns_empty_list() -> None:
    empty = pd.DataFrame(
        columns=["project_id", "project_name", "category", "budget_usd", "spent_usd"]
    )
    assert compute_category_variance(empty) == []


def test_category_variance_flagged_projects_populated(base_df: pd.DataFrame) -> None:
    """At 10 % tolerance, NBS-001 (+15 %) should appear in flagged_projects."""
    summaries = compute_category_variance(base_df, tolerance_pct=10.0)
    restoration = next(s for s in summaries if s.category == "Restoration")
    assert "NBS-001" in restoration.flagged_projects


# ── build_variance_report ─────────────────────────────────────────────────────


def test_build_variance_report_has_category_flag_column(base_df: pd.DataFrame) -> None:
    report = build_variance_report(base_df)
    assert "category_flag" in report.columns


def test_build_variance_report_row_count_matches_input(base_df: pd.DataFrame) -> None:
    report = build_variance_report(base_df)
    assert len(report) == len(base_df)


# ── parametrized variance accuracy ───────────────────────────────────────────


@pytest.mark.parametrize(
    ("budget", "spent", "tolerance", "expected_flag"),
    [
        (100_000, 111_000, 10.0, FLAG_OVER),    # +11 % → OVER
        (100_000, 89_000, 10.0, FLAG_UNDER),    # -11 % → UNDER
        (100_000, 105_000, 10.0, FLAG_ON_TRACK),# +5 % → within band
        (100_000, 100_000, 10.0, FLAG_ON_TRACK),# exact match
        (100_000, 0, 10.0, FLAG_UNDER),         # fully unspent
    ],
)
def test_project_variance_flag_parametrized(
    budget: float, spent: float, tolerance: float, expected_flag: str
) -> None:
    df = pd.DataFrame(
        {
            "project_id": ["P"],
            "project_name": ["Test"],
            "category": ["Cat"],
            "budget_usd": [float(budget)],
            "spent_usd": [float(spent)],
        }
    )
    result = compute_project_variance(df, tolerance_pct=tolerance)
    assert result["flag"].iloc[0] == expected_flag
