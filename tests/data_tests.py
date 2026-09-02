from DBManager_COPY import DBManager
from MT5_COPY import *
from data_update_COPY import *

def test_mt5():
    mt = MT5_Provider()
    x = mt.fetch_bars_from('GS', mt5.TIMEFRAME_M15, datetime(2026, 5, 1))
    print(x)
    mt.close_connection()
    return x

def test_db():
    db = DBManager('M5')
    db.save_bars('GS', test_mt5())

def test_db2():
    new_pair("GS", 'M5', 7)

def test_data_update():
    db = DBManager('M5')
    mt = MT5_Provider()
    local_data = db.get_bars('GS', limit=1)
    last_local_time = local_data['time'].iloc[0]
    last_local_time = datetime.strptime(str(last_local_time), '%Y-%m-%d %H:%M:%S')
    data_from_mt5 = pd.DataFrame(mt5.copy_rates_from_pos('GS', 5, 1, 1))
    actual_time = pd.to_datetime(data_from_mt5.iloc[0]['time'], unit='s')
    rates = mt5.copy_rates_range('GS', 5, last_local_time, actual_time)
    df = pd.DataFrame(rates)
    df = pd.to_datetime(df['time'], unit='s')
    print(df.tail(10))
