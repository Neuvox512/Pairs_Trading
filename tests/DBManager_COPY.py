import sqlite3
import pandas as pd
from Data_Layer.Timeframes import Timeframe

class DBManager:
    def __init__(self, timeframe: str):
        self.timeframe = Timeframe(timeframe)
        self.db_path = "C:/Users/gorn9/PycharmProjects/Hedge_bot_(Pairs Trading)/tests/" + self.timeframe.db_name
        self.create_table()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS rates 
        (
            symbol TEXT NOT NULL,
            time TIMESTAMP,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            tick_volume INTEGER,
            PRIMARY KEY (symbol, time)
        );
        """

        with self.get_connection() as conn:
            conn.execute(query)
            conn.commit()

    def save_bars(self, symbol: str, df: pd.DataFrame):

        df_to_save = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].copy()
        df_to_save['symbol'] = symbol
        df_to_save['time'] = df_to_save['time'].astype(str)

        with (self.get_connection() as conn):
            cursor = conn.cursor()
            for i,row in df_to_save.iterrows():
                cursor.execute (
                    """ INSERT OR IGNORE INTO rates (symbol, time, open, high, low, close, tick_volume) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row['symbol'],
                     row['time'],
                     row['open'],
                     row['high'],
                     row['low'],
                     row['close'],
                     row['tick_volume'])
                )
            conn.commit()

    def get_bars(self, symbol: str, limit: int = None):

        query = "SELECT time as time, open, high, low, close, tick_volume FROM rates WHERE symbol = ?"
        params = [symbol]

        if limit:
            query += " ORDER BY time DESC LIMIT ?"
            params.append(limit)
        else:
            query += " ORDER BY time ASC"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['time'])

        if limit:
            df = df.iloc[::-1].reset_index(drop=True)
        return df
