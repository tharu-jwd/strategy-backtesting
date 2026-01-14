"""Portfolio simulator for tracking positions and P&L."""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Trade:
    """Represents a single trade."""

    def __init__(
        self,
        date: datetime,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        commission: float = 0.0
    ):
        """
        Initialize a trade.

        Args:
            date: Trade date
            ticker: Stock ticker
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Execution price
            commission: Trading commission
        """
        self.date = date
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.price = price
        self.commission = commission
        self.total_cost = (quantity * price) + commission

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Trade({self.date.date()}, {self.action} {self.quantity} "
            f"{self.ticker} @ ${self.price:.2f})"
        )


class Portfolio:
    """
    Portfolio simulator for backtesting.

    Tracks cash, positions, trades, and calculates P&L.
    """

    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.0):
        """
        Initialize portfolio.

        Args:
            initial_capital: Starting cash amount
            commission: Commission per trade (flat fee or percentage)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission = commission
        self.positions: Dict[str, int] = {}  # ticker -> quantity
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.logger = logger

    def buy(self, date: datetime, ticker: str, quantity: int, price: float) -> bool:
        """
        Execute a buy order.

        Args:
            date: Trade date
            ticker: Stock ticker
            quantity: Number of shares to buy
            price: Execution price

        Returns:
            True if trade executed, False if insufficient funds
        """
        total_cost = (quantity * price) + self.commission

        if total_cost > self.cash:
            self.logger.warning(
                f"Insufficient funds: need ${total_cost:.2f}, have ${self.cash:.2f}"
            )
            return False

        # Execute trade
        self.cash -= total_cost
        self.positions[ticker] = self.positions.get(ticker, 0) + quantity

        # Record trade
        trade = Trade(date, ticker, "BUY", quantity, price, self.commission)
        self.trades.append(trade)

        self.logger.info(f"Executed: {trade}")
        return True

    def sell(self, date: datetime, ticker: str, quantity: int, price: float) -> bool:
        """
        Execute a sell order.

        Args:
            date: Trade date
            ticker: Stock ticker
            quantity: Number of shares to sell
            price: Execution price

        Returns:
            True if trade executed, False if insufficient shares
        """
        current_position = self.positions.get(ticker, 0)

        if quantity > current_position:
            self.logger.warning(
                f"Insufficient shares: trying to sell {quantity}, have {current_position}"
            )
            return False

        # Execute trade
        total_proceeds = (quantity * price) - self.commission
        self.cash += total_proceeds
        self.positions[ticker] -= quantity

        # Remove position if fully closed
        if self.positions[ticker] == 0:
            del self.positions[ticker]

        # Record trade
        trade = Trade(date, ticker, "SELL", quantity, price, self.commission)
        self.trades.append(trade)

        self.logger.info(f"Executed: {trade}")
        return True

    def get_position(self, ticker: str) -> int:
        """
        Get current position for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Number of shares held
        """
        return self.positions.get(ticker, 0)

    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.

        Args:
            current_prices: Dictionary of ticker -> current price

        Returns:
            Total portfolio value (cash + positions)
        """
        positions_value = sum(
            self.positions[ticker] * current_prices.get(ticker, 0)
            for ticker in self.positions
        )
        return self.cash + positions_value

    def record_equity(self, date: datetime, current_prices: Dict[str, float]):
        """
        Record equity curve data point.

        Args:
            date: Current date
            current_prices: Dictionary of ticker -> current price
        """
        portfolio_value = self.calculate_portfolio_value(current_prices)

        self.equity_curve.append({
            'date': date,
            'cash': self.cash,
            'portfolio_value': portfolio_value,
            'returns': (portfolio_value - self.initial_capital) / self.initial_capital
        })

    def get_equity_curve(self) -> pd.DataFrame:
        """
        Get equity curve as DataFrame.

        Returns:
            DataFrame with date, cash, portfolio_value, returns
        """
        if not self.equity_curve:
            return pd.DataFrame()

        df = pd.DataFrame(self.equity_curve)
        df.set_index('date', inplace=True)
        return df

    def get_trades_df(self) -> pd.DataFrame:
        """
        Get all trades as DataFrame.

        Returns:
            DataFrame with trade history
        """
        if not self.trades:
            return pd.DataFrame()

        trades_data = [
            {
                'date': t.date,
                'ticker': t.ticker,
                'action': t.action,
                'quantity': t.quantity,
                'price': t.price,
                'commission': t.commission,
                'total_cost': t.total_cost
            }
            for t in self.trades
        ]

        return pd.DataFrame(trades_data)

    def get_summary(self) -> Dict:
        """
        Get portfolio performance summary.

        Returns:
            Dictionary with performance metrics
        """
        if not self.equity_curve:
            return {}

        final_value = self.equity_curve[-1]['portfolio_value']
        total_return = (final_value - self.initial_capital) / self.initial_capital

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': len(self.trades),
            'remaining_cash': self.cash,
            'active_positions': len(self.positions)
        }
