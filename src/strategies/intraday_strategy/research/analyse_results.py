from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
import pandas as pd
from src.analysis.backtest_metrics import calculate_pnl, pnl_summary
from src.analysis.visualization import plot_pnl_results


if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    timeframe = 'M1'
    period_start = date(2025, 1,1)
    period_end = date(2026, 8,31)

    backtest = pd.read_parquet(
        '../backtest_results/signal_is_close/more_candidates/6_hlm/120_opening_minutes/backtest_2025.01_2026.08.parquet'
    )

    pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    pnl_results = pnl_summary(pnl, 4)
    print(pnl_results)

    figure = plot_pnl_results(pnl)
    figure.savefig( "backtest_performance_1.png", dpi=200)
