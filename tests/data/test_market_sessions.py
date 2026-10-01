from datetime import date
import pandas as pd
from src.data.market_session import (
    get_trading_dates,
    get_full_session_bar_range,
    get_previous_trading_dates,
    get_local_session_bar_range,
    get_session_data)


def test_get_session_data(sim_db) -> None:
    session_date = date(2026, 8, 3)
    symbols = ['first_i1', 'indep_i1', 'stationary', 'second_i1']
    timeframe = 'M1'

    session_data = get_session_data(sim_db, symbols, timeframe, session_date)

    print(session_data.columns.tolist())
    assert len(session_data) == 390
    assert  session_data.columns.tolist() == [
        ('close', 'first_i1'),
        ('close', 'indep_i1'),
        ('close', 'second_i1'),
        ('close', 'stationary'),
        ('spread', 'first_i1'),
        ('spread', 'indep_i1'),
        ('spread', 'second_i1'),
        ('spread', 'stationary')
    ]


def test_get_previous_trading_dates() -> None:
    session_date = date(2026, 1, 10)
    previous_dates = get_previous_trading_dates(session_date, sessions_count=2)

    assert previous_dates == [date(2026, 1, 8), date(2026, 1, 9)]
    

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


def test_local_session_bar_range() -> None:
    session_date = date(2026, 8, 3)
    timeframe = 'M1'
    local_session_bar_range = get_local_session_bar_range(session_date, timeframe, 90)

    assert local_session_bar_range == (
        pd.Timestamp('2026-08-03 13:30:00+0000', tz='UTC'),
        pd.Timestamp('2026-08-03 14:59:00+0000', tz='UTC'))

    timeframe = 'M5'
    local_session_bar_range = get_local_session_bar_range(session_date, timeframe, 90)

    assert local_session_bar_range == (
        pd.Timestamp('2026-08-03 13:30:00+0000', tz='UTC'),
        pd.Timestamp('2026-08-03 14:55:00+0000', tz='UTC'))


def test_get_full_session_bar_range () -> None:
    #Weekend (sunday)
    session_date = date(2026, 8, 2)
    session_bar_range = get_full_session_bar_range(session_date, 'M1')

    assert session_bar_range is None

    #Workday (monday)
    session_date = date(2026, 8, 3)
    session_bar_range = get_full_session_bar_range(session_date, 'M1')

    assert session_bar_range[0] == pd.Timestamp("2026-08-03 13:30:00", tz="UTC")
    assert session_bar_range[1] == pd.Timestamp("2026-08-03 19:59:00", tz="UTC")

