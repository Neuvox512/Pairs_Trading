import pytest
from src.analysis.spread import fit_spread_parameters


def test_fit_spread_parameters(sim_close_prices) -> None:
    first_symbol = "first_i1"
    second_symbol = "second_i1"

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices, first_symbol, second_symbol)

    assert intercept == pytest.approx(-25, abs=0.2)
    assert hedge_ratio == pytest.approx(0.5, abs=0.02)