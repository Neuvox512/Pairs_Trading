from datetime import date
import pandas as pd
import pandas_market_calendars as mcal
from src.data.timeframes import TIME_FREQUENCIES


NYSE_CALENDAR = mcal.get_calendar("NYSE")

def get_session_bar_range(session_date: date, timeframe: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    #Roboforex broker used here as example and therefore timezone is set to 'Europe/Bucharest'
    #Change 'tz' parameter according to your broker timezone
    schedule = NYSE_CALENDAR.schedule(start_date=session_date, end_date=session_date, tz='Europe/Bucharest')

    if schedule.empty:
        return None

    market_open = schedule.iloc[0]["market_open"]
    market_close = schedule.iloc[0]["market_close"]

    last_bar_time = market_close - pd.Timedelta(
        TIME_FREQUENCIES[timeframe]
    )

    return market_open, last_bar_time