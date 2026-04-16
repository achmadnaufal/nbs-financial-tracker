"""Budget variance analyzer for NbS project financial tracking.

Computes planned-vs-actual spending variance per cost category, flags
projects that exceed configurable tolerance thresholds, and produces a
summary report — all using immutable patterns (input DataFrames are never
mutated; every function returns a new object).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_TOLERANCE_PCT: Final[float] = 10.0  # ±10 % considered on-track
FLAG_OVER: Final[str] = "OVER_BUDGET"
FLAG_UNDER: Final[str] = "UNDER_BUDGET"
FLAG_ON_TRACK: Final[str] = "ON_TRACK"

REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"project_id", "project_name", "category", "budget_usd", "spent_usd"}
)


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class VarianceSummary:
    """Aggregated variance statistics for a single category.

    Attributes:
        category: Cost category name (e.g. "Restoration").
        total_budget_usd: Sum of planned budgets in this category.
        total_spent_usd: Sum of actual spending in this category.
        variance_usd: total_spent_usd - total_budget_usd (positive = over).
        variance_pct: variance_usd / total_budget_usd * 100, or 0 when budget is 0.
        flag: "OVER_BUDGET", "UNDER_BUDGET", or "ON_TRACK" relative to tolerance.
        project_count: Number of projects in this category.
        flagged_projects: Project IDs whose individual variance exceeds tolerance.
    """

    category: str
    total_budget_usd: float
    total_spent_usd: float
    variance_usd: float
    variance_pct: float
    flag: str
    project_count: int
    flagged_projects: tuple[str, ...]


# ── Validation helpers ───────────────────────────────────────────────────────


def _validate_dataframe(df: pd.DataFrame) -> None:
    """Raise ValueError if *df* is missing required columns or has bad types.

    Args:
        df: DataFrame to validate.

    Raises:
        ValueError: When required columns are absent or numeric columns contain
            non-numeric data.
        TypeError: When *df* is not a pandas DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {sorted(missing)}")

    if not df.empty:
        for col in ("budget_usd", "spent_usd"):
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column '{col}' must be numeric, got {df[col].dtype}")


def _validate_tolerance(tolerance_pct: float) -> None:
    """Raise ValueError when tolerance is not a finite positive number.

    Args:
        tolerance_pct: Tolerance threshold in percent.

    Raises:
        ValueError: When tolerance_pct is negative or not finite.
    """
    if not (isinstance(tolerance_pct, (int, float)) and tolerance_pct >= 0):
        raise ValueError(
            f"tolerance_pct must be a non-negative number, got {tolerance_pct!r}"
        )


# ── Core functions ───────────────────────────────────────────────────────────


def compute_project_variance(
    df: pd.DataFrame,
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
) -> pd.DataFrame:
    """Return per-project variance between budgeted and actual spend.

    The input DataFrame is never modified; all results are returned in a new
    DataFrame.

    Args:
        df: Project data with at minimum the columns defined in
            ``REQUIRED_COLUMNS``: ``project_id``, ``project_name``,
            ``category``, ``budget_usd``, ``spent_usd``.
        tolerance_pct: Percentage band within which a project is considered
            on-track.  Defaults to ``DEFAULT_TOLERANCE_PCT`` (10 %).

    Returns:
        A new DataFrame with one row per input project containing:

        - All original columns.
        - ``variance_usd``    — spent_usd minus budget_usd.
        - ``variance_pct``    — variance as a percentage of budget_usd (NaN
          when budget_usd is 0).
        - ``flag``            — "OVER_BUDGET", "UNDER_BUDGET", or "ON_TRACK".

    Raises:
        TypeError: When *df* is not a pandas DataFrame.
        ValueError: When required columns are missing or numeric columns have
            wrong dtype, or *tolerance_pct* is invalid.

    Example:
        >>> import pandas as pd
        >>> from src.budget_variance_analyzer import compute_project_variance
        >>> data = pd.DataFrame({
        ...     "project_id": ["NBS-001", "NBS-002"],
        ...     "project_name": ["Mangrove A", "Peatland B"],
        ...     "category": ["Restoration", "Rewetting"],
        ...     "budget_usd": [100_000, 200_000],
        ...     "spent_usd":  [115_000, 195_000],
        ... })
        >>> result = compute_project_variance(data, tolerance_pct=10.0)
        >>> result[["project_id", "variance_pct", "flag"]].to_string(index=False)
          project_id  variance_pct         flag
             NBS-001          15.0  OVER_BUDGET
             NBS-002          -2.5     ON_TRACK
    """
    _validate_dataframe(df)
    _validate_tolerance(tolerance_pct)

    if df.empty:
        empty = df.copy()
        empty["variance_usd"] = pd.Series(dtype=float)
        empty["variance_pct"] = pd.Series(dtype=float)
        empty["flag"] = pd.Series(dtype=str)
        return empty

    variance_usd = df["spent_usd"] - df["budget_usd"]
    with_zero_budget = df["budget_usd"].replace(0, float("nan"))
    variance_pct = (variance_usd / with_zero_budget * 100).round(2)

    flag = variance_pct.apply(
        lambda v: (
            FLAG_OVER if v > tolerance_pct
            else FLAG_UNDER if v < -tolerance_pct
            else FLAG_ON_TRACK
        )
        if pd.notna(v)
        else FLAG_ON_TRACK
    )

    return df.assign(
        variance_usd=variance_usd,
        variance_pct=variance_pct,
        flag=flag,
    )


