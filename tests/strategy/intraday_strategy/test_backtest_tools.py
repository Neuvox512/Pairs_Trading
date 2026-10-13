import pandas as pd
import pytest
from src.strategies.intraday_strategy.backtest_tools import simulate_trades


def test_simulate_trades(hedge_ratio = 2, entry_z = 2) -> None:
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
        2,
        10,
        3,
        1.5,
        0.5,
        5,
        1.0
    )

    if entry_z > 0:
        direction = -1
    else:
        direction = 1

    assert trades_history['direction'].tolist() == ([0, direction, direction] + [0]*297)

    assert trades_history['realized_pnl'].iloc[3] == pytest.approx(-4.4, abs=0.001)
    assert trades_history['realized_pnl'].iloc[3] == trades_history['realized_pnl'].iloc[-1]

    assert trades_history['quantity_1'].tolist() == ([0] + 2 * [symbols_info['contract_size'][0] * direction] + [0]*297)
    assert trades_history['quantity_2'].tolist() == (
            [0] + 2 * [symbols_info['contract_size'][1] * -direction * hedge_ratio] + [0] * 297
    )
