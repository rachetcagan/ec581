# strategies/hp_filter.py

import backtrader as bt
import pandas as pd
import statsmodels.api as sm
from utils.strategy_utils import log_strategy

class HPFilterIndicator(bt.Indicator):
    """
    Hodrick–Prescott Filter Indicator

    Produces two lines:
      - trend: the smoothed long‐term component
      - cycle: deviation of price from trend
    """
    lines = ('trend', 'cycle',)
    params = dict(
        lamb=1600,   # smoothing parameter (1600 is standard for daily data)
    )

    def __init__(self):
        # Need at least a few points to start filtering
        self.addminperiod(4)

    def next(self):
        # Grab all closes up to current bar as a Pandas Series
        # `get(ago=0, size=N)` gives the last N values, oldest first
        closes = pd.Series(self.data.close.get(size=len(self)))
        # Apply HP filter
        trend, cycle = sm.tsa.filters.hpfilter(closes, lamb=self.p.lamb)
        # Assign the latest values to our lines
        self.lines.trend[0] = trend.iloc[-1]
        self.lines.cycle[0] = cycle.iloc[-1]


class HPFilterStrategy(bt.Strategy):
    """
    HP Filter Strategy

    • Uses HPFilterIndicator to decompose price into trend & cycle.
    • Goes LONG when cycle > 0 (price above trend).
    • Exits (SELL) when cycle < 0.
    """
    params = dict(
        lamb=1600,   # smoothing for HP filter
        stake=100,   # shares per trade
    )

    def __init__(self):
        self.order = None
        # attach the HP filter indicator
        self.hp = HPFilterIndicator(self.data, lamb=self.p.lamb)

    def log(self, txt, dt=None):
        log_strategy(self, txt, dt)

    def next(self):
        if self.order:
            return

        cycle = self.hp.cycle[0]

        # Entry: price above trend
        if not self.position and cycle > 0:
            self.log(f"BUY CREATE  price={self.data.close[0]:.2f}  cycle={cycle:.2f}")
            self.order = self.buy(size=self.p.stake)

        # Exit: price below trend
        elif self.position and cycle < 0:
            self.log(f"SELL CREATE price={self.data.close[0]:.2f}  cycle={cycle:.2f}")
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
