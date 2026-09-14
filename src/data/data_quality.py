from datetime import datetime
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
from src.data.market_session import *


def main(timeframe : str) -> None:
    db = SQLiteDB(Path(SQLITE_DB_PATH))

    with db.connect() as conn:
        rows = conn.execute("""
        SELECT DISTINCT symbol
        FROM bars
        WHERE timeframe = ?
        ORDER BY symbol
        """,
        (timeframe,),).fetchall()

    symbols = []
    for row in rows:
        symbols.append(row[0])

    session_date = date(2026, 8, 4)
    session_bar_range = get_session_bar_range(session_date, timeframe)

    if session_bar_range is None:
        print("No session in this date")
        return None

    start_time, end_time = session_bar_range
    close_prices = db.load_close_prices(symbols, timeframe, start_time, end_time)
    expected_bars_count = len(close_prices)
    actual_bars_count = close_prices.notna().sum()

    quality = pd.DataFrame(
        {
        'symbols': actual_bars_count.index,
        'actual_bars_count': actual_bars_count.values,
        }
    )
    quality['expected_bars_count'] = expected_bars_count
    quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
    quality = quality.sort_values(by = 'coverage_pct', ascending = False)

    print(f'Number of symbols: {len(symbols)}')
    print(f'expected bars count: {expected_bars_count}')
    print(f'Worst symbols: {quality.tail(20).to_string(index = False)}')

if __name__ == '__main__':
    main(timeframe = 'M1')