from src.analysis.pairs_selection import historical_screening, select_candidate_pairs
from src.data.sqlite_db import SQLiteDB
from datetime import date


def test_select_candidate_pairs(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1", "stationary", "indep_i1"]
    fdr_level = 0.05

    historical_results = historical_screening(
        sim_db,
        symbols,
        "M1",
        date(2026, 8, 3),
        date(2026, 8, 4),
        fdr_level,
    )

    candidate_pairs = select_candidate_pairs(historical_results, 2)

    assert (list(candidate_pairs[['first_symbol', 'second_symbol']].itertuples(index = False, name = None))
            == [('first_i1', 'second_i1')])


def test_historical_pairs_screening(sim_db : SQLiteDB) -> None:
    symbols = ["first_i1", "second_i1"]
    fdr_level = 0.05

    historical_sessions = historical_screening(
        sim_db,
        symbols,
        'M1',
        date(2026, 8, 3),
        date(2026, 8, 4),
        fdr_level,
    )

    assert len(historical_sessions) == 2
    assert historical_sessions['reject_no_coint'].to_list() == [True, True]

