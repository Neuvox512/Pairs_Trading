from datetime import date
import pandas as pd
from src.data.preparation.market_session import get_session_bar_range

def test_get_session_bar_range ():
    #Weekend (sunday)
    session_date = date(2026, 8, 2)
    session_bar_range = get_session_bar_range(session_date, 'M1')

    assert session_bar_range is None

    #Workday (monday)
    session_date = date(2026, 8, 3)
    session_bar_range = get_session_bar_range(session_date, 'M1')

    assert session_bar_range[0] == pd.Timestamp("2026-08-03 16:30:00", tz="Europe/Bucharest")
    assert session_bar_range[1] == pd.Timestamp("2026-08-03 22:59:00", tz="Europe/Bucharest")
