def backtest(df,beta):

    lot = 0.1
    signals = []
    current_state = 0
    for i in range(len(df)):
        z = df['Z-Score'].iloc[i]
        cross = df['zero_cross'].iloc[i]

        if current_state == 0:
            if z >= 0.6: current_state = -1
            if z <= -0.6: current_state = 1
        elif (current_state == 1 or current_state == -1) and cross:
            current_state = 0

        signals.append(current_state)
    df['positions'] = signals

    df['PnL_raw_x'] = df['positions'].shift(1)*df['close_x'].diff()*lot*100000
    df['PnL_raw_y'] = -df['positions'].shift(1)*df['close_y'].diff()*lot*beta*100000
    df['PnL_raw'] = df['PnL_raw_x'] + df['PnL_raw_y']

    return df