def compute_category_variance(
    df: pd.DataFrame,
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
) -> list[VarianceSummary]:
    """Aggregate per-project variance into per-category summaries.

    Args:
        df: Project data (same schema as :func:`compute_project_variance`).
        tolerance_pct: Tolerance band in percent for flagging categories.

    Returns:
        A list of :class:`VarianceSummary` instances, one per category, sorted
        by descending absolute variance percentage.

    Raises:
        TypeError: When *df* is not a pandas DataFrame.
        ValueError: When required columns are missing or *tolerance_pct* is
            invalid.

    Example:
        >>> import pandas as pd
        >>> from src.budget_variance_analyzer import compute_category_variance
        >>> data = pd.DataFrame({
        ...     "project_id": ["NBS-001", "NBS-002", "NBS-003"],
        ...     "project_name": ["A", "B", "C"],
        ...     "category": ["Restoration", "Restoration", "Marine"],
        ...     "budget_usd": [100_000, 80_000, 50_000],
        ...     "spent_usd":  [120_000, 82_000, 45_000],
        ... })
        >>> summaries = compute_category_variance(data, tolerance_pct=10.0)
        >>> summaries[0].category
        'Restoration'
        >>> summaries[0].flag
        'OVER_BUDGET'
    """
    _validate_dataframe(df)
    _validate_tolerance(tolerance_pct)

    if df.empty:
        return []

    project_var = compute_project_variance(df, tolerance_pct=tolerance_pct)

    summaries: list[VarianceSummary] = []
    for category, group in project_var.groupby("category", sort=False):
        total_budget = float(group["budget_usd"].sum())
        total_spent = float(group["spent_usd"].sum())
        variance_usd = total_spent - total_budget
        variance_pct = (
            round(variance_usd / total_budget * 100, 2) if total_budget != 0 else 0.0
        )

        if variance_pct > tolerance_pct:
            flag = FLAG_OVER
        elif variance_pct < -tolerance_pct:
            flag = FLAG_UNDER
        else:
            flag = FLAG_ON_TRACK

        flagged = tuple(
            group.loc[group["flag"] != FLAG_ON_TRACK, "project_id"].tolist()
        )

        summaries.append(
            VarianceSummary(
                category=str(category),
                total_budget_usd=total_budget,
                total_spent_usd=total_spent,
                variance_usd=variance_usd,
                variance_pct=variance_pct,
                flag=flag,
                project_count=len(group),
                flagged_projects=flagged,
            )
        )

    summaries.sort(key=lambda s: abs(s.variance_pct), reverse=True)
    return summaries


def build_variance_report(
    df: pd.DataFrame,
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
) -> pd.DataFrame:
    """Return a flat DataFrame report combining project- and category-level variance.

    Suitable for display in a Streamlit table or export to Excel.

    Args:
        df: Project data (same schema as :func:`compute_project_variance`).
        tolerance_pct: Tolerance band in percent.

    Returns:
        A DataFrame with columns:

        - ``project_id``, ``project_name``, ``category``
        - ``budget_usd``, ``spent_usd``
        - ``variance_usd``, ``variance_pct``, ``flag``
        - ``category_flag`` — flag for the aggregated category-level variance.

    Raises:
        TypeError: When *df* is not a pandas DataFrame.
        ValueError: When required columns are missing or *tolerance_pct* is
            invalid.

    Example:
        >>> import pandas as pd
        >>> from src.budget_variance_analyzer import build_variance_report
        >>> data = pd.DataFrame({
        ...     "project_id": ["NBS-001"],
        ...     "project_name": ["Mangrove A"],
        ...     "category": ["Restoration"],
        ...     "budget_usd": [100_000],
        ...     "spent_usd":  [112_000],
        ... })
        >>> report = build_variance_report(data, tolerance_pct=10.0)
        >>> report["flag"].iloc[0]
        'OVER_BUDGET'
        >>> report["category_flag"].iloc[0]
        'OVER_BUDGET'
    """
    _validate_dataframe(df)
    _validate_tolerance(tolerance_pct)

    project_var = compute_project_variance(df, tolerance_pct=tolerance_pct)
    cat_summaries = compute_category_variance(df, tolerance_pct=tolerance_pct)
    cat_flag_map: dict[str, str] = {s.category: s.flag for s in cat_summaries}

    report = project_var[
        [
            "project_id",
            "project_name",
            "category",
            "budget_usd",
            "spent_usd",
            "variance_usd",
            "variance_pct",
            "flag",
        ]
    ].copy()

    report = report.assign(
        category_flag=report["category"].map(cat_flag_map).fillna(FLAG_ON_TRACK)
    )
    return report
