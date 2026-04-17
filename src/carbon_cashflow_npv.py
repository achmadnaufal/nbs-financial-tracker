"""Carbon project cashflow NPV/IRR calculator for NbS investments.

Computes Net Present Value (NPV), Internal Rate of Return (IRR), discounted
payback period, and break-even carbon credit price for nature-based carbon
projects. Models a typical project lifecycle: an initial CAPEX outlay
(year 0) followed by annual OPEX and carbon credit revenue across the
project duration.

All functions are immutable — inputs are never mutated and every function
returns a new object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_DISCOUNT_RATE: Final[float] = 0.08  # 8 % weighted cost of capital
IRR_MAX_ITERATIONS: Final[int] = 200
IRR_TOLERANCE: Final[float] = 1e-7
IRR_LOW_BOUND: Final[float] = -0.999
IRR_HIGH_BOUND: Final[float] = 10.0

REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "project_id",
        "capex_usd",
        "opex_annual_usd",
        "expected_credits_per_year",
        "price_per_credit_usd",
        "project_duration_years",
    }
)


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CashflowMetrics:
    """Discounted cashflow metrics for a single carbon project.

    Attributes:
        project_id: Identifier of the project being evaluated.
        npv_usd: Net Present Value of the cashflow stream in USD.
        irr: Internal Rate of Return as a decimal fraction (0.12 == 12 %),
            or ``None`` when no real IRR exists in the search interval.
        discounted_payback_years: Year (1-indexed) at which cumulative
            discounted cashflow turns non-negative; ``None`` when the
            project never recovers its CAPEX.
        breakeven_price_usd: Carbon credit price at which NPV equals zero
            given the project's CAPEX, OPEX, credit volume, duration, and
            discount rate. ``None`` when ``expected_credits_per_year`` is 0.
        total_revenue_usd: Undiscounted total carbon credit revenue.
        total_cost_usd: CAPEX plus undiscounted total OPEX.
    """

    project_id: str
    npv_usd: float
    irr: float | None
    discounted_payback_years: int | None
    breakeven_price_usd: float | None
    total_revenue_usd: float
    total_cost_usd: float


# ── Validation helpers ───────────────────────────────────────────────────────


def _validate_discount_rate(discount_rate: float) -> None:
    """Raise ValueError when discount_rate is not a finite number > -1.

    Args:
        discount_rate: Periodic discount rate (e.g. 0.08 for 8 %).

    Raises:
        ValueError: When the rate is non-numeric, NaN, or <= -1.
    """
    if not isinstance(discount_rate, (int, float)):
        raise ValueError(
            f"discount_rate must be numeric, got {type(discount_rate).__name__}"
        )
    if discount_rate != discount_rate:  # NaN check
        raise ValueError("discount_rate must not be NaN")
    if discount_rate <= -1:
        raise ValueError(f"discount_rate must be > -1, got {discount_rate}")


def _validate_duration(duration_years: int) -> None:
    """Raise ValueError when duration is not a positive integer.

    Args:
        duration_years: Project lifespan in whole years.

    Raises:
        ValueError: When duration_years is not a positive integer.
    """
    if not isinstance(duration_years, int) or isinstance(duration_years, bool):
        raise ValueError(
            f"duration_years must be int, got {type(duration_years).__name__}"
        )
    if duration_years < 1:
        raise ValueError(f"duration_years must be >= 1, got {duration_years}")


def _validate_dataframe(df: pd.DataFrame) -> None:
    """Raise ValueError when *df* is missing required carbon-project columns.

    Args:
        df: DataFrame to validate.

    Raises:
        TypeError: When *df* is not a pandas DataFrame.
        ValueError: When required columns are absent or the frame is empty.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")
    if df.empty:
        raise ValueError("Cannot evaluate an empty portfolio")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {sorted(missing)}")


# ── Core functions ───────────────────────────────────────────────────────────


def build_cashflow_series(
    capex_usd: float,
    opex_annual_usd: float,
    expected_credits_per_year: float,
    price_per_credit_usd: float,
    duration_years: int,
) -> list[float]:
    """Construct an annual cashflow stream for a carbon project.

    Year 0 is the CAPEX outlay (negative); years 1..N each contain the net
    of revenue (credits * price) minus annual OPEX.

    Args:
        capex_usd: Up-front capital expenditure (positive number).
        opex_annual_usd: Annual operating cost (positive number).
        expected_credits_per_year: Annual carbon credit volume.
        price_per_credit_usd: Price per carbon credit in USD.
        duration_years: Operating lifespan after year 0 (positive int).

    Returns:
        A list of length ``duration_years + 1`` of floats.

    Raises:
        ValueError: When duration_years is not a positive integer.
    """
    _validate_duration(duration_years)
    annual_net = (
        float(expected_credits_per_year) * float(price_per_credit_usd)
        - float(opex_annual_usd)
    )
    return [-float(capex_usd), *([annual_net] * duration_years)]


