from src.data.sqlite_db import SQLiteDB
import pandas as pd

def test_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "test_db.db"
    db = SQLiteDB(db_path)
    db.create_table()

    with db.connect() as conn:
        table = conn.execute(
            """SELECT name
             FROM sqlite_master
             WHERE type='table'
             AND name='bars'"""
        ).fetchone()

    assert table is not None

def test_save_bars(tmp_path, sim_bars) -> None:
    db_path = tmp_path / "test_db.db"
    db = SQLiteDB(db_path)
    db.create_table()

    db.save_bars('JPM', 'M1', sim_bars)
    db.save_bars('JPM', 'M1', sim_bars)

    with db.connect() as conn:
        row_count = conn.execute('SELECT count(*) FROM bars').fetchone()[0]

    assert row_count == 2

def test_save_symbols(tmp_path) -> None:
    db = SQLiteDB(tmp_path / "test_db.db")
    db.create_symbols_table()

    instruments = pd.DataFrame(
        {
        "symbol": ["AAPL.US", "MSFT.US"],
        "point": [0.01, 0.01],
        "contract_size": [1.0, 1.0],
        "volume_min": [1.0, 1.0],
        "volume_max": [1000.0, 1000.0],
        "volume_step": [1.0, 1.0],
        }
    )

    db.save_symbols(instruments)

    with db.connect() as conn:
        rows = conn.execute("SELECT symbol, point FROM symbols ORDER BY symbol").fetchall()

    assert rows == [("AAPL.US", 0.01), ("MSFT.US", 0.01)]

def test_load_bars(tmp_path, sim_bars) -> None:
    db_path = tmp_path / "test_db.db"
    db = SQLiteDB(db_path)
    db.create_table()

    start_time = sim_bars['time_utc'].iloc[-2]
    end_time = sim_bars['time_utc'].iloc[-1]

    db.save_bars('JPM', 'M1', sim_bars)
    loaded_bars = db.load_bars('JPM', 'M1', start_time=start_time, end_time=end_time)

    assert len(loaded_bars) == 2
    assert (loaded_bars['time_utc'] == sim_bars['time_utc']).all()


def test_get_last_bar(tmp_path, sim_bars) -> None:
    db_path = tmp_path / "test_db.db"
    db = SQLiteDB(db_path)
    db.create_table()
    db.save_bars('JPM', 'M1', sim_bars)

    latest_bar = db.get_latest_bar_time('JPM', 'M1')

    assert latest_bar is not None
    assert latest_bar == sim_bars['time_utc'].iloc[-1]


def test_load_close_prices(tmp_path, sim_bars) -> None:
    database = SQLiteDB(tmp_path / "test_db.db")
    database.create_table()
    database.save_bars("JPM", "M1", sim_bars)

    start_time = sim_bars["time_utc"].iloc[-2]
    end_time = sim_bars["time_utc"].iloc[-1]

    close_prices = database.load_close_prices(
        symbols=["JPM"],
        timeframe="M1",
        start_time=start_time,
        end_time=end_time,
    )

    assert len(close_prices) == 2
    assert list(close_prices.columns) == ["JPM"]


def test_load_quality_data(tmp_path, sim_bars) -> None:
    database = SQLiteDB(tmp_path / "test_db.db")
    database.create_table()
    database.save_bars("JPM", "M1", sim_bars)

    start_time = sim_bars["time_utc"].iloc[-2]
    end_time = sim_bars["time_utc"].iloc[-1]

    quality_data = database.load_quality_data(
        symbols=["JPM"],
        timeframe="M1",
        start_time=start_time,
        end_time=end_time,
    )

    assert list(quality_data.columns) == ['symbol', 'time_utc', 'close', 'spread', 'tick_volume']