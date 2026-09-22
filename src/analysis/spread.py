import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np


#Ornstein-Uhlenbeck discrete formula was used to calculate half-life
def calculate_spread_half_life(pair_spread : pd.Series) -> float | None:
    lag_spread = pair_spread.shift(1).dropna()
    d_spread = pair_spread - lag_spread
    d_spread = d_spread.dropna()
    mean_spread = lag_spread.mean()
    x = lag_spread - mean_spread
    x = x.to_frame()

    regression_model = LinearRegression(fit_intercept=False)
    regression_model.fit(x, d_spread)

    theta = regression_model.coef_[0]
    if theta >= 0:
        return None

    half_life = -np.log(2) / theta

    return half_life


def calculate_pair_spread_z_score(local_spread : pd.Series, global_spread : pd.Series) -> pd.Series:
    global_mean = global_spread.mean()
    global_std = global_spread.std()

    z_score = (local_spread - global_mean)/global_std

    return z_score


def calculate_pair_spread(
        pair_prices : pd.DataFrame,
        first_symbol : str,
        second_symbol : str,
        intercept : float,
        hedge_ratio : float
) -> pd.Series:

    spread = pair_prices[first_symbol] - pair_prices[second_symbol] * hedge_ratio - intercept

    return spread


def fit_spread_parameters(pair_prices : pd.DataFrame, first_symbol : str, second_symbol : str) -> tuple[float, float]:
    dependent_prices = pair_prices[first_symbol]
    independent_prices = pair_prices[[second_symbol]]

    regression_model = LinearRegression()
    regression_model.fit(independent_prices, dependent_prices)

    intercept = regression_model.intercept_
    hedge_ratio = regression_model.coef_[0]

    return intercept, hedge_ratio