def npv(cashflows: list[float], discount_rate: float = DEFAULT_DISCOUNT_RATE) -> float:
    """Return Net Present Value of *cashflows* at *discount_rate*.

    Args:
        cashflows: Sequence of period cashflows starting at period 0.
        discount_rate: Periodic discount rate (e.g. 0.08 for 8 %). A rate of
            0 returns the simple sum of cashflows.

    Returns:
        Net present value as a float.

    Raises:
        ValueError: When ``cashflows`` is empty or ``discount_rate`` is invalid.

    Example:
        >>> npv([-1000, 600, 600], discount_rate=0.10)
        41.32...
    """
    if not cashflows:
        raise ValueError("cashflows must contain at least one period")
    _validate_discount_rate(discount_rate)
    return sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows: list[float]) -> float | None:
    """Return Internal Rate of Return via bisection, or None when no sign change.

    IRR is the discount rate that makes NPV = 0. Bisection requires the
    cashflow stream to contain at least one positive and one negative
    period; otherwise ``None`` is returned.

    Args:
        cashflows: Sequence of period cashflows starting at period 0.

    Returns:
        IRR as a decimal fraction, or ``None`` when no root exists in the
        ``[IRR_LOW_BOUND, IRR_HIGH_BOUND]`` search interval.

    Raises:
        ValueError: When ``cashflows`` is empty.
    """
    if not cashflows:
        raise ValueError("cashflows must contain at least one period")
    has_pos = any(cf > 0 for cf in cashflows)
    has_neg = any(cf < 0 for cf in cashflows)
    if not (has_pos and has_neg):
        return None

    low, high = IRR_LOW_BOUND, IRR_HIGH_BOUND
    npv_low = npv(cashflows, low)
    npv_high = npv(cashflows, high)
    if npv_low * npv_high > 0:
        return None  # no sign change inside the search bracket

    for _ in range(IRR_MAX_ITERATIONS):
        mid = (low + high) / 2
        npv_mid = npv(cashflows, mid)
        if abs(npv_mid) < IRR_TOLERANCE:
            return mid
        if npv_low * npv_mid < 0:
            high, npv_high = mid, npv_mid
        else:
            low, npv_low = mid, npv_mid
    return (low + high) / 2


def discounted_payback_period(
    cashflows: list[float],
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
) -> int | None:
    """Return the first 1-indexed year where cumulative discounted cashflow >= 0.

    Args:
        cashflows: Sequence of period cashflows starting at period 0.
        discount_rate: Periodic discount rate.

    Returns:
        Year index (>= 1) at which payback is achieved, or ``None`` when the
        project never recovers its initial outlay within the supplied horizon.

    Raises:
        ValueError: When ``cashflows`` is empty or ``discount_rate`` is invalid.
    """
    if not cashflows:
        raise ValueError("cashflows must contain at least one period")
    _validate_discount_rate(discount_rate)
    cumulative = 0.0
    for t, cf in enumerate(cashflows):
        cumulative += cf / (1 + discount_rate) ** t
        if t > 0 and cumulative >= 0:
            return t
    return None


def breakeven_credit_price(
    capex_usd: float,
    opex_annual_usd: float,
    expected_credits_per_year: float,
    duration_years: int,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
) -> float | None:
    """Return the credit price at which project NPV equals zero.

    Solved analytically by treating annual revenue as the free variable:
    ``price * credits * AnnuityFactor == CAPEX + OPEX * AnnuityFactor``.

    Args:
        capex_usd: Up-front capital expenditure (positive).
        opex_annual_usd: Annual operating cost (positive).
        expected_credits_per_year: Annual credit volume; must be > 0.
        duration_years: Project lifespan in years; must be >= 1.
        discount_rate: Periodic discount rate.

    Returns:
        Break-even price per credit in USD, or ``None`` when
        ``expected_credits_per_year`` is 0.

    Raises:
        ValueError: When duration or discount rate inputs are invalid.
    """
    _validate_duration(duration_years)
    _validate_discount_rate(discount_rate)
    if expected_credits_per_year <= 0:
        return None

    if discount_rate == 0:
        annuity_factor = float(duration_years)
    else:
        annuity_factor = (1 - (1 + discount_rate) ** -duration_years) / discount_rate

    required_annual_revenue = (
        float(capex_usd) / annuity_factor + float(opex_annual_usd)
    )
    return required_annual_revenue / float(expected_credits_per_year)


