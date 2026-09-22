import pandas as pd
from sklearn.linear_model import LinearRegression


def fit_spread_parameters(pair_prices : pd.DataFrame, first_symbol : str, second_symbol : str) -> tuple[float, float]:
    dependent_prices = pair_prices[[first_symbol]]
    independent_prices = pair_prices[[second_symbol]]

    regression_model = LinearRegression()
    regression_model.fit(independent_prices, dependent_prices)

    intercept = regression_model.intercept_
    hedge_ratio = regression_model.coef_[0]

    return intercept, hedge_ratio