from src.analysis.pairs_screening import screen_historical_sessions
from src.analysis.pairs_screening import screen_pairs
from src.data.sqlite_db import SQLiteDB
from datetime import date


def test_screen_cointegrated_pairs(sim_close_prices) -> None:
    close_prices = sim_close_prices[
        ["first_i1", "second_i1"]
    ]

    results = screen_pairs(close_prices)

    assert len(results) == 1
    assert results.iloc[0]["first_symbol"] == "first_i1"
    assert results.iloc[0]["second_symbol"] == "second_i1"
    assert bool(results.iloc[0]["reject_no_coint"])


def test_screen_historical_sessions(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1"]

    historical_sessions = screen_historical_sessions(
        sim_db,
        symbols,
        'M1',
        date(2026, 8, 3),
        date(2026, 8, 3))

    assert historical_sessions['reject_no_coint'] == True