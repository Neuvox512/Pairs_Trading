from src.data.sqlite_db import SQLiteDB
import pandas as pd
import pytest


@pytest.fixture
def sim_bars():
    return pd.DataFrame(
        {
            "time_utc" : pd.to_datetime(["2026-02-09 16:30:00", "2026-02-09 16:31:00"], utc = True),
            "open" : [319.28, 321.24],
            "high" : [321.41, 321.79],
            "low" : [319.28, 320.12],
            "close" : [321.41, 320.12],
            "tick_volume" : [30, 38],
            "spread" : [22, 22],
            "real_volume" : [0, 0]
        }
    )

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

    db.save_bars('JPM', 'M1', sim_bars)
    loaded_bars = db.load_bars('JPM', 'M1')

    assert len(loaded_bars) == 2
    assert (loaded_bars['time_utc'] == sim_bars['time_utc']).all()


