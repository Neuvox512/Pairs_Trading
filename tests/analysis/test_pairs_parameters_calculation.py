import pytest
import pandas as pd
import numpy as np
from src.analysis.pairs_parameters_calculation import (
    fit_spread_parameters,
    calculate_pair_spread_z_score,
    calculate_pair_spread,
    calculate_spread_half_life,
    calculate_pairs_parameters)


def test_calculate_pair_parameters(sim_close_prices) -> None:
    candidate_pairs = pd.DataFrame([{'first_symbol': 'first_i1', 'second_symbol': 'second_i1'}])
    timeframe = "M1"
    params = calculate_pairs_parameters(sim_close_prices, candidate_pairs, timeframe)

    intercept, hedge_ratio = fit_spread_parameters(
        sim_close_prices,
        candidate_pairs['first_symbol'].iloc[0],
        candidate_pairs['second_symbol'].iloc[0]
    )
    spread = calculate_pair_spread(
        sim_close_prices,
        candidate_pairs['first_symbol'].iloc[0],
        candidate_pairs['second_symbol'].iloc[0],
        intercept, hedge_ratio
    )
    half_life = calculate_spread_half_life(spread, timeframe)

    assert params['first_symbol'].iloc[0] == 'first_i1'
    assert params['second_symbol'].iloc[0] == 'second_i1'
    assert params['intercept'].iloc[0]  == pytest.approx(intercept, abs=0.005)
    assert params['hedge_ratio'].iloc[0]  == pytest.approx(hedge_ratio, abs=0.005)
    assert params ['spread_mean'].iloc[0] == pytest.approx(spread.mean(), abs=0.005)
    assert params['spread_std'].iloc[0] == pytest.approx(spread.std(), abs=0.005)
    assert params['half_life_(minutes)'].iloc[0] == pytest.approx(half_life, abs=0.005)


def test_calculate_spread_half_life() -> None:
    theta = 0.5
    mean_spread = 5.0
    spread_values = [10.0]
    times = [pd.Timestamp('2026-09-03 19:00:00')]

    for i in range(100):
        if i == 50:
            current_spread = 100000000
            spread_values.append(current_spread)
        else:
            prev_spread = spread_values[-1]
            current_spread = -theta * (prev_spread - mean_spread) + prev_spread
            spread_values.append(current_spread)

        if i < 50:
            time = pd.Timestamp('2026-09-03 19:01:00') + pd.Timedelta(minutes=i)
            times.append(time)
        else:
            time = pd.Timestamp('2026-09-04 13:00:00') + pd.Timedelta(minutes=i)
            times.append(time)

    spread = pd.Series(spread_values, index = times)
    half_life = calculate_spread_half_life(spread, 'M1')
    expected_half_life = np.log(2)/theta

    assert half_life == pytest.approx(expected_half_life, abs=0.005)


def test_calculate_pair_spread_z_score(sim_close_prices) -> None:
    first_symbol = "first_i1"
    second_symbol = "second_i1"

    intercept, hedge_ratio = fit_spread_parameters(sim_close_prices.iloc[:-10], first_symbol, second_symbol)
    global_spread = calculate_pair_spread(sim_close_prices.iloc[:-10], first_symbol, second_symbol, intercept, hedge_ratio)
    global_mean = global_spread.mean()
    global_std = global_spread.std()

    local_spread = calculate_pair_spread(sim_close_prices.iloc[-10:], first_symbol, second_symbol, intercept, hedge_ratio)

    z_score = calculate_pair_spread_z_score(local_spread, global_mean, global_std)

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