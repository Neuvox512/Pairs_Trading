import pandas as pd
import numpy as np
import plotly.graph_objects as go
from Data_Layer.DBManager import DBManager
from Data_Layer import Timeframes as tf
import statsmodels.tsa.stattools as sm

class Pairs:
    def __init__(self, symbol_1 : str, symbol_2 : str, timeframe : str, big_window : int, small_window : int, offset = None):
        self.symbol_1 = symbol_1
        self.symbol_2 = symbol_2
        self.timeframe = tf.Timeframe(timeframe)
        self.big_window = big_window * self.timeframe.bars
        self.small_window = small_window * self.timeframe.bars
        self.offset = offset
        self.df = self.pairs(self.symbol_1, self.symbol_2, self.timeframe, self.offset)

    def pairs(self, symbol_1 : str, symbol_2 : str, timeframe : object, offset : int):
        db = DBManager(self.timeframe.frame)
        if offset == None:
            query_1 = '''SELECT time, close FROM rates WHERE symbol = ? ORDER BY time DESC LIMIT ?'''
            param_1 = [symbol_1, self.big_window]
            query_2 = '''SELECT time, close FROM rates WHERE symbol = ? ORDER BY time DESC LIMIT ?'''
            param_2 = [symbol_2, self.big_window]
        else:
            query_1 = '''SELECT time, close FROM rates WHERE symbol = ? ORDER BY time DESC LIMIT ? OFFSET ?'''
            param_1 = [symbol_1, self.big_window, self.offset]
            query_2 = '''SELECT time, close FROM rates WHERE symbol = ? ORDER BY time DESC LIMIT ? OFFSET ?'''
            param_2 = [symbol_2, self.big_window,self.offset]

        with db.get_connection() as conn:
            df_1 = pd.read_sql_query(query_1, conn, params=param_1)
            df_2 = pd.read_sql_query(query_2, conn, params=param_2)

        df_pairs = pd.merge(df_1, df_2, on='time', how='inner')
        df_pairs = df_pairs.rename(columns={'close_x': symbol_1, 'close_y': symbol_2})
        df_pairs = df_pairs.iloc[::-1].reset_index(drop=True)
        return df_pairs

    def cointegration(self,):
        coint_t, p_value, critical_values = sm.coint(self.df[self.symbol_1], self.df[self.symbol_2])
        return p_value

    def coef (self):
        df = self.df.tail(self.small_window).copy()
        symbol_2_with_intercept = sm.add_constant(df[self.symbol_2])
        model = sm.OLS(df[self.symbol_1], symbol_2_with_intercept).fit()
        intercept = model.params['const']
        slope = model.params[self.symbol_2]
        return [intercept, slope]

    def spread(self):
        df = self.df.copy()
        df['Spread'] = df[self.symbol_1] - (df[self.symbol_2] * self.coef()[1] + self.coef()[0])
        return df

    def z_score(self):
        df = self.spread().tail(self.small_window*2).copy()
        df['Spread_mean'] = df['Spread'].rolling(window=self.small_window).mean()
        df['Spread_std'] = df['Spread'].rolling(window=self.small_window).std()
        df['Z-Score'] = (df['Spread'] - df['Spread_mean']) / df['Spread_std']
        df.dropna(inplace=True)
        df['Sign'] = np.sign(df['Z-Score'])
        df['Zero_Cross'] = df['Sign'].diff().ne(0)
        return df.tail(self.small_window)

    def backtest(self, lot : float, z_trig : float, z_sl : float):
        return self.backtesting(self, lot, z_trig, z_sl)

    class backtesting:
        def __init__(self, pairs_instance, lot : float, z_trig : float, z_sl : float):
            self.parent = pairs_instance
            self.lot = lot
            self.z_trig = z_trig
            self.z_sl = z_sl
            self.df = self.bt(self.lot, self.z_trig, self.z_sl)

        def bt (self, lot, z_trig, z_sl):
            df = self.parent.z_score().copy()
            slope = self.parent.coef()[1]
            signals = []
            current_state = 0
            for i in range(len(df)):
                z = df['Z-Score'].iloc[i]

                if current_state == 0:
                    if z >= z_trig: current_state = -1
                    if z <= -z_trig: current_state = 1
                elif current_state == 1  and z >= -z_sl:
                    current_state = 0
                elif current_state == -1  and z <= z_sl:
                    current_state = 0

                signals.append(current_state)
            df['positions'] = signals

            df[f'PnL ({self.parent.symbol_1})'] = df['positions'].shift(1) * df[self.parent.symbol_1].diff() * lot * 100000
            df[f'PnL ({self.parent.symbol_2})'] = -df['positions'].shift(1) * df[self.parent.symbol_2].diff() * lot * slope * 100000
            df['PnL'] = df[f'PnL ({self.parent.symbol_1})'] + df[f'PnL ({self.parent.symbol_2})']
            df['PnL'] = df['PnL'].cumsum()
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

    def half_time(self):
        df = self.z_score().copy()
        dt = 1.0
        Y = df['Spread'].iloc[1:].values
        X = df['Spread'].iloc[:-1].values
        X_with_const = sm.add_constant(X)
        model = sm.OLS(Y, X_with_const).fit()
        if model.pvalues[1] > 0.05:
            raise ValueError(f'Mean revertion is impossible: no cointegration')

        a = model.params[0]
        b = model.params[1]
        std_residuals = np.std(model.resid)

        if b >= 1.0 or b <= 0:
            raise ValueError(f'Mean revertion is impossible: b = {b}')

        theta = -np.log(b) / dt
        mu = a / (1 - b)
        sigma = np.sqrt((-2 * np.log(b)) / (dt * (1 - b ** 2)))
        half_time = np.log(2) / theta

        return round(24 * half_time/self.timeframe.bars,2) # half time in hours

    def spread_plot(self):
        df = self.spread().copy()
        df["time"] = pd.to_datetime(df["time"])

        title_text = (
            f"Spread {self.symbol_1} / {self.symbol_2} [{self.timeframe.frame}] for {int(self.big_window/self.timeframe.bars)} days"
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
            f"Z-Score {self.symbol_1} / {self.symbol_2} [{self.timeframe.frame}] for {int(self.small_window/self.timeframe.bars)} days"
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