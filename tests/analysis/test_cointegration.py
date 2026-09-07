import pandas as pd
import numpy as np
from src.analysis.cointegration import cointegration_p_value

def test_cointegration_p_value() -> None:
    random_gen = np.random.RandomState(0)

    time_index = pd.date_range(start='2026-08-02', periods=500, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=500).cumsum(),
                                       index=time_index)

    second_symbol_cl_prices = pd.Series(50 + 2*first_symbol_cl_prices + random_gen.normal(size=500, scale=0.5),
                                        index=time_index)

    p_value = cointegration_p_value(first_symbol_cl_prices, second_symbol_cl_prices)

    print('p_value is ',p_value)
    assert p_value < 0.05

