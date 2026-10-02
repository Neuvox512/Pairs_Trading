from backtest_tools import backtest_period, calculate_pnl
from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
import pandas as pd

if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    period_start = date(2026, 8,25)
    period_end = date(2026, 8,26)
    timeframe = 'M1'

    # backtest_history, session = backtest_period(
    #     db,
    #     period_start,
    #     period_end,
    #     timeframe,
    #     3,
    #     2,
    #     0.5,
    #     3,
    #     1,
    #     10,
    #     1,
    #     0.9,
    #     0.75,
    #     0.25,
    #     90,
    #     0.1,
    #     0.05,
    # )
    # backtest_history.to_csv('backtest.csv', index=False)
    backtest = pd.read_csv('backtest.csv')
    pnl = calculate_pnl(backtest, period_start, period_end, timeframe)
    pnl.to_excel('pnl.xlsx')
