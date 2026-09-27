import pytest
import pandas as pd
import numpy as np
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_session_prices, get_trading_dates
from datetime import date


@pytest.fixture
def sim_db(tmp_path) -> SQLiteDB:
    db = SQLiteDB(tmp_path/'test_db.db')
    db.create_table()

    session_dates = ["2026-08-03 13:30:00", "2026-08-04 13:30:00"]
    random_gen = np.random.RandomState(0)

    for session_date in session_dates:
        time_index = pd.date_range(start=session_date, periods=390, freq="1min", tz="UTC")

        first_i1 = pd.Series(100 + random_gen.normal(size=390).cumsum(), index=time_index)

        second_i1 = pd.Series(50 + 2 * first_i1 + random_gen.normal(size=390, scale=0.1), index=time_index)

        independent_i1 = pd.Series(200 + random_gen.normal(size=390).cumsum(), index=time_index)

        stationary = pd.Series(100 + random_gen.normal(size=390), index=time_index)

        for sim_symbol, sim_close_prices in {
                "first_i1": first_i1,
                "second_i1": second_i1,
                "indep_i1": independent_i1,
                "stationary": stationary,
            }.items():

            sim_bars = pd.DataFrame(
                {
                    "time_utc": time_index,
                    "open": sim_close_prices,
                    "high": sim_close_prices,
                    "low": sim_close_prices,
                    "close": sim_close_prices,
                    "tick_volume": np.ones(390, dtype=int),
                    "spread": np.zeros(390, dtype=int),
                    "real_volume": np.zeros(390, dtype=int),
                }
            )

            db.save_bars(sim_symbol, 'M1', sim_bars)

    return db
    
    
@pytest.fixture
def sim_close_prices(sim_db : SQLiteDB) -> pd.DataFrame:
    symbols = ['first_i1', 'second_i1', 'indep_i1', 'stationary']
    sim_close_prices = get_session_prices(sim_db, symbols, 'M1', date(2026, 8, 3))

    return sim_close_prices


@pytest.fixture
def sim_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_utc": pd.to_datetime(
                [
                    "2026-08-03 13:30:00",
                    "2026-08-03 13:31:00",
                ],
                utc=True,
            ),
            "open": [319.28, 321.24],
            "high": [321.41, 321.79],
            "low": [319.28, 320.12],
            "close": [321.41, 320.12],
            "tick_volume": [30, 38],
            "spread": [22, 22],
            "real_volume": [0, 0],
        }
    )