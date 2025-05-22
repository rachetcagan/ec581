# strategies/lowess_strategy.py

import backtrader as bt
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess
from utils.strategy_utils import log_strategy

class LowessStrategy(bt.Strategy):
    """
    LOWESS Scatter Plot Smoothing Strategy

    - Smooths the closing price series with LOWESS using `frac`.
    - Generates a long signal when price crosses above its LOWESS curve.
    - Generates an exit signal when price crosses below its LOWESS curve.
    """
    params = dict(
        frac=0.1,    # smoothing fraction for LOWESS (optimizable)
        stake=100,   # shares per trade
    )

    def __init__(self):
        self.order = None
        self.closes = []
        self.smoothed = []

    def log(self, txt, dt=None):
        log_strategy(self, txt, dt)

    def next(self):
        # accumulate close prices
        price = float(self.data.close[0])
        self.closes.append(price)

        # apply LOWESS smoothing to full history
        idx = list(range(len(self.closes)))
        sm = lowess(self.closes, idx, frac=self.p.frac, return_sorted=False)
        self.smoothed = list(sm)
        current_smooth = self.smoothed[-1]

        # only act once we have at least two smoothed points
        if len(self.smoothed) < 2:
            return

        prev_smooth = self.smoothed[-2]
        prev_price  = self.closes[-2]

        # skip if an order is pending
        if self.order:
            return

        # entry: price crosses above smoothing
        if not self.position and prev_price <= prev_smooth and price > current_smooth:
            self.log(f"BUY CREATE  price={price:.2f}  lowess={current_smooth:.2f}")
            self.order = self.buy(size=self.p.stake)

        # exit: price crosses below smoothing
        elif self.position and prev_price >= prev_smooth and price < current_smooth:
            self.log(f"SELL CREATE price={price:.2f}  lowess={current_smooth:.2f}")
            self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            side = 'BUY' if order.isbuy() else 'SELL'
            self.log(f"{side} EXECUTED  price={order.executed.price:.2f}  "
                     f"cost={order.executed.value:.2f}  comm={order.executed.comm:.2f}")
        else:
            self.log("Order Canceled/Margin/Rejected")
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"TRADE PROFIT  GROSS={trade.pnl:.2f}  NET={trade.pnlcomm:.2f}")
