# strategies/ma_direction.py

import backtrader as bt
from utils.strategy_utils import log_strategy

class MADirection(bt.Strategy):
    """
    Exponential MA Direction Strategy

    • Computes EMA over `period` bars.
    • Defines MA direction as sign(EMA[t] – EMA[t-1]):
        +1 if EMA rising, –1 if falling, 0 if flat.
    • Goes long when direction turns positive and flat/no position.
    • Exits (sells) when direction turns negative and in position.
    """

    params = dict(
        period=20,   # look-back for the EMA
        stake=100,   # size of each trade
    )

    def __init__(self):
        self.order = None

        # The EMA line
        self.ema = bt.ind.EMA(self.data.close, period=self.p.period)

        # Difference between current EMA and prior bar’s EMA
        # (Backtrader lets us call the line backwards via self.ema(-1))
        self.ema_diff = self.ema - self.ema(-1) # Note to self: Change this if for more robustness!

    def log(self, txt, dt=None):
        """Standardized logging from utils/strategy_utils.py"""
        log_strategy(self, txt, dt)

    def next(self):
        # don’t send a new order if one is pending
        if self.order:
            return

        # compute direction
        diff = self.ema_diff[0]
        direction = 1 if diff > 0 else -1 if diff < 0 else 0

        # entry: if rising and no position
        if not self.position and direction > 0:
            self.log(f"BUY CREATE  price={self.data.close[0]:.2f}  direction={direction}")
            self.order = self.buy(size=self.p.stake)

        # exit: if falling and in position
        elif self.position and direction < 0:
            self.log(f"SELL CREATE price={self.data.close[0]:.2f}  direction={direction}")
            self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        # skip submitted/accepted states
        if order.status in [order.Submitted, order.Accepted]:
            return

        # handle completed orders
        if order.status == order.Completed:
            side = 'BUY' if order.isbuy() else 'SELL'
            self.log(f"{side} EXECUTED  price={order.executed.price:.2f}  "
                     f"cost={order.executed.value:.2f}  comm={order.executed.comm:.2f}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # allow new orders
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"TRADE PROFIT  GROSS={trade.pnl:.2f}  NET={trade.pnlcomm:.2f}")
