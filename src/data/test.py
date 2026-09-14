from mt5_terminal import MT5Terminal

mt5 = MT5Terminal()
mt5.connect()
last_bar = mt5.get_latest_closed_bar_time('AAPL.US', 'M1')
print(last_bar)