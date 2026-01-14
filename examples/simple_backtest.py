"""
Simple example of running a backtest with the Moving Average Crossover strategy.

This script demonstrates:
1. Loading data from the pipeline database
2. Configuring a strategy
3. Running a backtest
4. Viewing results
"""

import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.moving_average_strategy import MovingAverageCrossover


def main():
    """Run a simple backtest example."""

    # Configure strategy
    strategy = MovingAverageCrossover(
        short_window=20,  # 20-day moving average
        long_window=50    # 50-day moving average
    )

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,  # $100,000 starting capital
        commission=1.0,            # $1 per trade
        position_size=0.95         # Use 95% of available cash per trade
    )

    # Run backtest
    results = engine.run(
        ticker='AAPL',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    # Print results
    engine.print_results(results)

    # You can also access individual components:
    # print("\nEquity Curve:")
    # print(results['equity_curve'])

    # print("\nAll Trades:")
    # print(results['trades'])


if __name__ == '__main__':
    main()
