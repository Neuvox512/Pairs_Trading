from datetime import date
import pandas as pd
import pandas_market_calendars as mcal
from src.data.timeframes import TIME_FREQUENCIES
from src.config import BROKER_TIMEZONE, STOCK_MARKET_CALENDAR

MARKET_CALENDAR = mcal.get_calendar(STOCK_MARKET_CALENDAR)


def get_trading_dates(start_date : date, end_date : date) -> list[str]:
    schedule = MARKET_CALENDAR.schedule(start_date=start_date, end_date=end_date)

    trading_dates = []
    for date in schedule.index:
        trading_dates.append(date.date())

    return trading_dates


def get_session_bar_range(session_date: date, timeframe: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    #Roboforex broker used here as example and therefore timezone is set to 'Europe/Bucharest'
    #Change 'tz' parameter according to your broker timezone
    schedule = MARKET_CALENDAR.schedule(start_date=session_date, end_date=session_date, tz=BROKER_TIMEZONE)

    if schedule.empty:
        return None

    market_open = schedule.iloc[0]["market_open"]
    market_close = schedule.iloc[0]["market_close"]

    last_bar_time = market_close - pd.Timedelta(
        TIME_FREQUENCIES[timeframe]
    )

    return market_open, last_bar_time



