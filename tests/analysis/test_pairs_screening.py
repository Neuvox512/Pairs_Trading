from src.analysis.pairs_selection import historical_screening, select_stable_pairs, historical_screening_summary
from src.data.sqlite_db import SQLiteDB
from datetime import date


def test_select_stable_pairs(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1", "indep_i1", "stationary"]

    historical_data = historical_screening(
        sim_db,
        symbols,
        'M1',
        date(2026, 8, 3),
        date(2026, 8, 4)
    )
    historical_data_summary = historical_screening_summary(historical_data)
    stable_pairs = select_stable_pairs(historical_data_summary, 2, 1)

    assert len(stable_pairs) == 1
    assert stable_pairs.iloc[0]["first_symbol"] == "first_i1"
    assert stable_pairs.iloc[0]["second_symbol"] == "second_i1"

def test_historical_screening_summary(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1"]
    historical_results = historical_screening(
        sim_db,
        symbols,
        "M1",
        date(2026, 8, 3),
        date(2026, 8, 4),
    )

    pairs_summary = historical_screening_summary(historical_results)

    assert len(pairs_summary) == 1
    assert pairs_summary['persistence'].iloc[0] == 1.0



def test_historical_screening(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1"]

    historical_sessions = historical_screening(
        sim_db,
        symbols,
        'M1',
        date(2026, 8, 3),
        date(2026, 8, 4)
    )

    assert len(historical_sessions) == 2
    assert historical_sessions['reject_no_coint'].to_list() == [True, True]

