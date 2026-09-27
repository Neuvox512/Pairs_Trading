import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from src.data.timeframes import TIME_MINUTES


#Ornstein-Uhlenbeck formula was used to calculate half-life
#ds = theta(mu - s)dt + sigma * dW
#ds/dt = theta * mu - theta * s + stochastic_term    OR    Y = const - beta * X + residuals
def calculate_spread_half_life(pair_spread : pd.Series, timeframe : str) -> float | None:
    dt = TIME_MINUTES[timeframe]
    reg_data = pd.DataFrame(
        {
        'lag_spread' : pair_spread.shift(1),
        'diff_spread' : pair_spread.diff()
        }
    )

    real_dt = pair_spread.index.to_series().diff()
    consecutive_bars = (real_dt == pd.Timedelta(minutes=dt))

    reg_data = reg_data[consecutive_bars].dropna()
    x = reg_data[['lag_spread']]
    y = reg_data['diff_spread'] / dt

    regression_model = LinearRegression()
    regression_model.fit(x, y)

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