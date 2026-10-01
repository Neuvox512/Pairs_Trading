from datetime import date
import pandas as pd
from src.strategies.intraday_strategy.general_tools import (
    get_strat_dates,
    confirm_local_candidate_pairs,
    get_local_prices,
    get_pairs_parameters)


def test_get_pairs_parameters(sim_db) -> None:
    confirmed_pairs = pd.DataFrame(
        {
            'first_symbol': ['first_i1', 'indep_i1'],
            'second_symbol': ['second_i1', 'first_i1']
        }
    )
    timeframe = "M1"
    coint_dates = [date(2026, 8, 3),date(2026, 8, 4)]

    params = get_pairs_parameters(sim_db, confirmed_pairs, timeframe, coint_dates)

    assert len(params) == 2

def test_confirm_local_candidate_pairs(sim_db) -> None:
    candidate_pairs = pd.DataFrame(
        {
            'first_symbol': ['first_i1', 'indep_i1', 'stationary'],
            'second_symbol': ['second_i1', 'first_i1', 'second_i1']
        }
    )
    timeframe = "M1"
    session_date = date(2026, 8, 3)

    loc_candidate_pairs = confirm_local_candidate_pairs(sim_db, candidate_pairs, timeframe, session_date)

    assert len(loc_candidate_pairs) == 1
    assert loc_candidate_pairs.iloc[0]['first_symbol'] == 'first_i1'
    assert loc_candidate_pairs.iloc[0]['second_symbol'] == 'second_i1'


def test_get_local_prices(sim_db) -> None:
    session_date = date(2026, 8, 3)
    timeframe = "M1"
    symbols = ["first_i1", "second_i1", "indep_i1", "stationary"]

    local_prices = get_local_prices(sim_db, symbols, session_date, timeframe, 90)

    assert len(local_prices) == 90

def test_get_strat_dates() -> None:
    liquidity_dates, coint_dates = get_strat_dates(date(2026, 9, 11), 5, 2)

    # date(2026, 9, 7) is Labor day in USA, so NYSE was closed and not added to liquidity_dates
    assert liquidity_dates == [
        date(2026, 9, 1),
        date(2026, 9, 2),
        date(2026, 9, 3),
        date(2026, 9, 4),
        date(2026, 9, 8)]
    assert coint_dates == [date(2026, 9, 9), date(2026, 9, 10)]