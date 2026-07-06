from datetime import datetime
from DBManager import DBManager
from MT5 import MT5_Provider
from Timeframes import timeframes
import Timeframes as tf

def update_pair(symbol: str, timeframe):

    timeframe = tf.Timeframe(timeframe)
    db = DBManager(timeframe.frame)
    provider = MT5_Provider()

    df_local = db.get_bars(symbol, limit=1)

    last_time = df_local['time'].iloc[0]
    time_delta = int(((datetime.now() - last_time).total_seconds() / 60 // timeframe.id) + timeframe.id)

    if time_delta <= 1:
        print("Data are already up-to-date!")
        provider.close_connection()
        return
    else:
        print(f" Updating {symbol}...")
        df_raw = provider.fetch_bars_from(symbol, timeframe.id, time_delta)

    if not df_raw.empty:
        db.save_bars(symbol, df_raw)

    provider.close_connection()


def mass_update():
    print(f"\n==================================================")
    print(f"Mass update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"==================================================")

    USD_PAIRS = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]

    for timeframe in timeframes.keys():
        for symbol in USD_PAIRS:
            print(f"Updating {symbol} for {timeframe}...")
            try:
                update_pair(symbol,timeframe)
            except Exception as e:
                print(f"Can not update {symbol}: {e}")

    print(f"Mass update complete!")
