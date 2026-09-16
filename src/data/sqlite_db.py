import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime
from src.data.timeframes import TIME_FREQUENCIES

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

    def create_symbols_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS symbols(
            symbol TEXT PRIMARY KEY,
            point REAL NOT NULL
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

    def save_symbols(self, symbols : pd.DataFrame) -> None:
        query = """
        INSERT INTO symbols (symbol, point)
        VALUES (?, ?)
        ON CONFLICT (symbol)
        DO UPDATE SET point = excluded.point
        """
        params = symbols[['symbol', 'point']].itertuples(index = False, name = None)

        with self.connect() as conn:
            conn.executemany(query, params)

    def load_bars(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())

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
            bars = pd.read_sql_query(query, conn, params = (symbol, timeframe, start_timestamp, end_timestamp))

        bars['time_utc'] = pd.to_datetime(bars['time_utc'], unit = 's', utc = True)

        return bars

    def get_latest_bar_time(self, symbol : str, timeframe : str) -> datetime | None:
        query = """SELECT MAX(time_utc) FROM bars WHERE symbol = ? AND timeframe = ?"""

        with self.connect() as conn:
            latest_bar = conn.execute(query, (symbol, timeframe)).fetchone()[0]

        if latest_bar is None:
            return None

        return pd.to_datetime(latest_bar, unit = 's', utc = True)

    def load_quality_data(self, symbols: list[str], timeframe: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        placeholders = ', '.join(['?'] * len(symbols))

        query = f"""
        SELECT symbol, time_utc, close, spread, tick_volume
        FROM bars
        WHERE symbol in ({placeholders}) AND timeframe = ? AND time_utc BETWEEN ? AND ?
        """
        params = (*symbols, timeframe, start_timestamp, end_timestamp)

        with self.connect() as conn:
            bars = pd.read_sql_query(query, conn, params = params)

        bars['time_utc'] = pd.to_datetime(bars['time_utc'], unit = 's', utc = True)

        return bars

    def load_close_prices(self, symbols : list[str],timeframe : str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        placeholders = ', '.join(['?'] * len(symbols))
        query = f"""
        SELECT 
            symbol, 
            time_utc, 
            close 
        FROM bars 
        WHERE symbol IN ({placeholders}) AND timeframe = ? AND time_utc BETWEEN ? AND ?
        ORDER BY time_utc
        """
        params = (*symbols, timeframe, start_timestamp, end_timestamp)

        with self.connect() as conn:
            bars = pd.read_sql_query(query, conn, params = params)

        bars['time_utc'] = pd.to_datetime(bars['time_utc'], unit = 's', utc = True)
        close_prices = bars.pivot(columns ='symbol', index ='time_utc', values ='close')

        expected_times = pd.date_range(start_time, end_time, freq = TIME_FREQUENCIES[timeframe])
        close_prices = close_prices.reindex(expected_times)
        close_prices.index.name = 'time_utc'

        return close_prices
