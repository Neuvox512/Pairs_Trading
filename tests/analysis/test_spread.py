import pytest
from src.analysis.spread import fit_spread_parameters, calculate_pair_spread_z_score, calculate_pair_spread


def test_calculate_pairs_spread_z_score(sim_close_prices) -> None:
    first_symbol = "first_i1"
    second_symbol = "second_i1"

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices.iloc[:-10], first_symbol, second_symbol)
    global_spread = calculate_pair_spread(sim_close_prices.iloc[:-10], first_symbol, second_symbol, intercept, hedge_ratio)

    local_spread = calculate_pair_spread(sim_close_prices.iloc[-10:], first_symbol, second_symbol, intercept, hedge_ratio)

    z_score = calculate_pair_spread_z_score(local_spread, global_spread)

    assert z_score.values == pytest.approx(
        [0.44357725, -0.06978711, 0.86295494, -0.22807929, 0.32078286, 1.72974753,
         0.02754428, 0.28707326, 1.57592413, 0.03487642], abs=0.005
    )


def test_calculate_pairs_spread(sim_close_prices) -> None:
    first_symbol = "first_i1"
    second_symbol = "second_i1"

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices, first_symbol, second_symbol)

    spread = calculate_pair_spread(sim_close_prices, first_symbol, second_symbol, intercept, hedge_ratio)

    assert spread.mean() == pytest.approx(0, abs=0.005)


def test_fit_spread_parameters(sim_close_prices) -> None:
    first_symbol = "first_i1"
    second_symbol = "second_i1"

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices, first_symbol, second_symbol)

    assert intercept == pytest.approx(-25, abs=0.2)
    assert hedge_ratio == pytest.approx(0.5, abs=0.02)