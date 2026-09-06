from datetime import timedelta
from src.data.acquisition.data_updater import update_symbol
from src.data.acquisition.mt5_terminal import MT5Terminal
from src.data.sqlite_db import SQLiteDB


def test_update_data(tmp_path) -> None:
    db = SQLiteDB(tmp_path / "test_db.db")
    db.create_table()
    terminal = MT5Terminal()
    terminal.connect()

    latest_bar_time_from_mt5 = terminal.get_latest_closed_bar_time(symbol="JPM", timeframe="M1")

    assert latest_bar_time_from_mt5 is not None

    start_time = latest_bar_time_from_mt5 - timedelta(minutes=2)

    updated_count = update_symbol(
        terminal=terminal,
        database=db,
        symbol="JPM",
        timeframe="M1",
        start_time=start_time)

    latest_bar_time_from_db = db.get_latest_bar_time(symbol="JPM", timeframe="M1")

    assert updated_count > 0
    assert latest_bar_time_from_db == latest_bar_time_from_mt5