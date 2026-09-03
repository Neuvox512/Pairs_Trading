from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from DBManager_COPY import DBManager
from MT5_COPY import MT5_Provider
from Timeframes_COPY import timeframes
import Timeframes_COPY as tf

def update_pair(symbol: str, timeframe):

    timeframe = tf.Timeframe(timeframe)
    db = DBManager(timeframe.frame)
    provider = MT5_Provider()

    df_local = db.get_bars(symbol, limit=1)

    last_time = df_local['time'].iloc[0]
    time_delta = int(((datetime.now(ZoneInfo("Europe/Bucharest")) - last_time).total_seconds() / 60 // timeframe.id) + timeframe.id)

    if time_delta <= 1:
        print("data are already up-to-date!")
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
    print(f"Mass update: {datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%Y-%m-%d %H:%M')}")
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

def new_pair(symbol: str, timeframe, days : int):
    timeframe = tf.Timeframe(timeframe)
    db = DBManager(timeframe.frame)
    provider = MT5_Provider()
    date_from = datetime.now(ZoneInfo("Europe/Bucharest")) - timedelta(days=days)

    df_from_db = db.get_bars(symbol, limit=1)
    if not df_from_db.empty:
        print(f" Symbol {symbol} is already in database!")
    else:
        print(f" Adding {symbol}...")
        df_raw = provider.fetch_bars_from(symbol, timeframe.id, date_from)
        if not df_raw.empty:
            db.save_bars(symbol, df_raw)
        print(f" {symbol} is successfully added to database!")

    provider.close_connection()

new_pair("GS", 'M5', 7)
