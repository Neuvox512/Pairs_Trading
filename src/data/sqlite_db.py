import sqlite3
from pathlib import Path

class sqliteDB:
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
            spread  NOT NULL,
            real_value REAL NOT NULL,
            PRIMARY KEY (symbol, timeframe, time_utc)
        )
        """

        with self.connect() as conn:
            conn.execute(query)
            
        
