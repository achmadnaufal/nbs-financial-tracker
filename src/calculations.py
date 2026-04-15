"""Financial calculations for NbS project tracking."""

from typing import Any

import pandas as pd


def compute_budget_vs_actuals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute budget vs actuals summary per project (immutable)."""
    result = df[["project_id", "project_name", "budget_usd", "spent_usd"]].copy()
    result = result.assign(
        remaining_usd=result["budget_usd"] - result["spent_usd"],
        utilization_pct=(result["spent_usd"] / result["budget_usd"] * 100).round(1),
    )
    return result


def compute_burn_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly burn rate by category."""
    monthly = df.copy()
    monthly = monthly.assign(month=monthly["disbursement_date"].dt.to_period("M"))
    burn = (
        monthly.groupby(["month", "category"], as_index=False)
        .agg(total_spent=("spent_usd", "sum"))
    )
    burn = burn.assign(month_str=burn["month"].astype(str))
    return burn


def compute_partner_payments(df: pd.DataFrame) -> pd.DataFrame:
    """Compute payment summary per partner."""
    return (
        df.groupby("partner", as_index=False)
        .agg(
            total_budget=("budget_usd", "sum"),
            total_disbursed=("disbursed_usd", "sum"),
            total_spent=("spent_usd", "sum"),
            project_count=("project_id", "count"),
        )
        .assign(
            pending_disbursement=lambda x: x["total_budget"] - x["total_disbursed"],
        )
        .sort_values("total_budget", ascending=False)
    )


def compute_disbursement_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Compute cumulative disbursement over time."""
    timeline = (
        df[["disbursement_date", "disbursed_usd"]]
        .copy()
        .sort_values("disbursement_date")
    )
    timeline = timeline.assign(
        cumulative_disbursed=timeline["disbursed_usd"].cumsum()
    )
    return timeline


def compute_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute financial summary by project category."""
    return (
        df.groupby("category", as_index=False)
        .agg(
            total_budget=("budget_usd", "sum"),
            total_spent=("spent_usd", "sum"),
            total_disbursed=("disbursed_usd", "sum"),
            project_count=("project_id", "count"),
        )
        .assign(
            utilization_pct=lambda x: (x["total_spent"] / x["total_budget"] * 100).round(1),
        )
    )


def compute_kpi_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Compute top-level KPI metrics."""
    total_budget = float(df["budget_usd"].sum())
    total_disbursed = float(df["disbursed_usd"].sum())
    total_spent = float(df["spent_usd"].sum())
    project_count = len(df)

    return {
        "total_budget": total_budget,
        "total_disbursed": total_disbursed,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent,
        "overall_burn_rate": round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0.0,
        "disbursement_rate": round(total_disbursed / total_budget * 100, 1) if total_budget > 0 else 0.0,
        "project_count": project_count,
    }
