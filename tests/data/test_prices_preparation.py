import pandas as pd

from src.data.market_session import get_session_prices
from src.data.sqlite_db import SQLiteDB
from pathlib import Path
from datetime import datetime, date


def test_get_session_prices(tmp_path, sim_bars) -> None:
    db = SQLiteDB(Path(tmp_path/'test_db.db'))
    db.create_table()

    db.save_bars('JPM', 'M1', sim_bars)
    db.save_bars('GS', 'M1', sim_bars)

    session_prices = get_session_prices(db, ['JPM', 'GS'], 'M1', date(2026,8,3))
    print(session_prices)
    assert session_prices.shape == (390,2)
    assert session_prices.index[0] == pd.Timestamp('2026-08-03 13:30:00', tz = 'utc')
    assert session_prices.index[-1] == pd.Timestamp('2026-08-03 19:59:00', tz = 'utc')