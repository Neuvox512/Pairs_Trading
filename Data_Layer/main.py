import data_update as dup
from Data_Analysis.Pairs import Pairs
import DBManager as dbm
import MetaTrader5 as mt5
import pandas as pd
from MT5 import MT5_Provider
from data_update import *
from datetime import datetime

def main():

    print("Loading data...")

    dup.mass_update()

    print("Data are loaded")
    print("==========================================================")
    # pairs = Pairs(symbol_1,symbol_2,'M30', 126, 40)
    # if pairs.cointegration() <= 0.05:
    #     print(f'p-value = {pairs.cointegration():.4f}')
    #     print(f'Pairs {symbol_1} and {symbol_2} are cointegrated')
    #
    # print (f'alfa = {pairs.coef()[0]}')
    # print (f'beta = {pairs.coef()[1]}')
    # pairs.z_score_plot()
main()