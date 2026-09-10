from src.data.market_session import *
from src.analysis.cointegration import (integration_p_values,
                                        cointegration_p_value,
                                        select_i1_symbols,
                                        calculate_pair_p_values,
                                        bh_correction)


def test_integration_p_values(sim_close_prices) -> None:
    first_symbol_p_values = integration_p_values(sim_close_prices['first_i1'])

    second_symbol_p_values = integration_p_values(sim_close_prices['second_i1'])

    assert first_symbol_p_values[0] > 0.05
    assert first_symbol_p_values[1] < 0.05
    assert second_symbol_p_values[0] > 0.05
    assert second_symbol_p_values[1] < 0.05


def test_select_i1_symbols(sim_close_prices) -> None:
    all_close_prices = pd.DataFrame(
        {
            "first_symbol": sim_close_prices['first_i1'],
            "second_symbol": sim_close_prices['second_i1'],
            "stationary_symbol": sim_close_prices['stationary'],
        }
    )

    selected_symbols = select_i1_symbols(all_close_prices)

    assert set(selected_symbols) == {"first_symbol", "second_symbol"}


def test_cointegration_p_value(sim_close_prices) -> None:
    p_value = cointegration_p_value(sim_close_prices['first_i1'], sim_close_prices['second_i1'])

    assert p_value < 0.05


def test_calculate_pair_p_values(sim_close_prices) -> None:
    pair_results = calculate_pair_p_values(close_prices=sim_close_prices, symbols=["first_i1", "second_i1", "indep_i1"])

    actual_pairs = list(pair_results[["first_symbol", "second_symbol"]].itertuples(index=False, name=None))

    assert actual_pairs == [
        ("first_i1", "second_i1"),
        ("first_i1", "indep_i1"),
        ("second_i1", "indep_i1"),
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
