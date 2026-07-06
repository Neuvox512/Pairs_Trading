import Spread
import pandas as pd
from Z_score import z_score, z_score_analysis
from Spread import data_collection, spread, cointegration, spread_analysis
from Backtest import backtest
import matplotlib.pyplot as plt

data = data_collection()
cointegration(data)

data = spread(data)

# spread_analysis(data)

z_score = z_score(data[0])
z_score = z_score_analysis(z_score)
print(z_score)

# print(z_score['Z-Score'].iloc[-1])
print("alfa:",data[1])
print("beta:",data[2])

# 

