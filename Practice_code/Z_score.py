import matplotlib.pyplot as plt
import numpy as np

def z_score(df):
    days = int(input("Enter period (working days): "))
    period = days * 24 * 12

    df['spread_mean'] = df['spread'].rolling(window=period).mean()
    df['spread_std'] = df['spread'].rolling(window=period).std()
    df['Z-Score'] = (df['spread'] - df['spread_mean'])/df['spread_std']
    df.dropna(inplace=True)
    return df.tail(period)

def z_score_analysis(df):
    plt.plot(df['Z-Score'])
    plt.show()

    df['sign'] = np.sign(df['Z-Score'])
    df['zero_cross'] = df['sign'].diff().ne(0) & df['Z-Score'].shift().notna()
    print(f"Total amount of crossings during {int(df.shape[0]/24/60)} working days:", df['zero_cross'].iloc[:].sum())
    return df
