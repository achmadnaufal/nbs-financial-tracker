## [Unreleased] - 2026-04-18

### Added

- `src/carbon_cashflow_npv.py`: Carbon Project Cashflow NPV/IRR calculator.
  Builds annual cashflow streams (CAPEX year 0, revenue minus OPEX years 1..N)
  and computes Net Present Value, Internal Rate of Return (bisection),
  discounted payback period, and break-even carbon credit price for
  nature-based carbon projects. Public API: `evaluate_project`,
  `evaluate_portfolio`, `build_cashflow_series`, `npv`, `irr`,
  `discounted_payback_period`, `breakeven_credit_price`, plus
  `CashflowMetrics` dataclass. All functions are immutable.
- `src/__init__.py`: re-exports the new public surface.
- `tests/test_carbon_cashflow_npv.py`: 26 pytest tests covering happy path,
  zero discount rate, negative-only cashflows, empty portfolio, missing
  columns, IRR sign-change handling, payback non-recovery, and
  break-even price math.
- `sample_data/sample_data.csv`: 20-row carbon-project dataset
  (project_id, project_name, currency, capex_usd, opex_annual_usd,
  expected_credits_per_year, price_per_credit_usd, project_start_date,
  project_duration_years, country) spanning 9 countries.
- `README.md`: Quick Start and step-by-step usage section for the new module.

## [Unreleased] - 2026-04-17

### Added

- `src/budget_variance_analyzer.py`: Budget Variance Analyzer module.
  Computes planned-vs-actual spending variance per project and cost category,
  flags projects/categories that breach a configurable tolerance threshold
  (default ±10 %), and exposes three public functions:
  `compute_project_variance`, `compute_category_variance`, and
  `build_variance_report`. All functions are immutable (inputs never mutated).
- `tests/test_budget_variance_analyzer.py`: 25 pytest tests covering happy
  path, empty DataFrame, zero budget, single row, negative spend, type/schema
  validation errors, determinism, and parametrized flag scenarios.