def evaluate_project(
    project_id: str,
    capex_usd: float,
    opex_annual_usd: float,
    expected_credits_per_year: float,
    price_per_credit_usd: float,
    duration_years: int,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
) -> CashflowMetrics:
    """Compute the full set of cashflow metrics for a single carbon project.

    Args:
        project_id: Identifier carried into the result for traceability.
        capex_usd: Up-front capital expenditure.
        opex_annual_usd: Annual operating cost.
        expected_credits_per_year: Annual carbon credit production.
        price_per_credit_usd: Price per carbon credit in USD.
        duration_years: Project lifespan in years.
        discount_rate: Periodic discount rate (default 0.08).

    Returns:
        A :class:`CashflowMetrics` dataclass with NPV, IRR, payback,
        break-even price, and undiscounted totals.

    Raises:
        ValueError: When duration or discount rate inputs are invalid.

    Example:
        >>> m = evaluate_project(
        ...     "NBS-001", capex_usd=500_000, opex_annual_usd=50_000,
        ...     expected_credits_per_year=20_000,
        ...     price_per_credit_usd=12.0, duration_years=10,
        ...     discount_rate=0.08,
        ... )
        >>> m.npv_usd > 0
        True
    """
    cashflows = build_cashflow_series(
        capex_usd=capex_usd,
        opex_annual_usd=opex_annual_usd,
        expected_credits_per_year=expected_credits_per_year,
        price_per_credit_usd=price_per_credit_usd,
        duration_years=duration_years,
    )
    return CashflowMetrics(
        project_id=str(project_id),
        npv_usd=round(npv(cashflows, discount_rate), 2),
        irr=irr(cashflows),
        discounted_payback_years=discounted_payback_period(cashflows, discount_rate),
        breakeven_price_usd=(
            round(p, 4)
            if (
                p := breakeven_credit_price(
                    capex_usd=capex_usd,
                    opex_annual_usd=opex_annual_usd,
                    expected_credits_per_year=expected_credits_per_year,
                    duration_years=duration_years,
                    discount_rate=discount_rate,
                )
            )
            is not None
            else None
        ),
        total_revenue_usd=round(
            float(expected_credits_per_year)
            * float(price_per_credit_usd)
            * duration_years,
            2,
        ),
        total_cost_usd=round(
            float(capex_usd) + float(opex_annual_usd) * duration_years, 2
        ),
    )


def evaluate_portfolio(
    df: pd.DataFrame,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
) -> pd.DataFrame:
    """Evaluate a portfolio of carbon projects and return a metrics DataFrame.

    Args:
        df: Portfolio DataFrame with at minimum the columns in
            ``REQUIRED_COLUMNS``: ``project_id``, ``capex_usd``,
            ``opex_annual_usd``, ``expected_credits_per_year``,
            ``price_per_credit_usd``, ``project_duration_years``.
        discount_rate: Periodic discount rate applied to every project.

    Returns:
        A new DataFrame sorted by descending NPV with the columns
        ``project_id``, ``npv_usd``, ``irr``, ``discounted_payback_years``,
        ``breakeven_price_usd``, ``total_revenue_usd``, ``total_cost_usd``.

    Raises:
        TypeError: When *df* is not a pandas DataFrame.
        ValueError: When the portfolio is empty, required columns are missing,
            or ``discount_rate`` is invalid.
    """
    _validate_dataframe(df)
    _validate_discount_rate(discount_rate)

    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        metrics = evaluate_project(
            project_id=row["project_id"],
            capex_usd=float(row["capex_usd"]),
            opex_annual_usd=float(row["opex_annual_usd"]),
            expected_credits_per_year=float(row["expected_credits_per_year"]),
            price_per_credit_usd=float(row["price_per_credit_usd"]),
            duration_years=int(row["project_duration_years"]),
            discount_rate=discount_rate,
        )
        rows.append(
            {
                "project_id": metrics.project_id,
                "npv_usd": metrics.npv_usd,
                "irr": metrics.irr,
                "discounted_payback_years": metrics.discounted_payback_years,
                "breakeven_price_usd": metrics.breakeven_price_usd,
                "total_revenue_usd": metrics.total_revenue_usd,
                "total_cost_usd": metrics.total_cost_usd,
            }
        )
    return pd.DataFrame(rows).sort_values("npv_usd", ascending=False).reset_index(
        drop=True
    )
