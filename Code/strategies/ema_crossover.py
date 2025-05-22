# strategies/ema_crossover.py

import backtrader as bt
from utils.strategy_utils import log_strategy

class EMACrossover(bt.Strategy):
    """
    Exponential MA Crossover:
      • BUY when fast EMA crosses above slow EMA
      • SELL when fast EMA crosses below slow EMA
    """
    params = dict(
        fast_period=12,
        slow_period=26,
        stake=1,
    )

    def __init__(self):
        self.order = None
        self.ema_fast  = bt.ind.EMA(self.data.close, period=self.p.fast_period)
        self.ema_slow  = bt.ind.EMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.ind.CrossOver(self.ema_fast, self.ema_slow)

    def log(self, txt, dt=None):
        log_strategy(self, txt, dt)

    def next(self):
        if self.order:
            return

        if not self.position and self.crossover > 0:
            self.log(f"BUY CREATE  price={self.data.close[0]:.2f}")
            self.order = self.buy(size=self.p.stake)
        elif self.position and self.crossover < 0:
            self.log(f"SELL CREATE price={self.data.close[0]:.2f}")
            self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status is order.Completed:
            dir_ = 'BUY' if order.isbuy() else 'SELL'
            self.log(f"{dir_} EXECUTED  price={order.executed.price:.2f}  "
                     f"cost={order.executed.value:.2f}  comm={order.executed.comm:.2f}")
        else:
            self.log("Order Canceled/Margin/Rejected")
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"TRADE PROFIT  GROSS={trade.pnl:.2f}  NET={trade.pnlcomm:.2f}")
