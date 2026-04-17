"""Tests for src.carbon_cashflow_npv — NPV/IRR carbon project calculator."""

from __future__ import annotations

import pandas as pd
import pytest

from src.carbon_cashflow_npv import (
    DEFAULT_DISCOUNT_RATE,
    CashflowMetrics,
    breakeven_credit_price,
    build_cashflow_series,
    discounted_payback_period,
    evaluate_portfolio,
    evaluate_project,
    irr,
    npv,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def carbon_portfolio_df() -> pd.DataFrame:
    """Three-project carbon portfolio with mixed economics."""
    return pd.DataFrame(
        {
            "project_id": ["NBS-C01", "NBS-C02", "NBS-C03"],
            "project_name": ["Mangrove A", "Peatland B", "Agroforestry C"],
            "capex_usd": [500_000, 1_000_000, 200_000],
            "opex_annual_usd": [50_000, 80_000, 20_000],
            "expected_credits_per_year": [20_000, 25_000, 5_000],
            "price_per_credit_usd": [12.0, 9.0, 15.0],
            "project_duration_years": [10, 15, 8],
        }
    )


# ── build_cashflow_series ────────────────────────────────────────────────────


def test_build_cashflow_series_happy_path() -> None:
    series = build_cashflow_series(
        capex_usd=500_000,
        opex_annual_usd=50_000,
        expected_credits_per_year=20_000,
        price_per_credit_usd=12.0,
        duration_years=10,
    )
    assert len(series) == 11
    assert series[0] == -500_000
    # 20_000 * 12 - 50_000 = 190_000 each year
    assert all(cf == 190_000 for cf in series[1:])


def test_build_cashflow_series_rejects_zero_duration() -> None:
    with pytest.raises(ValueError, match="duration_years must be >= 1"):
        build_cashflow_series(
            capex_usd=100,
            opex_annual_usd=10,
            expected_credits_per_year=1,
            price_per_credit_usd=1,
            duration_years=0,
        )


def test_build_cashflow_series_rejects_bool_duration() -> None:
    with pytest.raises(ValueError, match="duration_years must be int"):
        build_cashflow_series(
            capex_usd=100,
            opex_annual_usd=10,
            expected_credits_per_year=1,
            price_per_credit_usd=1,
            duration_years=True,  # type: ignore[arg-type]
        )


# ── npv ──────────────────────────────────────────────────────────────────────


def test_npv_simple_known_value() -> None:
    # CF: -1000, +600, +600 at 10 % => -1000 + 545.45 + 495.87 = 41.32
    result = npv([-1000, 600, 600], discount_rate=0.10)
    assert result == pytest.approx(41.3223, abs=1e-3)


def test_npv_zero_discount_rate_equals_sum() -> None:
    cashflows = [-1000, 200, 300, 400, 500]
    assert npv(cashflows, discount_rate=0.0) == sum(cashflows)


def test_npv_rejects_empty_cashflows() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        npv([], discount_rate=0.05)


def test_npv_rejects_invalid_discount_rate() -> None:
    with pytest.raises(ValueError, match="discount_rate must be > -1"):
        npv([-100, 50, 60], discount_rate=-1.0)


def test_npv_rejects_nan_discount_rate() -> None:
    with pytest.raises(ValueError, match="must not be NaN"):
        npv([-100, 50, 60], discount_rate=float("nan"))


def test_npv_negative_only_cashflows() -> None:
    # All negative cashflows: NPV must also be negative.
    assert npv([-100, -50, -25], discount_rate=0.05) < 0


# ── irr ──────────────────────────────────────────────────────────────────────


def test_irr_known_value() -> None:
    # -1000 then 600, 600: IRR ≈ 13.07 %
    result = irr([-1000, 600, 600])
    assert result is not None
    assert result == pytest.approx(0.1306623, abs=1e-4)


def test_irr_no_sign_change_returns_none() -> None:
    assert irr([-100, -50, -25]) is None
    assert irr([100, 50, 25]) is None


def test_irr_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one period"):
        irr([])


def test_irr_npv_zero_at_irr() -> None:
    cashflows = [-500_000, *([190_000] * 10)]
    rate = irr(cashflows)
    assert rate is not None
    assert npv(cashflows, rate) == pytest.approx(0.0, abs=1e-3)


# ── discounted_payback_period ────────────────────────────────────────────────


def test_payback_recovered_within_horizon() -> None:
    # 500k CAPEX, 190k/yr net at 8 % => payback in year 4
    cashflows = [-500_000, *([190_000] * 10)]
    assert discounted_payback_period(cashflows, discount_rate=0.08) == 4


def test_payback_returns_none_when_never_recovered() -> None:
    cashflows = [-1_000_000, *([10_000] * 5)]
    assert discounted_payback_period(cashflows, discount_rate=0.08) is None


def test_payback_zero_discount_rate() -> None:
    cashflows = [-1000, 250, 250, 250, 250, 250]
    # Cumulative reaches 0 at year 4: -1000+250+250+250+250 = 0
    assert discounted_payback_period(cashflows, discount_rate=0.0) == 4


# ── breakeven_credit_price ───────────────────────────────────────────────────


def test_breakeven_price_zero_discount_rate() -> None:
    # CAPEX=100k, OPEX=10k/yr, 1000 credits/yr, 10yr, r=0
    # required annual revenue = 100k/10 + 10k = 20k => price = 20
    price = breakeven_credit_price(
        capex_usd=100_000,
        opex_annual_usd=10_000,
        expected_credits_per_year=1_000,
        duration_years=10,
        discount_rate=0.0,
    )
    assert price == pytest.approx(20.0)


def test_breakeven_price_makes_npv_zero() -> None:
    price = breakeven_credit_price(
        capex_usd=500_000,
        opex_annual_usd=50_000,
        expected_credits_per_year=20_000,
        duration_years=10,
        discount_rate=0.08,
    )
    assert price is not None
    series = build_cashflow_series(
        capex_usd=500_000,
        opex_annual_usd=50_000,
        expected_credits_per_year=20_000,
        price_per_credit_usd=price,
        duration_years=10,
    )
    assert npv(series, discount_rate=0.08) == pytest.approx(0.0, abs=1e-2)


def test_breakeven_price_zero_credits_returns_none() -> None:
    assert (
        breakeven_credit_price(
            capex_usd=100_000,
            opex_annual_usd=10_000,
            expected_credits_per_year=0,
            duration_years=10,
        )
        is None
    )


# ── evaluate_project ─────────────────────────────────────────────────────────


def test_evaluate_project_returns_dataclass() -> None:
    result = evaluate_project(
        project_id="NBS-C01",
        capex_usd=500_000,
        opex_annual_usd=50_000,
        expected_credits_per_year=20_000,
        price_per_credit_usd=12.0,
        duration_years=10,
        discount_rate=0.08,
    )
    assert isinstance(result, CashflowMetrics)
    assert result.project_id == "NBS-C01"
    assert result.npv_usd > 0
    assert result.irr is not None and result.irr > 0.08
    assert result.discounted_payback_years == 4
    assert result.total_revenue_usd == 2_400_000.0
    assert result.total_cost_usd == 1_000_000.0


def test_evaluate_project_negative_npv_for_unprofitable() -> None:
    result = evaluate_project(
        project_id="BAD",
        capex_usd=1_000_000,
        opex_annual_usd=200_000,
        expected_credits_per_year=5_000,
        price_per_credit_usd=2.0,  # too cheap
        duration_years=5,
        discount_rate=DEFAULT_DISCOUNT_RATE,
    )
    assert result.npv_usd < 0
    assert result.discounted_payback_years is None


# ── evaluate_portfolio ───────────────────────────────────────────────────────


def test_evaluate_portfolio_happy_path(carbon_portfolio_df: pd.DataFrame) -> None:
    out = evaluate_portfolio(carbon_portfolio_df, discount_rate=0.08)
    assert list(out.columns) == [
        "project_id",
        "npv_usd",
        "irr",
        "discounted_payback_years",
        "breakeven_price_usd",
        "total_revenue_usd",
        "total_cost_usd",
    ]
    assert len(out) == 3
    # Sorted by descending NPV
    assert (out["npv_usd"].diff().dropna() <= 0).all()


def test_evaluate_portfolio_does_not_mutate_input(
    carbon_portfolio_df: pd.DataFrame,
) -> None:
    snapshot = carbon_portfolio_df.copy(deep=True)
    evaluate_portfolio(carbon_portfolio_df, discount_rate=0.08)
    pd.testing.assert_frame_equal(carbon_portfolio_df, snapshot)


def test_evaluate_portfolio_empty_raises() -> None:
    empty = pd.DataFrame(
        columns=[
            "project_id",
            "capex_usd",
            "opex_annual_usd",
            "expected_credits_per_year",
            "price_per_credit_usd",
            "project_duration_years",
        ]
    )
    with pytest.raises(ValueError, match="empty portfolio"):
        evaluate_portfolio(empty)


def test_evaluate_portfolio_missing_columns_raises() -> None:
    bad = pd.DataFrame({"project_id": ["X"], "capex_usd": [1.0]})
    with pytest.raises(ValueError, match="missing required columns"):
        evaluate_portfolio(bad)


def test_evaluate_portfolio_rejects_non_dataframe() -> None:
    with pytest.raises(TypeError, match="Expected pd.DataFrame"):
        evaluate_portfolio([1, 2, 3])  # type: ignore[arg-type]


def test_evaluate_portfolio_zero_discount_rate(
    carbon_portfolio_df: pd.DataFrame,
) -> None:
    out = evaluate_portfolio(carbon_portfolio_df, discount_rate=0.0)
    # At r=0 NPV equals total revenue minus total cost
    expected_npv = (
        carbon_portfolio_df["expected_credits_per_year"]
        * carbon_portfolio_df["price_per_credit_usd"]
        * carbon_portfolio_df["project_duration_years"]
    ) - (
        carbon_portfolio_df["capex_usd"]
        + carbon_portfolio_df["opex_annual_usd"]
        * carbon_portfolio_df["project_duration_years"]
    )
    assert sorted(out["npv_usd"].tolist()) == sorted(
        round(v, 2) for v in expected_npv.tolist()
    )
