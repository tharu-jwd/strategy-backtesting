# Strategy Backtester

A simple, lightweight backtesting engine for testing trading strategies on historical market data. Designed to work with data from the [stock-data-pipeline](https://github.com/tharu-jwd/stock-data-pipeline) project through a shared PostgreSQL database.

## Overview

This backtesting engine allows you to:
- Define custom trading strategies
- Test strategies on historical stock data
- Track portfolio performance and P&L
- Calculate key performance metrics (returns, Sharpe ratio, drawdown)
- Simulate realistic trading with commissions and position sizing

## Features

- **Strategy Framework**: Simple base class for implementing custom strategies
- **Portfolio Simulator**: Realistic position tracking with cash management
- **Performance Metrics**: Returns, Sharpe ratio, maximum drawdown, trade analysis
- **Flexible Configuration**: Customizable capital, commission, position sizing
- **Database Integration**: Direct access to pipeline data via shared PostgreSQL

## Prerequisites

1. **Python 3.11+** installed
2. **stock-data-pipeline running**: The PostgreSQL database must be running with data
   ```bash
   cd ../stock-data-pipeline
   docker-compose up -d postgres
   ```

## Installation

1. **Navigate to the project directory**
   ```bash
   cd strategy-backtester
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   The default settings should work if your pipeline is using the standard configuration:
   ```env
   POSTGRES_USER=fintech
   POSTGRES_PASSWORD=fintech123
   POSTGRES_DB=stock_data
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

## Project Structure

```
strategy-backtester/
├── src/
│   ├── data/
│   │   └── database.py              # Database connection for market data
│   ├── strategies/
│   │   ├── base_strategy.py         # Abstract strategy base class
│   │   └── moving_average_strategy.py  # Example MA crossover strategy
│   ├── backtesting/
│   │   ├── portfolio.py             # Portfolio simulator with P&L tracking
│   │   └── backtest_engine.py       # Main backtesting orchestrator
│   └── utils/
│       ├── config.py                # Configuration management
│       └── logger.py                # Logging utilities
├── examples/
│   └── simple_backtest.py           # Example backtest script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## Quick Start

### Run the Example Backtest

```bash
# Activate virtual environment
source venv/bin/activate

# Run example backtest
python examples/simple_backtest.py
```

This will run a Moving Average Crossover strategy on AAPL for 2024 and display results.

### Expected Output

```
============================================================
BACKTEST RESULTS
============================================================

Ticker: AAPL
Period: 2024-01-01 to 2024-12-31
Strategy: Moving Average Crossover({'short_window': 20, 'long_window': 50})

Initial Capital: $100,000.00
Final Value: $105,234.50
Total Return: 5.23%
Buy & Hold Return: 8.45%

Sharpe Ratio: 0.85
Max Drawdown: -12.34%

Total Trades: 8
Remaining Cash: $12,450.00
Active Positions: 0
============================================================
```

## Usage

### Basic Backtest

```python
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.moving_average_strategy import MovingAverageCrossover

# Create strategy
strategy = MovingAverageCrossover(short_window=20, long_window=50)

# Create backtest engine
engine = BacktestEngine(
    strategy=strategy,
    initial_capital=100000.0,
    commission=1.0,
    position_size=0.95
)

# Run backtest
results = engine.run(
    ticker='AAPL',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Display results
engine.print_results(results)
```

### Creating Custom Strategies

Inherit from `BaseStrategy` and implement the `generate_signals` method:

```python
from src.strategies.base_strategy import BaseStrategy, Signal
import pandas as pd

class MyStrategy(BaseStrategy):
    """My custom trading strategy."""

    def __init__(self, param1=10):
        super().__init__(name="My Strategy")
        self.param1 = param1
        self.set_parameters(param1=param1)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Args:
            data: DataFrame with columns: open, high, low, close, volume
                  Index is the date

        Returns:
            Series with signals: 1 (BUY), -1 (SELL), 0 (HOLD)
        """
        signals = pd.Series(Signal.HOLD.value, index=data.index)

        # Your strategy logic here
        # Example: Buy when close > 20-day MA
        ma = data['close'].rolling(window=self.param1).mean()

        for i in range(1, len(data)):
            if data['close'].iloc[i] > ma.iloc[i]:
                signals.iloc[i] = Signal.BUY.value
            else:
                signals.iloc[i] = Signal.SELL.value

        return signals
```

### Accessing Market Data Directly

```python
from src.data.database import MarketDataDB

# Connect to database
db = MarketDataDB()
db.connect()

# Get stock data
data = db.get_stock_data('AAPL', '2024-01-01', '2024-12-31')
print(data.head())

# Get available tickers
tickers = db.get_available_tickers()
print(f"Available tickers: {tickers}")

# Get date range for a ticker
date_range = db.get_date_range('AAPL')
print(date_range)

# Close connection
db.close()
```

### Analyzing Results

```python
# Run backtest
results = engine.run('AAPL', '2024-01-01', '2024-12-31')

# Access equity curve
equity_curve = results['equity_curve']
print(equity_curve.head())

# Access all trades
trades = results['trades']
print(f"Total trades: {len(trades)}")
print(trades)

# Access performance metrics
print(f"Total Return: {results['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")

# Export equity curve
equity_curve.to_csv('equity_curve.csv')
```

## Configuration

### Backtest Parameters

- **initial_capital**: Starting portfolio value (default: $100,000)
- **commission**: Cost per trade in dollars (default: $0)
- **position_size**: Fraction of portfolio to use per trade, 0.0-1.0 (default: 1.0)

```python
engine = BacktestEngine(
    strategy=my_strategy,
    initial_capital=50000.0,   # Start with $50k
    commission=5.0,             # $5 per trade
    position_size=0.5           # Use 50% of cash per trade
)
```

### Strategy Parameters

Pass parameters when creating strategy instances:

```python
strategy = MovingAverageCrossover(
    short_window=10,   # Faster signals
    long_window=30     # Shorter long window
)
```

## Performance Metrics

The backtesting engine calculates:

- **Total Return**: Overall percentage gain/loss
- **Buy & Hold Return**: Comparison to passive strategy
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Total Trades**: Number of buy/sell executions

## How It Works

### Data Flow

1. **Pipeline** fetches data from Polygon.io → stores in PostgreSQL
2. **Backtester** reads from same PostgreSQL database
3. Strategy generates signals based on historical data
4. Portfolio simulator executes trades and tracks P&L
5. Results are calculated and returned

### Architecture

```
┌─────────────────┐
│ stock-data-     │
│ pipeline        │
└────────┬────────┘
         │
         ▼
   ┌──────────┐
   │PostgreSQL│◄──────┐
   │ Database │       │
   └──────────┘       │
                      │
              ┌───────┴────────┐
              │ Backtester     │
              │ ┌────────────┐ │
              │ │MarketDataDB│ │
              │ └─────┬──────┘ │
              │       │        │
              │   ┌───▼─────┐  │
              │   │Strategy │  │
              │   └───┬─────┘  │
              │       │        │
              │  ┌────▼─────┐  │
              │  │Portfolio │  │
              │  └──────────┘  │
              └────────────────┘
```

## Troubleshooting

### "No data available" Error

**Cause**: Pipeline database is empty or doesn't have the requested ticker/date range.

**Solution**:
```bash
# Check what data is available
cd ../stock-data-pipeline
docker-compose exec app python -c "
from src.query.data_retriever import StockDataRetriever
retriever = StockDataRetriever()
print('Available tickers:', retriever.get_available_tickers())
print('Date range for AAPL:', retriever.get_date_range('AAPL'))
"

# Run pipeline to fetch data if needed
docker-compose exec app python -m src.main --tickers AAPL --start-date 2024-01-01 --end-date 2024-12-31
```

### Database Connection Error

**Cause**: PostgreSQL container not running or wrong credentials.

**Solution**:
```bash
# Check if database container is running
cd ../stock-data-pipeline
docker-compose ps postgres

# Start database if not running
docker-compose up -d postgres

# Verify .env settings match pipeline configuration
cat .env
```

### "Insufficient data" Error

**Cause**: Strategy requires more data points than available (e.g., 200-day MA needs 200+ days).

**Solution**:
- Increase date range in backtest
- Reduce strategy window parameters
- Fetch more historical data via pipeline

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests (when available)
pytest
```

### Adding New Strategies

1. Create new file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `generate_signals()` method
4. Test with example backtest script

## Roadmap

- [ ] Multi-asset backtesting (portfolios with multiple stocks)
- [ ] Advanced metrics (Sortino ratio, Calmar ratio, win rate)
- [ ] Strategy optimization (parameter grid search)
- [ ] Visualization (equity curves, drawdown charts)
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Export results to various formats

## License

MIT License

## Related Projects

- [stock-data-pipeline](https://github.com/tharu-jwd/stock-data-pipeline) - Data pipeline for market data collection

