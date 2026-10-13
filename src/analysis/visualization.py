import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def plot_pnl_results(pnl_results : pd.DataFrame) -> Figure:
    daily_changes = (
            pnl_results.groupby('session_date')
            .agg(session_start_equity = ('equity', 'first'),
                 session_end_equity = ('equity', 'last')
            )
    ).sort_values('session_date').reset_index()

    daily_changes['daily_pnl_pct'] = (
            (daily_changes['session_end_equity'] - daily_changes['session_start_equity']
             ) / daily_changes['session_start_equity'] * 100
    )

    fig, (equity_ax, pnl_ax) = plt.subplots(
        nrows=2, ncols=1, sharex=True, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 2]}, layout="constrained"
    )

    equity_ax.plot(
        daily_changes['session_date'], daily_changes['session_end_equity'], label='Equity', color='#2563EB', linewidth=1.5
    )
    equity_ax.set_title("Equity Chart")
    equity_ax.set_ylabel("Daily Equity (USD)")

    pnl_ax.bar(
        daily_changes['session_date'],
        daily_changes['daily_pnl_pct'],
        label='Daily Profit & Loss',
        color=['#16A085' if value >= 0 else '#D95F59' for value in daily_changes['daily_pnl_pct']],
        width=1.5,
    )
    pnl_ax.axhline(y=0, color='#666666', linewidth=1.0)
    pnl_ax.set_title("Profit & Loss")
    pnl_ax.set_ylabel("Daily Return (%)")

    pnl_ax.set_xlabel("Date")

    for ax in (equity_ax, pnl_ax):
        ax.spines["top"].set_color("#CCCCCC")
        ax.spines["right"].set_color("#CCCCCC")
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")

        ax.set_xlim(daily_changes['session_date'].min(), daily_changes['session_date'].max())
        ax.grid(alpha=0.3)

    fig.autofmt_xdate(rotation=30)

    return fig


def show_liquidity_params_distribution(symbols_liquidity_quality : pd.DataFrame) -> None:
    fig, ax = plt.subplots(1,3, figsize = (12,7))
    ax[0].hist(symbols_liquidity_quality['avg_tick_volume'], bins = 50)
    ax[0].set_title('Average daily tick volume')

    ax[1].hist(symbols_liquidity_quality['coverage_pct'], bins = 50)
    ax[1].set_title('Coverage (%)')

    ax[2].hist(symbols_liquidity_quality['avg_spread_pct'], bins = 50)
    ax[2].set_title('Average spread (%)')

    plt.show()