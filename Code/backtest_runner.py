# backtest_runner.py

import backtrader as bt
from utils.data_loader import load_csv_data, load_api_data

def run_backtest(
    strategy_class,
    use_api: bool,
    data_path: str = None,
    symbol: str = None,
    start: str = None,
    end: str = None,
    initial_cash: float = 10_000,
    commission: float = 0.001,
    **strategy_kwargs
):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    cerebro.addstrategy(strategy_class, **strategy_kwargs)

    # --- data selection ---
    if use_api:
        data_feed = load_api_data(symbol=symbol, start=start, end=end)
    else:
        data_feed = load_csv_data(data_path)
    cerebro.adddata(data_feed)

    # --- run & report ---
    start_val = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {start_val:.2f}")
    cerebro.run()
    end_val = cerebro.broker.getvalue()
    print(f"Final Portfolio Value:   {end_val:.2f}")
    print(f"Net Change:              {end_val - start_val:.2f}")
    return cerebro
