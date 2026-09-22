import pytest
from src.analysis.spread import fit_spread_parameters


def test_fit_spread_parameters(sim_close_prices) -> None:
    first_symbol = sim_close_prices.columns[0]
    second_symbol = sim_close_prices.columns[2]

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices, first_symbol, second_symbol)

    assert intercept == pytest.approx(-24.98786059)
    assert hedge_ratio == pytest.approx(0.49997483)