from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path

import pandas as pd
from src.strategies.intraday_strategy.backtest_tools import pnl_summary, backtest_period, calculate_pnl
from src.strategies.intraday_strategy.backtest_tools import *

if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    period_start = date(2025, 1,1)
    period_end = date(2026, 8,31)
    timeframe = 'M1'


    backtest_history = backtest_period(
        db,
        period_start,
        period_end,
        timeframe,
        2,
        6,
        1.5,
        0.5,
        6,
        1,
        10,
        1,
        0.9,
        0.5,
        0.5,
        120,
        0.1,
        0.05,
        0.75,
        2.5
    )
    # signal_z == current_bar + more candidates + 6_min_hlm + 120_min_opening
    backtest_history.to_parquet(f'backtest_2025.01_2026.08.parquet')

    # backtest = pd.read_parquet('backtest_6.parquet')
    #
    # pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    # pnl_summary = pnl_summary(pnl, 4)
    # print(pnl_summary)