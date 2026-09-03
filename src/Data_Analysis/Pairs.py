import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.Data_Layer.DBManager import DBManager
from src.Data_Layer import Timeframes as tf
import statsmodels.tsa.stattools as sm
from datetime import datetime, timedelta

comission = 0.0003

class Pairs:
    def __init__(self, symbol_1 : str, symbol_2 : str, timeframe : str,
                 date_from : datetime, date_to : datetime, small_window : int):
        self.symbol_1 = symbol_1
        self.symbol_2 = symbol_2
        self.timeframe = tf.Timeframe(timeframe)
        self.big_window_start = date_from
        self.big_window_end = date_to
        self.small_window = small_window
        self.df = self.pairs(self.symbol_1, self.symbol_2, self.timeframe)

    def pairs(self, symbol_1 : str, symbol_2 : str, timeframe : object):
        db = DBManager(self.timeframe.frame)

        query = ("SELECT time, close FROM rates WHERE symbol = ? AND "
                 "time BETWEEN ? AND ?"
                 " AND TIME(time) BETWEEN '16:30:00' AND '23:00:00' ")
        param_1 = [symbol_1, self.big_window_start, self.big_window_end]
        param_2 = [symbol_2, self.big_window_start,self.big_window_end]

        with db.get_connection() as conn:
            df_1 = pd.read_sql_query(query, conn, params=param_1)
            df_2 = pd.read_sql_query(query, conn, params=param_2)

        df_pairs = pd.merge(df_1, df_2, on='time', how='outer').ffill().bfill()
        df_pairs = df_pairs.rename(columns={'close_x': symbol_1, 'close_y': symbol_2})
        return df_pairs

    def cointegration(self,):
        try:
            coint_t, p_value, critical_values = sm.coint(self.df[self.symbol_1], self.df[self.symbol_2])
            return p_value
        except Exception as e:
            print(f'Error in cointegration: {e}')

    def coef (self):
        df = self.df
        if df.empty:
            print ('No data!')
        model = sm.OLS(df[self.symbol_1], df[self.symbol_2]).fit()
        hedge_ratio = model.params[self.symbol_2]
        return hedge_ratio

    def spread(self):
        df = self.df.copy()
        df['Spread'] = df[self.symbol_1] - (df[self.symbol_2] * self.coef())
        return df

    def z_score(self):
        df = self.spread().copy()
        df = df[df['time'].between(datetime.strftime(
            self.big_window_end - timedelta(minutes = 2 * self.small_window),'%Y-%m-%d %H:%M:%S'),
            self.big_window_end.strftime('%Y-%m-%d %H:%M:%S'))]
        df['Spread_mean'] = df['Spread'].rolling(window=df.shape[0]//2).mean()
        df['Spread_std'] = df['Spread'].rolling(window=df.shape[0]//2).std()
        df['Z-Score'] = (df['Spread'] - df['Spread_mean']) / df['Spread_std']
        df.dropna(inplace=True)
        return df[df['time'].between(datetime.strftime
            (self.big_window_end - timedelta(days = self.small_window),
             '%Y-%m-%d %H:%M'), self.df['time'].iloc[-1])]

    def half_time(self):
        df = self.spread().copy()
        dz = df['Spread'].diff().dropna().values
        spread_dev = (df['Spread'] - df['Spread'].mean()).shift(1).dropna().values
        model = sm.OLS(dz, spread_dev).fit()
        theta = model.params[0]
        half_time = np.log(2) / theta

        return abs(round(half_time,0)) # half time

    def backtest(self, lot : float, z_open : float):
        return self.backtesting(self, lot, z_open)

    class backtesting:
        def __init__(self, pairs_instance, lot : float, z_open : float):
            self.parent = pairs_instance
            self.lot = lot
            self.z_open = z_open
            self.z_close = z_open * 0.2
            self.df = self.bt(self.lot, self.z_open, self.z_close)

        def bt (self, lot, z_open, z_close):
            df = self.parent.z_score().copy()
            slope = self.parent.coef()
            signals = []
            bars_count = 0
            current_state = 0
            for i in range(len(df)):
                z = df['Z-Score'].iloc[i]

                if current_state == 0:
                    if z >= z_open: current_state = -1 # Short
                    if z <= -z_open: current_state = 1 # Long
                elif current_state == 1  and z >= z_close:
                    current_state = 0
                    bars_count = 0
                elif current_state == -1  and z <= z_close:
                    current_state = 0
                    bars_count = 0
                elif current_state == -1 or current_state == 1:
                    bars_count += 1
                if bars_count >= 3 * self.parent.half_time():
                    current_state = 0
                    bars_count = 0

                signals.append(current_state)
            df['positions'] = signals

            df[f'PnL ({self.parent.symbol_1})'] = df['positions'].shift(1) * df[self.parent.symbol_1].diff() * lot * 100
            df[f'PnL ({self.parent.symbol_2})'] = -df['positions'].shift(1) * df[self.parent.symbol_2].diff() * lot * slope * 100
            df['PnL'] = df[f'PnL ({self.parent.symbol_1})'] + df[f'PnL ({self.parent.symbol_2})']
            df.dropna(inplace=True)
            return df

        def pnl(self):
            return round(self.df['PnL'].iloc[-1], 2)

        def plot(self):
            df = self.df.copy()
            df["time"] = pd.to_datetime(df["time"])
            title_text = (
                f"PnL {self.parent.symbol_1} / {self.parent.symbol_2} [{self.parent.timeframe.frame}] for {int(self.parent.small_window / self.parent.timeframe.bars)} days")
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["PnL"],
                    mode="lines",
                    name=f"PnL ({self.parent.symbol_1} - {self.parent.symbol_2})",
                    line=dict(color="#2ecc71", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(46, 204, 113, 0.15)",
                )
            )
            fig.add_shape(
                type="line",
                x0=df["time"].min(),
                y0=0,
                x1=df["time"].max(),
                y1=0,
                line=dict(color="#ff2e63", width=1.5, dash="dash"),
            )
            fig.update_layout(
                title=dict(
                    text=title_text,
                    x=0.5,
                    y=0.95,
                    xanchor="center",
                    font=dict(size=18, color="#eeeeee", weight="bold"),
                ),
                paper_bgcolor="#111111",
                plot_bgcolor="#111111",
                xaxis=dict(
                    gridcolor="#444444",
                    tickfont=dict(size=12, color="#aaaaaa"),
                ),
                yaxis=dict(
                    gridcolor="#444444",
                    tickfont=dict(size=12, color="#aaaaaa"),
                    title=dict(
                        text="PnL value", font=dict(size=14, color="#eeeeee")
                    ),
                    tickformat=".4f",
                    range=[df["PnL"].min() * 1.1, df["PnL"].max() * 1.1],
                ),
                legend=dict(
                    x=0.02,
                    y=0.98,
                    bgcolor="rgba(34, 40, 49, 0.8)",
                    font=dict(size=10, color="#eeeeee"),
                ),
                margin=dict(l=100, r=40, t=70, b=60),
                width=600,
                height=325,
            )
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                ]
            )
            fig.show()

    def spread_plot(self):
        df = self.spread().copy()
        df["time"] = pd.to_datetime(df["time"])

        title_text = (
            f"Spread {self.symbol_1} / {self.symbol_2} [{self.timeframe.frame}]"
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["Spread"],
                mode="lines",
                name=f"Spread ({self.symbol_1} - {self.symbol_2})",
                line=dict(color="#fbd46d", width=2),
                fill="tozeroy",
                fillcolor="rgba(251, 212, 109, 0.15)",
            )
        )

        fig.add_shape(
            type="line",
            x0=df["time"].min(),
            y0=0,
            x1=df["time"].max(),
            y1=0,
            line=dict(color="#ff2e63", width=1.5, dash="dash"),
        )

        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                y=0.95,
                xanchor="center",
                font=dict(size=18, color="#eeeeee", weight="bold"),
            ),
            paper_bgcolor="#111111",
            plot_bgcolor="#111111",
            xaxis=dict(
                gridcolor="#444444",
                tickfont=dict(size=12, color="#aaaaaa"),
            ),
            yaxis=dict(
                gridcolor="#444444",
                tickfont=dict(size=12, color="#aaaaaa"),
                title=dict(
                    text="Spread value", font=dict(size=14, color="#eeeeee")
                ),
                tickformat=".4f",
                range=[df["Spread"].min() * 1.1, df["Spread"].max() * 1.1],
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(34, 40, 49, 0.8)",
                font=dict(size=10, color="#eeeeee"),
            ),
            margin=dict(l=100, r=40, t=70, b=60),
            width=600,
            height=325,
        )

        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
            ]
        )

        fig.show()

    def z_score_plot(self):
        df = self.z_score().copy()
        df["time"] = pd.to_datetime(df["time"])

        title_text = (
            f"Z-Score {self.symbol_1} / {self.symbol_2} [{self.timeframe.frame}] for {self.small_window} days"
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["Z-Score"],
                mode="lines",
                name=f"Z-Score ({self.symbol_1} - {self.symbol_2})",
                line=dict(color="#ff9f43", width=2),
                fill="tozeroy",
                fillcolor="rgba(255, 159, 67, 0.15)",
            )
        )

        fig.add_shape(
            type="line",
            x0=df["time"].min(),
            y0=0,
            x1=df["time"].max(),
            y1=0,
            line=dict(color="#ff2e63", width=1.5, dash="dash"),
        )

        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                y=0.95,
                xanchor="center",
                font=dict(size=18, color="#eeeeee", weight="bold"),
            ),
            paper_bgcolor="#111111",
            plot_bgcolor="#111111",
            xaxis=dict(
                gridcolor="#444444",
                tickfont=dict(size=12, color="#aaaaaa"),
            ),
            yaxis=dict(
                gridcolor="#444444",
                tickfont=dict(size=12, color="#aaaaaa"),
                title=dict(
                    text="Z-Score value", font=dict(size=14, color="#eeeeee")
                ),
                tickformat=".4f",
                range=[df["Z-Score"].min() * 1.1, df["Z-Score"].max() * 1.1],
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(34, 40, 49, 0.8)",
                font=dict(size=10, color="#eeeeee"),
            ),
            margin=dict(l=100, r=40, t=70, b=60),
            width=600,
            height=325,
        )

        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
            ]
        )

        fig.show()


# pairs = Pairs('NVDA','BAC','M1',
#               datetime(2026, 1, 12, 19, 00, 00),
#               datetime(2026, 1, 12, 20, 00, 00),
#               30)
# print(pairs.coef())