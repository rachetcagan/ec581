# runner.py

import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt

from utils.data_loader import load_api_data, load_csv_data

def run_and_collect(
    name: str,
    strategy_class,
    strategy_kwargs: dict,
    *,
    use_api: bool,
    symbol: str,
    data_path: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    show_plot: bool = False
) -> pd.Series:
    """
    Run a single strategy, collect its equity curve, and optionally plot candlestick + trades.

    Returns a pandas Series of the equity curve.
    """
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    # ---- data feed ----
    if use_api:
        data_feed = load_api_data(symbol=symbol, start=start_date, end=end_date)
    else:
        data_feed = load_csv_data(data_path=data_path)
    cerebro.adddata(data_feed)

    # ---- strategy + analyzer ----
    cerebro.addstrategy(strategy_class, **strategy_kwargs)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')

    print(f"\n=== Running {name} ===")
    strat = cerebro.run()[0]
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value for {name}: {final_value:.2f}")

    # ---- build equity curve ----
    returns = strat.analyzers.returns.get_analysis()
    returns_series = pd.Series(returns).sort_index()
    equity_curve = (1 + returns_series).cumprod() * initial_cash
    equity_curve.name = name

    # ---- optional individual plot ----
    if show_plot:
        figs = cerebro.plot(style='candlestick')
        # cerebro.plot returns a nested list of figures/axes
        # we can set a title on the first figure
        figs[0][0].suptitle(f"{name} — Candlestick + Trades", fontsize=12)

    return equity_curve
