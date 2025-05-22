# main.py

import pandas as pd
import matplotlib.pyplot as plt

from runner import run_and_collect
from strategies.ema_crossover import EMACrossover
from strategies.ma_direction import MADirection
from strategies.hp_filter import HPFilterStrategy
from strategies.lowess import LowessStrategy


# === Global Configuration ===
USE_API       = True
SYMBOL        = '^XU100'
DATA_PATH     = 'data/sample_data.csv'
START_DATE    = '2000-01-01'
END_DATE      = '2025-05-01'
INITIAL_CASH  = 10_000
COMMISSION    = 0.001
STAKE         = 1

# Strategy-specific globals
FAST_PERIOD   = 12
SLOW_PERIOD   = 26

MA_PERIOD     = 20

HP_LAMB       = 1600

LOWESS_FRACTION = 0.10     # <— optimizable fraction for LOWESS

# Master switch: show individual candlestick + trades plots?
SHOW_INDIVIDUAL_PLOTS = False

# List of strategies (name, class, kwargs)
STRATEGIES = [
    ('EMA Crossover', EMACrossover,       dict(fast_period=FAST_PERIOD, slow_period=SLOW_PERIOD, stake=STAKE)),
    ('MA Direction',   MADirection,       dict(period=MA_PERIOD, stake=STAKE)),
    ('HP Filter',      HPFilterStrategy,  dict(lamb=HP_LAMB, stake=STAKE)),
    ('Lowess',         LowessStrategy,    dict(frac=LOWESS_FRACTION, stake=STAKE))
]

def main():
    curves = []
    for name, cls, params in STRATEGIES:
        curve = run_and_collect(
            name,
            cls,
            params,
            use_api=USE_API,
            symbol=SYMBOL,
            data_path=DATA_PATH,
            start_date=START_DATE,
            end_date=END_DATE,
            initial_cash=INITIAL_CASH,
            commission=COMMISSION,
            show_plot=SHOW_INDIVIDUAL_PLOTS
        )
        curves.append(curve)

    # Combine all equity curves for comparison
    df = pd.concat(curves, axis=1)
    df.plot(title='Equity Curve Comparison')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value')
    plt.show()

if __name__ == '__main__':
    main()
