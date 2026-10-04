from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
import pandas as pd
from src.strategies.intraday_strategy.backtest_tools import pnl_summary, backtest_period, calculate_pnl

if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    period_start = date(2026, 8,25)
    period_end = date(2026, 8,26)
    timeframe = 'M1'

    # backtest_history = backtest_period(
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
    # backtest_history.to_parquet('backtest.parquet')
    # print(backtest_history)
    backtest = pd.read_parquet('backtest.parquet')
    # print(backtest)
    pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    # print(pnl[['equity', 'balance', 'drawdown']].tail(60))
    pnl_summary = pnl_summary(pnl, 0)
    print(pnl_summary)