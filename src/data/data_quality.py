from datetime import date
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
from src.data.market_session import get_session_bar_range, get_trading_dates


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

    daily_quality_results = []
    trading_dates = get_trading_dates(date(2026, 8, 1), date(2026, 8, 31))

    for session_date in trading_dates:
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

        quality["session_date"] = session_date
        quality['expected_bars_count'] = expected_bars_count
        quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
        quality = quality.sort_values(by = 'coverage_pct', ascending = False)

        daily_quality_results.append(quality)

    daily_quality = pd.concat(daily_quality_results, ignore_index = True)

    print("Trading dates:", len(trading_dates))
    print("Daily result rows:", len(daily_quality))

if __name__ == '__main__':
    main(timeframe = 'M1')