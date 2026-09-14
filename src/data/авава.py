from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH

db = SQLiteDB(SQLITE_DB_PATH)

with db.connect() as conn:
    result = conn.execute(
        """
        SELECT
            symbol,
            datetime(MIN(time_utc), 'unixepoch'),
            datetime(MAX(time_utc), 'unixepoch'),
            COUNT(*)
        FROM bars
        WHERE symbol = ?
          AND timeframe = ?
        """,
        ("JPM.US", "M1"),
    ).fetchone()

print(result)