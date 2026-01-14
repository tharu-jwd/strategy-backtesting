"""Moving Average Crossover Strategy implementation."""

import pandas as pd
from src.strategies.base_strategy import BaseStrategy, Signal


class MovingAverageCrossover(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy.

    Generates BUY signal when short MA crosses above long MA.
    Generates SELL signal when short MA crosses below long MA.
    """

    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initialize the Moving Average Crossover strategy.

        Args:
            short_window: Short moving average window (default: 20)
            long_window: Long moving average window (default: 50)
        """
        super().__init__(name="Moving Average Crossover")
        self.short_window = short_window
        self.long_window = long_window
        self.set_parameters(short_window=short_window, long_window=long_window)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MA crossover.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with signals (1=BUY, -1=SELL, 0=HOLD)
        """
        if len(data) < self.long_window:
            raise ValueError(
                f"Insufficient data: need at least {self.long_window} rows, "
                f"got {len(data)}"
            )

        # Calculate moving averages
        data = data.copy()
        data['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['close'].rolling(window=self.long_window).mean()

        # Initialize signals
        signals = pd.Series(Signal.HOLD.value, index=data.index)

        # Generate signals based on crossover
        # BUY when short MA crosses above long MA
        # SELL when short MA crosses below long MA
        for i in range(1, len(data)):
            prev_idx = data.index[i-1]
            curr_idx = data.index[i]

            prev_short = data.loc[prev_idx, 'short_ma']
            prev_long = data.loc[prev_idx, 'long_ma']
            curr_short = data.loc[curr_idx, 'short_ma']
            curr_long = data.loc[curr_idx, 'long_ma']

            # Check for valid values (not NaN)
            if pd.notna([prev_short, prev_long, curr_short, curr_long]).all():
                # Bullish crossover
                if prev_short <= prev_long and curr_short > curr_long:
                    signals.loc[curr_idx] = Signal.BUY.value
                # Bearish crossover
                elif prev_short >= prev_long and curr_short < curr_long:
                    signals.loc[curr_idx] = Signal.SELL.value

        return signals
