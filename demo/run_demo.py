"""CLI demo: NbS portfolio financial KPIs from sample data.

Run from repo root:

    python3 -m demo.run_demo
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.calculations import (
    compute_budget_vs_actuals,
    compute_category_summary,
    compute_kpi_metrics,
    compute_partner_payments,
)
from src.data_loader import get_sample_data_path, load_csv


def _money(v: float) -> str:
    return f"${v:>12,.0f}"


def main() -> None:
    df = load_csv(get_sample_data_path())

    print("=" * 70)
    print("NbS Financial Tracker — portfolio demo")
    print("=" * 70)

    kpi = compute_kpi_metrics(df)
    print(f"  Projects in portfolio:       {kpi['project_count']:>10d}")
    print(f"  Total budget:                {_money(kpi['total_budget'])}")
    print(f"  Total disbursed:             {_money(kpi['total_disbursed'])}")
    print(f"  Total spent:                 {_money(kpi['total_spent'])}")
    print(f"  Total remaining:             {_money(kpi['total_remaining'])}")
    print(f"  Disbursement rate:           {kpi['disbursement_rate']:>10.1f}%")
    print(f"  Overall burn rate:           {kpi['overall_burn_rate']:>10.1f}%")
    print()

    print("Spending by category:")
    cat = compute_category_summary(df)
    print(cat.to_string(index=False, float_format=lambda v: f"{v:,.0f}"))
    print()

    print("Top 5 partners by budget:")
    partners = compute_partner_payments(df).head(5)
    print(partners.to_string(index=False, float_format=lambda v: f"{v:,.0f}"))
    print()

    print("Projects with utilisation > 90% (burn-rate watchlist):")
    bva = compute_budget_vs_actuals(df)
    hot = bva[bva["utilization_pct"] >= 90].sort_values("utilization_pct", ascending=False)
    if hot.empty:
        print("  (none)")
    else:
        print(hot[["project_id", "project_name", "utilization_pct"]].to_string(index=False))
    print()
    print("Run `streamlit run app.py` for the interactive dashboard.")


if __name__ == "__main__":
    main()
