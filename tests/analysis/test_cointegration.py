import pandas as pd
import numpy as np
from src.analysis.cointegration import (integration_p_values,
                                        cointegration_p_value,
                                        select_i1_symbols,
                                        calculate_pair_p_values,
                                        bh_correction)


def test_integration_p_values() -> None:
    random_gen = np.random.RandomState(0)
    time_index = pd.date_range(start='2026-08-02', periods=250, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(),
                                       index=time_index)
    first_symbol_p_values = integration_p_values(first_symbol_cl_prices)

    second_symbol_cl_prices = pd.Series(50 + 2 * first_symbol_cl_prices + random_gen.normal(size=250, scale=0.5),
                                        index=time_index)
    second_symbol_p_values = integration_p_values(second_symbol_cl_prices)

    assert first_symbol_p_values[0] > 0.05
    assert first_symbol_p_values[1] < 0.05
    assert second_symbol_p_values[0] > 0.05
    assert second_symbol_p_values[1] < 0.05


def test_select_i1_symbols() -> None:
    random_gen = np.random.RandomState(0)
    time_index = pd.date_range(start='2026-08-02', periods=250, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(),
                                       index=time_index)

    second_symbol_cl_prices = pd.Series(50 + 2 * first_symbol_cl_prices + random_gen.normal(size=250, scale=0.5),
                                        index=time_index)

    stationary_cl_prices = pd.Series(100 + random_gen.normal(size=250), index=time_index)

    all_close_prices = pd.DataFrame(
        {
            "first_prices": first_symbol_cl_prices,
            "second_prices": second_symbol_cl_prices,
            "stationary_prices": stationary_cl_prices,
        }
    )

    selected_symbols = select_i1_symbols(all_close_prices)

    assert set(selected_symbols) == {"first_prices", "second_prices"}


def test_cointegration_p_value() -> None:
    random_gen = np.random.RandomState(0)
    time_index = pd.date_range(start='2026-08-02', periods=250, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(),
                                       index=time_index)

    second_symbol_cl_prices = pd.Series(50 + 2*first_symbol_cl_prices + random_gen.normal(size=250, scale=0.5),
                                        index=time_index)

    p_value = cointegration_p_value(first_symbol_cl_prices, second_symbol_cl_prices)

    print('p_value is ',p_value)
    assert p_value < 0.05


def test_calculate_pair_p_values() -> None:
    random_gen = np.random.RandomState(0)
    time_index = pd.date_range( start="2026-08-02", periods=250, freq="1min", tz="UTC")

    first_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(), index=time_index)

    second_prices = pd.Series(50 + 2 * first_prices + random_gen.normal(size=250, scale=0.5), index=time_index)

    third_prices = pd.Series(200 + random_gen.normal(size=250).cumsum(), index=time_index)

    close_prices = pd.DataFrame(
        {
            "symbol_1": first_prices,
            "symbol_2": second_prices,
            "symbol_3": third_prices,
        }
    )

    pair_results = calculate_pair_p_values(close_prices=close_prices, symbols=["symbol_1", "symbol_2", "symbol_3"])

    actual_pairs = list(pair_results[["first_symbol", "second_symbol"]].itertuples(index=False, name=None))

    assert actual_pairs == [
        ("symbol_1", "symbol_2"),
        ("symbol_1", "symbol_3"),
        ("symbol_2", "symbol_3"),
    ]

    assert pair_results["coint_p_value"].between(0, 1).all()

    first_second_p_value = pair_results.iloc[0]["coint_p_value"]

    assert first_second_p_value < 0.05


def test_bh_correction() -> None:
    close_prices = pd.DataFrame(
        {
            "symbol_1": ['BAC', 'JPM', 'C'],
            "symbol_2": ['AAPL', 'MSFT', 'GS'],
            "coint_p_value": [0.01, 0.45, 0.07],
        }
    )
    adjusted_results = bh_correction(close_prices)

    assert adjusted_results["reject_no_coint"].tolist() == [True, False, False]