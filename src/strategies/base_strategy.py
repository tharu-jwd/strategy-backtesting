"""Base strategy class for defining trading strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd
from enum import Enum


class Signal(Enum):
    """Trading signals."""
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All strategies must implement the generate_signals method.
    """

    def __init__(self, name: str):
        """
        Initialize the strategy.

        Args:
            name: Strategy name
        """
        self.name = name
        self.parameters = {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on market data.

        Args:
            data: DataFrame with OHLCV data (indexed by date)
                  Required columns: open, high, low, close, volume

        Returns:
            Series with trading signals (1=BUY, -1=SELL, 0=HOLD) indexed by date
        """
        pass

    def set_parameters(self, **params):
        """
        Set strategy parameters.

        Args:
            **params: Strategy-specific parameters
        """
        self.parameters.update(params)

    def get_parameters(self) -> Dict:
        """
        Get current strategy parameters.

        Returns:
            Dictionary of parameters
        """
        return self.parameters.copy()

    def __str__(self) -> str:
        """String representation of strategy."""
        return f"{self.name}({self.parameters})"

    def __repr__(self) -> str:
        """String representation of strategy."""
        return self.__str__()
