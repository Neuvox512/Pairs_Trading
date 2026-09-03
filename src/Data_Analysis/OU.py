import numpy as np
from Pairs import Pairs
import statsmodels.tsa.stattools as sm
import pandas as pd
import matplotlib.pyplot as plt


def OU (df):
    dt = 1.0
    Y = df['Spread'].iloc[1:].values
    X = df['Spread'].iloc[:-1].values
    X_with_const = sm.add_constant(X)
    model = sm.OLS(Y, X_with_const).fit()
    if model.pvalues[1] > 0.05:
        raise ValueError (f'Mean revertion is impossible: no cointegration')

    a = model.params[0]
    b = model.params[1]
    std_residuals = np.std(model.resid)

    if b >= 1.0 or b <= 0:
        raise ValueError (f'Mean revertion is impossible: b = {b}')

    theta = -np.log(b)/dt
    mu = a/(1-b)
    sigma = std_residuals * np.sqrt((-2*np.log(b))/(dt*(1-b**2)))
    half_time = np.log(2)/theta

    z_score = (X[-1] - mu)/(sigma/(np.sqrt(2*theta)))
    return z_score,half_time,mu,X[-1],X[-1]-mu


# df = pd.DataFrame()
# time = []
# z_sc = []
# half_t = []
# mu = []
# spread_ = []
# spread_diff = []
# for i in range(48*19):
#     pairs = Pairs('GBPUSD','EURUSD','M30',126,20, 0+i)
#     spread = pairs.spread()
#     time.append(spread['time'].iloc[-1])
#     z_sc.append(half_time (spread)[0])
#     half_t.append(half_time (spread)[1])
#     mu.append(half_time (spread)[2])
#     spread_.append(half_time (spread)[3])
#     spread_diff.append(half_time (spread)[4])
#     i = i+1
#     print(i)
# df['time'] = time
# df['z_sc'] = z_sc
# df['half_time'] = half_t
# df['mu'] = mu
# df['spread'] = spread_
# df['spread_diff'] = spread_diff
# df = df.iloc[::-1].reset_index(drop=True)
#
# plt.plot(df['z_sc'])
# plt.show()
# plt.plot(df['mu'])
# plt.show()
# plt.plot(df['spread'])
# plt.show()
# plt.plot(df['spread_diff'])
# plt.show()
# print(df.head())

# list_ = []
# for i in range(126):
#     pairs = Pairs('GBPUSD','EURUSD','M30',i+1,1)
#     print(pairs.cointegration())
#     if pairs.cointegration() < 0.06:
#         list_.append(i)
# print(list_)

pairs = Pairs('GBPUSD','EURUSD','M30',126,20)
print(pairs.z_score_plot())