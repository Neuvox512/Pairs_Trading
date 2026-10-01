from datetime import date, timedelta
import pandas as pd
import pandas_market_calendars as mcal
from src.data.timeframes import TIME_FREQUENCIES
from src.config import STOCK_MARKET_CALENDAR
from src.data.sqlite_db import  SQLiteDB

MARKET_CALENDAR = mcal.get_calendar(STOCK_MARKET_CALENDAR)


def get_session_data(db : SQLiteDB, symbols : list[str], timeframe : str,session_date : date) -> pd.DataFrame:
    session_range = get_full_session_bar_range(session_date, timeframe)

    if session_range is None:
        return pd.DataFrame()

    market_data = db.load_market_data(symbols, timeframe, session_range[0], session_range[1])
    market_data = market_data.ffill()
    market_data = market_data.dropna()

    return market_data


def get_previous_trading_dates(session_date : date, sessions_count : int) -> list[date]:
    start_date = session_date - timedelta(days=max(sessions_count * 3, 7))

    trading_dates = get_trading_dates(start_date, session_date)

    previous_trading_dates = []
    for trading_date in trading_dates:
        if trading_date < session_date:
            previous_trading_dates.append(trading_date)

    return previous_trading_dates[-sessions_count:]


def get_trading_dates(start_date : date, end_date : date) -> list[date]:
    schedule = MARKET_CALENDAR.schedule(start_date=start_date, end_date=end_date)

    trading_dates = []
    for session_date in schedule.index:
        trading_dates.append(session_date.date())

    return trading_dates


def get_local_session_bar_range(
        session_date : date,
        timeframe : str,
        opening_minutes : int
) -> tuple[pd.Timestamp, pd.Timestamp]:

    market_open, market_close = get_full_session_bar_range(session_date, timeframe)
    local_end_range = market_open + pd.Timedelta(minutes=opening_minutes) - pd.Timedelta(TIME_FREQUENCIES[timeframe])

    return market_open, local_end_range


def get_full_session_bar_range(session_date: date, timeframe: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    schedule = MARKET_CALENDAR.schedule(start_date=session_date, end_date=session_date, tz='UTC')

    if schedule.empty:
        return None

    market_open = schedule.iloc[0]["market_open"]
    market_close = schedule.iloc[0]["market_close"]

    last_bar_time = market_close - pd.Timedelta(
        TIME_FREQUENCIES[timeframe]
    )

    return market_open, last_bar_time
