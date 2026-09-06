from src.data.sqlite_db import SQLiteDB

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
    print(latest_bar)

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