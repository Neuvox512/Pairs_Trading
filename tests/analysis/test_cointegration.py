from src.data.market_session import *
from src.analysis.cointegration import (
    select_i1_symbols,
    cointegration,
    bh_correction)


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


def test_cointegration(sim_close_prices) -> None:
    pair_results = cointegration(sim_close_prices, ["first_i1", "second_i1", "indep_i1"])

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
