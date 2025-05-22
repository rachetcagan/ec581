# utils/data_loader.py

import backtrader as bt
import pandas as pd
import yfinance as yf

def load_csv_data(data_path: str, dtformat: str = '%Y-%m-%d') -> bt.feeds.GenericCSVData:
    """Load OHLCV from CSV."""
    return bt.feeds.GenericCSVData(
        dataname=data_path,
        dtformat=dtformat,
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1
    )

def load_api_data(
    symbol: str,
    start: str,
    end: str,
    timeframe: str = '1d'
) -> bt.feeds.PandasData:
    """
    Fetch OHLCV from Yahoo via yfinance and wrap in a Backtrader feed.
    start/end in 'YYYY-MM-DD' format.
    """
    # yfinance now defaults to auto_adjust=True.
    df = yf.download(symbol, start=start, end=end, interval=timeframe)

    if df.empty:
        raise ValueError(
            f"No data fetched for symbol {symbol} from {start} to {end}. "
            "Download may have failed (e.g., YFRateLimitError, invalid symbol, no data for period)."
        )

    # Handle potential MultiIndex columns (e.g., if yf.download gets a list of symbols
    # or returns a MultiIndex for a single symbol under certain conditions/errors).
    if isinstance(df.columns, pd.MultiIndex):
        # Assuming the actual OHLCV names ('Open', 'High', etc.) are in the first level
        # if yfinance returns columns like ('Open', 'AAPL'), ('Close', 'AAPL')
        df.columns = df.columns.get_level_values(0)

    # Ensure column names are strings and convert to lowercase for consistent mapping.
    df.columns = [str(col).lower() for col in df.columns]
    
    df.index = pd.to_datetime(df.index) # Ensure index is datetime

    # Standardize column names. yfinance with auto_adjust=True typically provides
    # 'open', 'high', 'low', 'close', 'volume' (after lowercasing).
    # 'close' is the adjusted close.
    rename_map = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'adj close': 'close', # Map 'adj close' to 'close' if present
        'close': 'close',     # Ensure 'close' (potentially adjusted) maps to 'close'
        'volume': 'volume'
    }
    
    # Apply renaming for columns found in rename_map, keep others as is.
    df.rename(columns=lambda c: rename_map.get(c, c), inplace=True)

    required_cols = ['open', 'high', 'low', 'close', 'volume']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"DataFrame for {symbol} is missing required columns: {missing_cols} "
            f"after processing. Available columns: {df.columns.tolist()}"
        )
        
    # Select only the required columns for Backtrader's PandasData feed.
    # Using .copy() to avoid potential SettingWithCopyWarning later.
    df_for_bt = df[required_cols].copy()

    return bt.feeds.PandasData(dataname=df_for_bt)
