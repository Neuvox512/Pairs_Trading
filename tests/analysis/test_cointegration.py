from src.data.market_session import *
from src.analysis.cointegration import (
    select_i1_symbols,
    cointegration_global_test,
    cointegration_local_test,
    bh_correction,
    screen_global_pairs,
    screen_local_pairs)


def test_screen_local_pairs(sim_close_prices) -> None:
    candidate_pairs = pd.DataFrame({
        "first_symbol": ['first_i1', 'stationary'],
        "second_symbol": ['second_i1', 'first_i1']
    })
    local_pairs = screen_local_pairs(sim_close_prices, candidate_pairs)

    assert (list(local_pairs[['first_symbol', 'second_symbol']].itertuples(index = False, name = None))
            == [('first_i1', 'second_i1')])

def test_screen_global_pairs(sim_close_prices) -> None:
    close_prices = sim_close_prices[
        ["first_i1", "second_i1"]
    ]

    results = screen_global_pairs(close_prices)

    assert len(results) == 1
    assert results.iloc[0]["first_symbol"] == "first_i1"
    assert results.iloc[0]["second_symbol"] == "second_i1"
    assert bool(results.iloc[0]["reject_no_coint"])


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


def test_cointegration_global_test(sim_close_prices) -> None:
    pair_results = cointegration_global_test(sim_close_prices, ["first_i1", "second_i1", "indep_i1"])

    assert pair_results["coint_p_value"].between(0, 1).all()

    first_second_p_value = pair_results.iloc[0]["coint_p_value"]

    assert first_second_p_value < 0.05


def test_cointegration_local_test(sim_close_prices) -> None:
    candidate_pairs = pd.DataFrame({
        "first_symbol": ['first_i1', 'indep_i1'],
        "second_symbol": ['second_i1', 'first_i1']
    })
    local_coint = cointegration_local_test(sim_close_prices, candidate_pairs)
    actual_pairs = list(candidate_pairs[['first_symbol', 'second_symbol']].itertuples(index=False, name = None))

    assert list(local_coint[['first_symbol', 'second_symbol']].itertuples(index=False, name = None)) == actual_pairs


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
