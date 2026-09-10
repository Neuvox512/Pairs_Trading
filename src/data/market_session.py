from datetime import date
import pandas as pd
import pandas_market_calendars as mcal
from src.data.timeframes import TIME_FREQUENCIES
from src.config import STOCK_MARKET_CALENDAR
from src.data.sqlite_db import  SQLiteDB

MARKET_CALENDAR = mcal.get_calendar(STOCK_MARKET_CALENDAR)


def get_session_prices(db : SQLiteDB, symbols : list[str], timeframe : str,session_date : date):
    session_range = get_session_bar_range(session_date, timeframe)

    if session_range is None:
        return pd.DataFrame()

    close_prices = db.load_close_prices(symbols, timeframe, session_range[0], session_range[1])
    close_prices = close_prices.ffill()

    return close_prices


def get_trading_dates(start_date : date, end_date : date) -> list[date]:
    schedule = MARKET_CALENDAR.schedule(start_date=start_date, end_date=end_date)

    trading_dates = []
    for session_date in schedule.index:
        trading_dates.append(session_date.date())

    return trading_dates


def get_session_bar_range(session_date: date, timeframe: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    schedule = MARKET_CALENDAR.schedule(start_date=session_date, end_date=session_date, tz='UTC')

    if schedule.empty:
        return None

    market_open = schedule.iloc[0]["market_open"]
    market_close = schedule.iloc[0]["market_close"]

    last_bar_time = market_close - pd.Timedelta(
        TIME_FREQUENCIES[timeframe]
    )

    return market_open, last_bar_time

