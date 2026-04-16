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
