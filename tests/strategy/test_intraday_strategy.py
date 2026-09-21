from datetime import date
from src.strategy.intraday_strategy import get_strat_dates


def test_get_strat_dates() -> None:
    liquidity_dates, coint_dates = get_strat_dates(date(2026, 9, 11), 5, 2)

    # date(2026, 9, 7) is Labor day in USA, so NYSE was closed and not added to liquidity_dates
    assert liquidity_dates == [
        date(2026, 9, 1),
        date(2026, 9, 2),
        date(2026, 9, 3),
        date(2026, 9, 4),
        date(2026, 9, 8)]
    assert coint_dates == [date(2026, 9, 9), date(2026, 9, 10)]