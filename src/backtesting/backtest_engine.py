"""Main backtesting engine that orchestrates strategy execution."""

from typing import Optional, Dict
import pandas as pd
from datetime import datetime

from src.data.database import MarketDataDB
from src.strategies.base_strategy import BaseStrategy, Signal
from src.backtesting.portfolio import Portfolio
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestEngine:
    """
    Main backtesting engine.

    Orchestrates data loading, signal generation, trade execution, and performance tracking.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 100000.0,
        commission: float = 0.0,
        position_size: float = 1.0
    ):
        """
        Initialize the backtesting engine.

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Starting portfolio value
            commission: Trading commission per trade
            position_size: Fraction of portfolio to use per trade (0.0 to 1.0)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.position_size = position_size
        self.portfolio = Portfolio(initial_capital, commission)
        self.db = MarketDataDB()
        self.logger = logger
        self.data = None
        self.signals = None

    def run(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Run backtest on a single ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with backtest results
        """
        self.logger.info(f"Starting backtest for {ticker}")
        self.logger.info(f"Period: {start_date} to {end_date}")
        self.logger.info(f"Strategy: {self.strategy}")

        # Load data
        try:
            self.db.connect()
            self.data = self.db.get_stock_data(ticker, start_date, end_date)

            if self.data.empty:
                self.logger.error(f"No data available for {ticker}")
                return {'error': 'No data available'}

            self.logger.info(f"Loaded {len(self.data)} days of data")

        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return {'error': str(e)}

        finally:
            self.db.close()

        # Generate signals
        try:
            self.signals = self.strategy.generate_signals(self.data)
            buy_signals = (self.signals == Signal.BUY.value).sum()
            sell_signals = (self.signals == Signal.SELL.value).sum()
            self.logger.info(f"Generated {buy_signals} BUY and {sell_signals} SELL signals")

        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return {'error': str(e)}

        # Execute backtest
        try:
            self._execute_backtest(ticker)
        except Exception as e:
            self.logger.error(f"Error during backtest execution: {str(e)}")
            return {'error': str(e)}

        # Generate results
        results = self._generate_results(ticker, start_date, end_date)
        self.logger.info("Backtest completed")

        return results

    def _execute_backtest(self, ticker: str):
        """
        Execute backtest by simulating trades based on signals.

        Args:
            ticker: Stock ticker symbol
        """
        position = 0  # 0 = no position, 1 = long position

        for date, signal in self.signals.items():
            current_price = self.data.loc[date, 'close']

            # BUY signal
            if signal == Signal.BUY.value and position == 0:
                # Calculate position size
                max_investment = self.portfolio.cash * self.position_size
                quantity = int(max_investment / current_price)

                if quantity > 0:
                    success = self.portfolio.buy(date, ticker, quantity, current_price)
                    if success:
                        position = 1

            # SELL signal
            elif signal == Signal.SELL.value and position == 1:
                quantity = self.portfolio.get_position(ticker)

                if quantity > 0:
                    success = self.portfolio.sell(date, ticker, quantity, current_price)
                    if success:
                        position = 0

            # Record equity for this day
            self.portfolio.record_equity(date, {ticker: current_price})

    def _generate_results(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Generate backtest results and performance metrics.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with results
        """
        summary = self.portfolio.get_summary()
        equity_curve = self.portfolio.get_equity_curve()
        trades_df = self.portfolio.get_trades_df()

        # Calculate additional metrics
        if not equity_curve.empty:
            returns = equity_curve['returns']
            daily_returns = equity_curve['portfolio_value'].pct_change()

            # Sharpe ratio (assuming 252 trading days, 0% risk-free rate)
            if daily_returns.std() != 0:
                sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)
            else:
                sharpe_ratio = 0

            # Maximum drawdown
            cumulative = (1 + daily_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # Buy and hold comparison
            initial_price = self.data['close'].iloc[0]
            final_price = self.data['close'].iloc[-1]
            buy_hold_return = (final_price - initial_price) / initial_price

        else:
            sharpe_ratio = 0
            max_drawdown = 0
            buy_hold_return = 0

        results = {
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'strategy': str(self.strategy),
            'initial_capital': self.initial_capital,
            'final_value': summary.get('final_value', 0),
            'total_return': summary.get('total_return', 0),
            'total_return_pct': summary.get('total_return_pct', 0),
            'buy_hold_return_pct': buy_hold_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': summary.get('total_trades', 0),
            'remaining_cash': summary.get('remaining_cash', 0),
            'active_positions': summary.get('active_positions', 0),
            'equity_curve': equity_curve,
            'trades': trades_df
        }

        return results

    def print_results(self, results: Dict):
        """
        Print backtest results in a formatted way.

        Args:
            results: Results dictionary from run()
        """
        if 'error' in results:
            print(f"\nError: {results['error']}")
            return

        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"\nTicker: {results['ticker']}")
        print(f"Period: {results['start_date']} to {results['end_date']}")
        print(f"Strategy: {results['strategy']}")
        print(f"\nInitial Capital: ${results['initial_capital']:,.2f}")
        print(f"Final Value: ${results['final_value']:,.2f}")
        print(f"Total Return: {results['total_return_pct']:.2f}%")
        print(f"Buy & Hold Return: {results['buy_hold_return_pct']:.2f}%")
        print(f"\nSharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"\nTotal Trades: {results['total_trades']}")
        print(f"Remaining Cash: ${results['remaining_cash']:,.2f}")
        print(f"Active Positions: {results['active_positions']}")
        print("\n" + "="*60)

        # Print trades
        if not results['trades'].empty:
            print("\nTrades:")
            print(results['trades'].to_string())
