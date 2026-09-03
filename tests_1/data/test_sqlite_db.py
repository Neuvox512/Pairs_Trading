from src.data.sqlite_db import sqliteDB

def test_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "test_db.db"
    db = sqliteDB(db_path)
    db.create_table()

    with db.connect() as conn:
        table = conn.execute(
            """SELECT name
             FROM sqlite_master
             WHERE type='table'
             AND name='bars'"""
        ).fetchone()

    assert table is not None
