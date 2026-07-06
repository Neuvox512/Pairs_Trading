import time
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as sm

SYMBOL_A = "GBPUSD"
SYMBOL_B = "EURUSD"
lot = 0.25
MAGIC_NUMBER = 148822861
WINDOW_SMALL = 20*24*2

if not mt5.initialize():
    print("Ошибка подключения к MT5. Бот остановлен.")
    mt5.shutdown()

def get_dynamic_zscore():
    bars_a = mt5.copy_rates_from_pos(SYMBOL_A, mt5.TIMEFRAME_M30, 1, WINDOW_SMALL + 2)
    bars_b = mt5.copy_rates_from_pos(SYMBOL_B, mt5.TIMEFRAME_M30, 1, WINDOW_SMALL + 2)

    df_a = pd.DataFrame(bars_a)
    df_b = pd.DataFrame(bars_b)

    symbol_B_with_const = sm.add_constant(df_b['close'])
    lin_reg = sm.OLS(df_a['close'], symbol_B_with_const).fit()
    intercept = lin_reg.params['const']
    slope = lin_reg.params['close']
    spread = df_a["close"] - (slope * df_b["close"] + intercept)

    df_s1 = spread[1:].values
    df_s2 = spread[:-1].values
    s_2_with_const = sm.add_constant(df_s2)

    model = sm.OLS(df_s1, s_2_with_const).fit()
    if model.pvalues[1] > 0.05:
        raise ValueError(f'Mean revertion is impossible: no cointegration')
    a = model.params[0]
    b = model.params[1]
    std_residuals = np.std(model.resid)
    if b >= 1.0 or b <= 0:
        raise ValueError(f'Mean revertion is impossible: b = {b}')

    theta = -np.log(b) / 1.0
    mu = a / (1 - b)
    sigma = std_residuals * np.sqrt((-2 * np.log(b)) / (1.0 * (1 - b ** 2)))
    half_time = np.log(2) / theta

    z_score = (df_s2[-1] - mu) / (sigma / (np.sqrt(2 * theta)))
    diff_spread = df_s2[-1] - mu
    return z_score,diff_spread,half_time, slope

diff_spread_snapshot = get_dynamic_zscore()[1]

def get_pnl(SYMBOL_A,SYMBOL_B):
    positions = mt5.positions_get(magic=MAGIC_NUMBER)
    if positions is None:
        return
    for pos in positions:
        if pos.symbol == SYMBOL_A:
            pnl_A = pos.profit + pos.swap
        if pos.symbol == SYMBOL_B:
            pnl_B = pos.profit + pos.swap
    total_pnl = pnl_A + pnl_B
    return total_pnl

def check_our_positions():

    positions = mt5.positions_get(magic=MAGIC_NUMBER)
    if not positions or len(positions) == 0:
        return 0

    for pos in positions:
        if pos.symbol == SYMBOL_A:
            if pos.type == mt5.ORDER_TYPE_BUY:
                return 1  # Long of SYMBOL_A
            elif pos.type == mt5.ORDER_TYPE_SELL:
                return -1  # Short of SYMBOL_A
    return 0


def send_order(symbol, order_type, volume):
    price = (mt5.symbol_info_tick(symbol).ask
             if order_type == mt5.ORDER_TYPE_BUY
             else mt5.symbol_info_tick(symbol).bid)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": MAGIC_NUMBER,
        "comment": "PairTrading Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Ошибка ордера по {symbol}: {result.comment}")
    return result


def close_all_positions():
    positions = mt5.positions_get(magic=MAGIC_NUMBER)
    if not positions:
        return

    print("Сигнал на закрытие прибыли. Закрываем ноги...")
    for pos in positions:
        reverse_type = (
            mt5.ORDER_TYPE_SELL
            if pos.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )
        send_order(pos.symbol, reverse_type, pos.volume)

print("Робот запущен и отслеживает рынок...")


prev_spread_sign = None
while True:
    try:
        current_pos_state = check_our_positions()
        z, diff_spread, half_time, slope = get_dynamic_zscore()
        print(f"Z-Score: {z:.2f} | Позиция в MT5: {current_pos_state} | Спред: {diff_spread:.5f}")
        print('half_time:', half_time)

        if current_pos_state == 0:
            if z >= 1.0:
                print("!!! СИГНАЛ: Продажа спреда !!!")
                send_order(SYMBOL_A, mt5.ORDER_TYPE_SELL, lot)
                send_order(SYMBOL_B, mt5.ORDER_TYPE_BUY, round(lot * slope, 2))
                diff_spread_snapshot = diff_spread

            elif z <= -1.0:
                print("!!! СИГНАЛ: Покупка спреда !!!")
                send_order(SYMBOL_A, mt5.ORDER_TYPE_BUY, lot)
                send_order(SYMBOL_B, mt5.ORDER_TYPE_SELL, round(lot * slope, 2))
                diff_spread_snapshot = diff_spread

        elif current_pos_state != 0:
            z = get_dynamic_zscore()
            if get_pnl(SYMBOL_A, SYMBOL_B) >= 0.8 * (diff_spread_snapshot*100000*lot):
                close_all_positions()
            else:
                print(f'PnL: {get_pnl(SYMBOL_A, SYMBOL_B)} | Yield: {round(get_pnl(SYMBOL_A, SYMBOL_B)/(diff_spread_snapshot*100000*lot),2)}%')

        time.sleep(1800)

    except Exception as e:
        print(f"Критическая ошибка в цикле: {e}")
        time.sleep(10)