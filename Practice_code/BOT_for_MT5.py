import time
import MetaTrader5 as mt5
import pandas as pd

SYMBOL_A = "GBPUSD"
SYMBOL_B = "EURUSD"
LOT_A = 0.3
MAGIC_NUMBER = 148822861
ALPHA = 0.12159844176115589
BETA = 1.051366382624424
small_window = 20 * 48

if not mt5.initialize():
    print("Can not connect to MT5")
    mt5.shutdown()


def get_current_z_score():
    bars_a = mt5.copy_rates_from_pos(SYMBOL_A, mt5.TIMEFRAME_M30, 1, small_window * 2)
    bars_b = mt5.copy_rates_from_pos(SYMBOL_B, mt5.TIMEFRAME_M30, 1, small_window * 2)

    df_a = pd.DataFrame(bars_a)
    df_b = pd.DataFrame(bars_b)

    spread = df_a["close"] - (BETA * df_b["close"] + ALPHA)

    mean = spread.rolling(small_window).mean().iloc[-1]
    std = spread.rolling(small_window).std().iloc[-1]
    current_spread = spread.iloc[-1]

    z_score = (current_spread - mean) / std
    spread_centered = current_spread - mean

    return z_score, spread_centered


def check_our_positions():
    positions = mt5.positions_get(magic=MAGIC_NUMBER)
    if not positions or len(positions) == 0:
        return 0

    for pos in positions:
        if pos.symbol == SYMBOL_A:
            if pos.type == mt5.ORDER_TYPE_BUY:
                return 1  # symbol_1 long
            elif pos.type == mt5.ORDER_TYPE_SELL:
                return -1  # symbol_2 short
    return 0


def send_order(symbol, order_type, volume, position_id=None):
    price = (mt5.symbol_info_tick(symbol).ask
             if order_type == mt5.ORDER_TYPE_BUY
             else mt5.symbol_info_tick(symbol).bid)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,  # slipering
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

    print("Closing positions..")
    for pos in positions:
        reverse_type = (
            mt5.ORDER_TYPE_SELL
            if pos.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )
        send_order(pos.symbol, reverse_type, pos.volume, position_id=pos.ticket)



print("BOT is monitoring market...")

prev_spread_sign = None

while True:
    try:
        z, current_centered_spread = get_current_z_score()
        current_pos_state = check_our_positions()

        print(
            f"Z-Score: {z:.2f} | Position in MT5: {current_pos_state} | Delta_spread : {current_centered_spread:.5f}"
        )

        if current_pos_state == 0:
            if z >= 1.1:
                print("!!! Signal: Short Spread !!!")
                send_order(SYMBOL_A, mt5.ORDER_TYPE_SELL, LOT_A)
                send_order(SYMBOL_B, mt5.ORDER_TYPE_BUY, round(LOT_A * BETA, 2))
            elif z <= -1.1:
                print("!!! Signal: Long Spread !!!")
                send_order(SYMBOL_A, mt5.ORDER_TYPE_BUY, LOT_A)
                send_order(SYMBOL_B, mt5.ORDER_TYPE_SELL, round(LOT_A * BETA, 2))

        elif current_pos_state != 0:
            if current_pos_state == -1 and z <= 0.5:
                close_all_positions()
            if current_pos_state == 1 and z >= -0.5:
                close_all_positions()


        time.sleep(1800)

    except Exception as e:
        print(f"Критическая ошибка в цикле: {e}")
        time.sleep(10)
