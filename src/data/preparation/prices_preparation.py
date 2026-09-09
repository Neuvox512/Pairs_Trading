import pandas as pd
from datetime import date
from src.data.sqlite_db import  SQLiteDB
from src.data.preparation.market_session import get_session_bar_range


def get_session_prices(db : SQLiteDB, symbols : list[str], timeframe : str,session_date : date):
    session_range = get_session_bar_range(session_date, timeframe)

    if session_range is None:
        return pd.DataFrame()

    close_prices = db.load_close_prices(symbols, timeframe, session_range[0], session_range[1])
    close_prices = close_prices.ffill()

    return close_prices
