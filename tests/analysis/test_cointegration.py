import pandas as pd
import numpy as np
from src.analysis.cointegration import integration_p_values, cointegration_p_value


def test_integration_p_values() -> None:
    random_gen = np.random.RandomState(0)
    time_index = pd.date_range(start='2026-08-02', periods=250, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(),
                                       index=time_index)
    first_symbol_p_value = integration_p_values(first_symbol_cl_prices)

    second_symbol_cl_prices = pd.Series(50 + 2 * first_symbol_cl_prices + random_gen.normal(size=250, scale=0.5),
                                        index=time_index)
    second_symbol_p_value = integration_p_values(second_symbol_cl_prices)

    assert first_symbol_p_value[0] > 0.05
    assert first_symbol_p_value[1] < 0.05
    assert second_symbol_p_value[0] > 0.05
    assert second_symbol_p_value[1] < 0.05


def test_cointegration_p_value() -> None:
    random_gen = np.random.RandomState(0)

    time_index = pd.date_range(start='2026-08-02', periods=250, freq='1min', tz='UTC')

    first_symbol_cl_prices = pd.Series(100 + random_gen.normal(size=250).cumsum(),
                                       index=time_index)

    second_symbol_cl_prices = pd.Series(50 + 2*first_symbol_cl_prices + random_gen.normal(size=250, scale=0.5),
                                        index=time_index)

    p_value = cointegration_p_value(first_symbol_cl_prices, second_symbol_cl_prices)

    print('p_value is ',p_value)
    assert p_value < 0.05

