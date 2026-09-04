from src.data.sqlite_db import SQLiteDB
from src.data.mt5_terminal import MT5Terminal
from datetime import datetime, timezone
from src.data.data_updater import update_data
import pandas as pd


def test_update_data(tmp_path, sim_bars):
    db_path = tmp_path / "test_db.db"
    db = SQLiteDB(db_path)
    db.create_table()
    start_time = datetime(2026, 2, 9, 16, 30, tzinfo=timezone.utc)
    end_time = datetime(2026, 2, 9, 16, 31, tzinfo=timezone.utc)
    terminal = MT5Terminal()
    terminal.connect()

    raw_count = update_data(terminal, db, symbol="JPM", timeframe="M1", start_time=start_time, end_time=end_time)
    latest_bar_from_db = db.get_latest_bar(symbol="JPM", timeframe="M1")

    bars_from_mt5 = terminal.fetch_bars(symbol="JPM", timeframe="M1", start_time=start_time, end_time=end_time)
    latest_bar_from_mt5 = pd.to_datetime(bars_from_mt5['time_utc'].iloc[-1])

    assert latest_bar_from_db is not None
    assert latest_bar_from_mt5 is not None
    assert latest_bar_from_db == latest_bar_from_mt5