import pandas as pd
import MetaTrader5 as mt5
import numpy as np
import statsmodels.tsa.stattools as ts
import matplotlib.pyplot as plt

if not mt5.initialize():
    print("initialize() failed, error code =",mt5.last_error())
    quit()

#define symbols to be compared, timeframe and period
days = input("Enter the number of days: ")
if days == '': days = 252
else:days = int(days)
symbol1 = 'AUDUSD'
symbol2 = 'EURUSD'
timeframe = mt5.TIMEFRAME_M5
period = 24 * days * 12

def data_collection():
    #create dataframes of extracted bars from history
    aud_df = pd.DataFrame(mt5.copy_rates_from_pos(symbol1, timeframe, 0,period))
    nzd_df = pd.DataFrame(mt5.copy_rates_from_pos(symbol2, timeframe, 0,period))

    #define new dataframe with 'time' and 'close' attributes
    aud_df = pd.DataFrame(aud_df[['time','close']])
    nzd_df = pd.DataFrame(nzd_df[['time','close']])

    #change time format
    aud_df['time'] = pd.to_datetime(aud_df['time'], unit='s')
    nzd_df['time'] = pd.to_datetime(nzd_df['time'], unit='s')
    aud_df = aud_df.set_index('time')
    nzd_df = nzd_df.set_index('time')

    #Merging dataframes
    final_df = pd.merge(aud_df, nzd_df, on='time')
    aud = final_df['close_x']
    nzd = final_df['close_y']
    return final_df

def spread(df):
    x_with_const = ts.add_constant(df['close_y'])
    model = ts.OLS(df['close_x'], x_with_const).fit()
    alfa =  model.params['const']
    beta = model.params['close_y']
    df['spread'] = df['close_x'] - alfa - beta * df['close_y']
    return df,alfa,beta

#method for data analysis during the period
def spread_analysis(df):
    plt.plot(df['spread'])
    plt.show()

    df['sign'] = np.sign(df['spread'])
    df['zero_cross'] = df['sign'].diff().ne(0) & df['spread'].shift().notna()
    print(f"Total amount of crossings during {days} working days:", df['zero_cross'].iloc[-(period * 24*60):].sum())
    return df

def cointegration(df):
    z_score,p_value, crit_values = ts.coint(df['close_x'], df['close_y'])
    print(z_score)
    print(p_value)
    print(crit_values)


