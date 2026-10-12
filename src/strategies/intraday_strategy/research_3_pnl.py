from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
import pandas as pd
from src.strategies.intraday_strategy.backtest_tools import pnl_summary, backtest_period, calculate_pnl
from src.strategies.intraday_strategy.general_tools import plot_backtest_results


if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    period_start = date(2025, 1,1)
    period_end = date(2026, 8,31)
    timeframe = 'M1'

    backtest = pd.read_parquet(
        'backtest_results/signal_is_close/more_candidates/6_hlm/120_opening_minutes/backtest_2025.01_2026.08.parquet'
    )

    pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    pnl_summary = pnl_summary(pnl, 4)
    print(pnl_summary)

    figure = plot_backtest_results(pnl)
    figure.savefig( "backtest_performance.png", dpi=200)
