# NbS Project Financial Tracker

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-30%2B%20passing-brightgreen)](tests/)

Streamlit web app for tracking Nature-based Solutions (NbS) project finances — budget allocation, disbursement timeline, partner payments, and burn rate. Built for PUR's project management workflow.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
# Open http://localhost:8501
```

## Features

- **Budget vs Actuals** — Grouped bar chart comparing budget, disbursed, and spent amounts per project
- **Burn Rate** — Monthly spending trends by category with utilization gauge
- **Partner Payments** — Payment status and pending disbursements per partner organization
- **Disbursement Timeline** — Cumulative disbursement area chart with category breakdown
- **Interactive Filters** — Filter by category, partner, and location
- **Excel Export** — Download multi-sheet financial report
- **CSV Upload** — Use your own data or the bundled Indonesian NbS sample dataset

## New: Budget Variance Analyzer

`src/budget_variance_analyzer.py` computes planned-vs-actual spending variance
per project and cost category, flags outliers against a configurable tolerance
threshold, and produces a flat report ready for display or export.

### Step-by-step usage

```python
import pandas as pd
from src.budget_variance_analyzer import (
    compute_project_variance,
    compute_category_variance,
    build_variance_report,
)

# 1. Load your project data (must include project_id, project_name,
#    category, budget_usd, spent_usd columns).
df = pd.read_csv("demo/sample_data.csv")

# 2. Per-project variance — adds variance_usd, variance_pct, flag columns.
project_var = compute_project_variance(df, tolerance_pct=10.0)
print(project_var[["project_id", "variance_pct", "flag"]])

# 3. Category-level aggregates — returns a list of VarianceSummary dataclasses.
cat_summaries = compute_category_variance(df, tolerance_pct=10.0)
for s in cat_summaries:
    print(f"{s.category}: {s.variance_pct:+.1f}%  [{s.flag}]")
    if s.flagged_projects:
        print(f"  Flagged: {', '.join(s.flagged_projects)}")

# 4. Flat report combining project- and category-level flags (ideal for Excel export).
report = build_variance_report(df, tolerance_pct=10.0)
print(report[["project_id", "flag", "category_flag"]])
```

**Flags:** `OVER_BUDGET` (variance > +tolerance %), `UNDER_BUDGET` (variance < -tolerance %),
`ON_TRACK` (within band). Default tolerance is 10 %.

---

## New: Carbon Project Cashflow NPV/IRR Calculator

`src/carbon_cashflow_npv.py` evaluates nature-based carbon projects on a
discounted-cashflow basis: NPV, IRR, discounted payback period, and the
break-even carbon credit price required to reach NPV = 0. Use it for
investment screening across a portfolio of credit-generating NbS projects.

### Quick Start

```bash
pip install -r requirements.txt
pytest tests/ -q
```

### Step-by-step usage

```python
import pandas as pd
from src.carbon_cashflow_npv import (
    evaluate_project,
    evaluate_portfolio,
    npv,
    irr,
)

# 1. Evaluate a single project (CAPEX in year 0, then annual revenue - OPEX).
metrics = evaluate_project(
    project_id="NBS-C01",
    capex_usd=500_000,
    opex_annual_usd=50_000,
    expected_credits_per_year=20_000,
    price_per_credit_usd=12.0,
    duration_years=10,
    discount_rate=0.08,  # 8 % cost of capital
)
print(metrics)
# CashflowMetrics(project_id='NBS-C01', npv_usd=..., irr=...,
#                 discounted_payback_years=4, breakeven_price_usd=...)

# 2. Evaluate an entire portfolio from CSV.
df = pd.read_csv("sample_data/sample_data.csv")
report = evaluate_portfolio(df, discount_rate=0.08)
print(report.head())
# Sorted by descending NPV — top picks first.

# 3. Low-level primitives are exposed too.
cashflows = [-1_000, 600, 600]
print(npv(cashflows, discount_rate=0.10))   # 41.32
print(irr(cashflows))                       # ≈ 0.1307
```

**Edge cases handled with clear errors:**
- Empty portfolio → `ValueError("Cannot evaluate an empty portfolio")`
- Missing required columns → `ValueError` listing the missing names
- `discount_rate <= -1` or NaN → `ValueError`
- Zero discount rate → NPV equals the simple cashflow sum (no division-by-zero)
- Negative or all-negative cashflows → IRR returns `None` (no sign change)
- Project never recovers CAPEX → `discounted_payback_years` is `None`

---

## Sample Output

The app loads with 25 rows of realistic Indonesian NbS project data covering:
- Mangrove restoration, peatland rewetting, agroforestry, marine conservation
- Partners across Kalimantan, Riau, Sulawesi, Papua, Java, and more
- Budget range: $55,000 – $250,000 USD

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Data | Pandas |
| Charts | Plotly |
| Export | openpyxl |
| Tests | pytest |

## Project Structure

```
nbs-financial-tracker/
├── app.py                  # Main Streamlit application
├── src/
│   ├── data_loader.py      # CSV loading, validation, filtering
│   ├── calculations.py     # Financial computations
│   ├── charts.py           # Plotly chart builders
│   └── export.py           # Excel/CSV export utilities
├── demo/
│   └── sample_data.csv     # 25 rows of Indonesian NbS project data
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_data_loader.py # Data loading & validation tests
│   ├── test_calculations.py# Financial calculation tests
│   ├── test_charts.py      # Chart generation tests
│   ├── test_export.py      # Export functionality tests
│   └── test_integration.py # End-to-end pipeline tests
├── requirements.txt
├── LICENSE
└── README.md
```

## Running Tests

```bash
pytest tests/ -v
```

## License

[MIT](LICENSE)
