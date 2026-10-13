import pandas as pd
import pytest
from datetime import date

from statsmodels.genmod.families.links import sqrt

from src.strategies.intraday_strategy.backtest_tools import simulate_trades, calculate_pnl, pnl_summary


def test_pnl_summary() -> None:
    calculated_pnl = pd.DataFrame({
        'session_date' : (
            2 * [date(2026, 8, 3)]
            + 2 * [date(2026,8,4)]
            + 2 * [date(2026,8,5)]
        ),
        'balance' : [100, 102, 102, 102, 102, 101],
        'equity' : [100, 102, 102, 102, 102, 101],
        'drawdown' : [0, 0, 0, 0, 0, 1],
    })

    risk_free_rate = 4
    pnl_results = pnl_summary(calculated_pnl, 4)

    # daily returns
    daily_returns = [(102-100)/100*100, (102-102)/102*100, (101-102)/102*100]
    expected_mean = sum(daily_returns)/ 3
    expected_std = (
        (
                (expected_mean-daily_returns[0])**2
                + (expected_mean-daily_returns[1])**2
                + (expected_mean-daily_returns[2])**2
         ) / (3-1)) ** 0.5
    expected_sharpe = ((expected_mean - risk_free_rate/252) / expected_std) * 252**0.5

    assert pnl_results['trading_days'] == 3
    assert pnl_results['pnl_pct'] == pytest.approx(1, abs = 0.001)
    assert pnl_results['max_drawdown_pct'] == pytest.approx(1, abs = 0.001)
    assert pnl_results['annualized_sharpe_ratio'] == pytest.approx(expected_sharpe, abs = 0.001)


def test_calculate_pnl() -> None:
    first_day_pair_1 = pd.DataFrame({
        "time": pd.date_range(
            "2026-08-03 13:30", periods=390, freq="min", tz="UTC"
        ),
        "session_date": date(2026, 8, 3),
        "unrealized_pnl": [0, -4] + [0] * 388,
        "realized_pnl": [0, 0] + [-3] * 388,
    })

    first_day_pair_2 = first_day_pair_1.copy()
    first_day_pair_2['unrealized_pnl'] = [0, -2] + [0] * 388
    first_day_pair_2['realized_pnl'] = [0, 0] + [-1] * 388

    last_day_pair_1 = pd.DataFrame({
        "time": pd.date_range(
            "2026-08-05 13:30", periods=390, freq="min", tz="UTC"
        ),
        "session_date": date(2026, 8, 5),
        "unrealized_pnl": [0, 5] + [0] * 388,
        "realized_pnl": [0, 0] + [3] * 388,
    })

    history = pd.concat([first_day_pair_1, first_day_pair_2, last_day_pair_1], ignore_index=True).reset_index(drop=True)

    pnl = calculate_pnl(
        history,
        date(2026, 8, 3),
        date(2026, 8, 5),
        'M1',
        initial_balance = 100
    )

    assert len(pnl) == 390 * 3

    assert pnl['balance'].iloc[0] == 100
    assert pnl['unrealized_pnl'].iloc[1] == pytest.approx(-6, abs = 0.001)
    assert pnl['realized_pnl'].iloc[2] == pytest.approx(-4, abs = 0.001)
    assert pnl['drawdown'].iloc[1] == pytest.approx(6, abs = 0.001)
    assert pnl['drawdown'].iloc[2] == pytest.approx(4, abs = 0.001)

    no_trades_day = pnl[pnl['session_date'] == date(2026, 8, 4)]
    assert (no_trades_day['balance'] == 96).all() & (no_trades_day['equity'] == 96).all()
    assert (no_trades_day['unrealized_pnl'] == 0).all()

    last_day = pnl[pnl['session_date'] == date(2026, 8, 5)]
    assert last_day['realized_pnl'].iloc[0] == pytest.approx(-4, abs = 0.001)
    assert last_day['drawdown'].iloc[0] == pytest.approx(4, abs = 0.001)
    assert last_day['unrealized_pnl'].iloc[1] == pytest.approx(5, abs = 0.001)
    assert last_day['equity'].iloc[1] == pytest.approx(101, abs = 0.001)
    assert last_day['drawdown'].iloc[1] == pytest.approx(0, abs = 0.001)
    assert last_day['realized_pnl'].iloc[2] == pytest.approx(-1, abs = 0.001)
    assert last_day['drawdown'].iloc[2] == pytest.approx(1.98, abs = 0.001)

    assert pnl['equity'].iloc[-1] == pnl['balance'].iloc[-1] == pytest.approx(99, abs = 0.001)


@pytest.mark.parametrize(
    "hedge_ratio, entry_z, expected_pnl, half_life",
    [
        (2, 2, -1.4, 1),
        (2, 2, -4.4, 10),
        (2, -2, 3.6, 10),
        (-2, 2, -0.4, 10),
        (-2, -2, -0.4, 10),
    ],
)

def test_simulate_trades(hedge_ratio, entry_z, expected_pnl, half_life) -> None:
    symbols_info = pd.DataFrame({
        'symbol': ['JPM', 'AAPL'],
        'point' : [0.1, 0.1],
        'contract_size' : [1.0, 1.0],
        'volume_min' : [0.1, 0.1],
        'volume_max' : [100.0, 100.0],
        'volume_step' : [0.1, 0.1],
    })

    if hedge_ratio > 0:
        second_exit_price = 200
    else:
        second_exit_price = 201

    prices = pd.DataFrame({
        'time' : pd.date_range('2026-08-03 15:00', periods=300, freq = 'min'),
        'symbol_1' : 'JPM',
        'symbol_2' : 'AAPL',
        'symbol_1_close' : [100,101,102] + [103]*290 + [102]*7,
        'symbol_2_close' : [200]*3 + [199]*290 + [second_exit_price]*7,
        'symbol_1_spread' : 2,
        'symbol_2_spread' : 1,
        'z_score' : [0, entry_z, entry_z+1] + [0]*290 + [2]*5 + [0]*2,
    })

    trades_history = simulate_trades(
        prices,
        'M1',
        symbols_info,
        hedge_ratio,
        half_life,
        1,
        1.5,
        0.5,
        5,
        1.0
    )

    if entry_z > 0:
        direction = -1
    else:
        direction = 1

    assert trades_history['realized_pnl'].iloc[3] == pytest.approx(expected_pnl, abs=0.001)

    if half_life > 1:
        assert trades_history['direction'].tolist() == ([0, direction, direction] + [0]*297)

        assert trades_history['realized_pnl'].iloc[3] == trades_history['realized_pnl'].iloc[-1]

        assert trades_history['quantity_1'].tolist() == ([0] + 2 * [symbols_info['contract_size'][0] * direction] + [0]*297)
        assert trades_history['quantity_2'].tolist() == (
                [0] + 2 * [symbols_info['contract_size'][1] * -direction * hedge_ratio] + [0] * 297
    )

    else:
        assert trades_history['direction'].tolist() == ([0, direction] + [0] * 298)

        assert trades_history['realized_pnl'].iloc[3] == trades_history['realized_pnl'].iloc[-1]

        assert trades_history['quantity_1'].tolist() == (
                    [0] + 1 * [symbols_info['contract_size'][0] * direction] + [0] * 298)
        assert trades_history['quantity_2'].tolist() == (
                [0] + 1 * [symbols_info['contract_size'][1] * -direction * hedge_ratio] + [0] * 298
        )

    # print(trades_history.head(10)