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
    period_end = date(2026, 1,1)
    timeframe = 'M1'

    backtest = pd.read_parquet('backtest_2025.01_2026.01_more_candidates.parquet')

    pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    pnl_summary = pnl_summary(pnl, 4)
    print(pnl_summary)