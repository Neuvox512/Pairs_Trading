from datetime import date
import pandas as pd
from src.data.market_session import get_sessions_and_bars


def pnl_summary(calculated_pnl : pd.DataFrame, year_risk_free_rate : float) -> pd.Series:
    trading_days = calculated_pnl['session_date'].nunique()
    start_balance = calculated_pnl['balance'].iloc[0]
    result_balance = calculated_pnl['balance'].iloc[-1]
    pnl_pct = (result_balance-start_balance)/start_balance * 100
    risk_free_rate = year_risk_free_rate / 252

    daily_changes = (
            calculated_pnl.groupby('session_date')
            .agg(session_start_equity = ('equity', 'first'), session_end_equity = ('equity', 'last'))
    )
    daily_changes['daily_pnl_pct'] = (
            (daily_changes['session_end_equity'] - daily_changes['session_start_equity']
             ) / daily_changes['session_start_equity'] * 100
    )
    avg_daily_pnl = daily_changes['daily_pnl_pct'].values.mean()
    daily_pnl_std = daily_changes['daily_pnl_pct'].std()
    daily_sharpe = (avg_daily_pnl - risk_free_rate)/daily_pnl_std
    annualized_daily_sharpe = daily_sharpe * (252**0.5)

    summary = pd.Series(
        {
            'period_start' : calculated_pnl['session_date'].min(),
            'period_end' : calculated_pnl['session_date'].max(),
            'trading_days' : trading_days,
            'max_drawdown_pct' : calculated_pnl['drawdown'].max(),
            'pnl_pct' : pnl_pct,
            'annualized_sharpe_ratio' : annualized_daily_sharpe
        }
    )

    return summary


def calculate_pnl(
        period_history : pd.DataFrame,
        start_date : date,
        end_date : date,
        timeframe : str,
        initial_balance: float,
) -> pd.DataFrame:
    sessions_and_times = get_sessions_and_bars(start_date, end_date, timeframe)

    if period_history.empty:
        raise ValueError("Period history is empty")

    pnl_history = (
        period_history.groupby(['session_date','time'])
        .agg(unrealized_pnl = ('unrealized_pnl', 'sum'), realized_pnl = ('realized_pnl', 'sum'))
        .sort_values(['session_date', 'time'])
        .reset_index(drop=False)
    )

    pnl_history = sessions_and_times.merge(pnl_history, on=['session_date', 'time'], how='left')
    pnl_history = pnl_history.fillna(0)

    pnl_history['realized_pnl'] = (
        pnl_history.groupby('session_date')['realized_pnl'].
        diff().fillna(pnl_history['realized_pnl']).cumsum()
    )
    pnl_history['equity'] = pnl_history['realized_pnl'] + pnl_history['unrealized_pnl'] + initial_balance
    pnl_history['balance'] = pnl_history['realized_pnl'] + initial_balance
    pnl_history['drawdown'] = (pnl_history['equity'].cummax() - pnl_history['equity'])/pnl_history['equity'].cummax() * 100

    return pnl_history