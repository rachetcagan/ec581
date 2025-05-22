# utils/strategy_utils.py

def log_strategy(self, txt: str, dt=None):
    """
    Standard logging for any strategy.
    """
    dt = dt or self.data.datetime.date(0)
    print(f"{dt.isoformat()}  {txt}")
