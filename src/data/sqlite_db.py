import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime


class SQLiteDB:
    def __init__(self, db_path : Path) -> None:
        self.db_path = Path(db_path)


    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


    def create_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS bars 
        (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            time_utc INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            tick_volume INTEGER NOT NULL,
            spread INTEGER NOT NULL,
            real_volume INTEGER NOT NULL,
            PRIMARY KEY (symbol, timeframe, time_utc)
        )
        """

        with self.connect() as conn:
            conn.execute(query)


    def save_bars(self, symbol : str, timeframe : str, bars : pd.DataFrame) -> int:
        bars_to_save = bars.copy()
        bars_to_save['symbol'] = symbol
        bars_to_save['timeframe'] = timeframe
        unix_start = pd.Timestamp('1970-01-01', tz = 'UTC')
        bars_to_save['time_utc'] = ((bars_to_save['time_utc'] - unix_start).dt.total_seconds()).astype('int64')

        columns = [
            "symbol",
            "timeframe",
            "time_utc",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread",
            "real_volume"
        ]

        rows = bars_to_save[columns].itertuples(index = False, name = None)

        query = """INSERT INTO bars (
            symbol,
            timeframe,
            time_utc,
            open,
            high,
            low,
            close,
            tick_volume,
            spread,
            real_volume
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, timeframe, time_utc)
        DO UPDATE SET 
            symbol = excluded.symbol,
            timeframe = excluded.timeframe,
            time_utc = excluded.time_utc,
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            tick_volume = excluded.tick_volume,
            spread = excluded.spread,
            real_volume = excluded.real_volume"""

        with self.connect() as conn:
            conn.executemany(query, rows)

        return len(bars_to_save)


    def load_bars(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        start_time = int(start_time.timestamp())
        end_time = int(end_time.timestamp())

        query = """
        SELECT 
            symbol,
            timeframe,
            time_utc,
            open,
            high,
            low,
            close,
            tick_volume,
            spread,
            real_volume
        FROM bars 
        WHERE symbol = ? 
            AND timeframe = ?
            AND time_utc BETWEEN ? AND ?
        ORDER BY time_utc
        """

        with self.connect() as conn:
            bars = pd.read_sql_query(query,conn, params = (symbol, timeframe, start_time, end_time))

        bars['time_utc'] = pd.to_datetime(bars['time_utc'], unit = 's', utc = True)

        return bars
        

    def get_latest_bar_time(self, symbol : str, timeframe : str) -> pd.Timestamp | None:
        query = """SELECT MAX(time_utc) FROM bars WHERE symbol = ? AND timeframe = ?"""

        with self.connect() as conn:
            latest_bar = conn.execute(query, (symbol, timeframe)).fetchone()[0]

        if latest_bar is None:
            return None

        return pd.to_datetime(latest_bar, unit = 's', utc = True)