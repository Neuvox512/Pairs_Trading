from datetime import date
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_session_bar_range, get_trading_dates
from src.data.timeframes import TIME_FREQUENCIES


def historical_symbols_sreening(db : SQLiteDB, timeframe : str, start_date : date, end_date : date) -> None | pd.DataFrame:
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
    trading_dates = get_trading_dates(start_date, end_date)

    for session_date in trading_dates:
        session_bar_range = get_session_bar_range(session_date, timeframe)
        if session_bar_range is None:
            print("No session in this date")
            return None

        start_time, end_time = session_bar_range
        bars = db.load_quality_data(symbols, timeframe, start_time, end_time)
        expected_bars_count = len(pd.date_range(start=start_time, end=end_time, freq=TIME_FREQUENCIES[timeframe]))

        quality = (
            bars.groupby('symbol')
            .agg(actual_bars_count = ('time_utc', 'count'),
                 median_close = ('close', 'median'),
                 median_spread = ('spread', 'median')
                 )
            .reset_index()
        )

        quality["session_date"] = session_date
        quality['expected_bars_count'] = expected_bars_count
        quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
        daily_quality_results.append(quality)

    daily_quality = pd.concat(daily_quality_results, ignore_index = True)

    return daily_quality
