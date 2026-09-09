from datetime import date
import pandas as pd
from src.data.preparation.market_session import get_trading_dates, get_session_bar_range


def test_get_trading_dates() -> None:
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 10)

    trading_dates = get_trading_dates(start_date, end_date)

    assert trading_dates == [date(2026, 1, 2),
                             date(2026, 1, 5),
                             date(2026, 1, 6),
                             date(2026, 1, 7),
                             date(2026, 1, 8),
                             date(2026, 1, 9)]


def test_get_session_bar_range () -> None:
    #Weekend (sunday)
    session_date = date(2026, 8, 2)
    session_bar_range = get_session_bar_range(session_date, 'M1')

    assert session_bar_range is None

    #Workday (monday)
    session_date = date(2026, 8, 3)
    session_bar_range = get_session_bar_range(session_date, 'M1')

    assert session_bar_range[0] == pd.Timestamp("2026-08-03 16:30:00", tz="Europe/Bucharest")
    assert session_bar_range[1] == pd.Timestamp("2026-08-03 22:59:00", tz="Europe/Bucharest")

