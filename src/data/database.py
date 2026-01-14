"""Database connection for reading market data from the pipeline."""

import psycopg2
from typing import Optional, List
import pandas as pd
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketDataDB:
    """Read-only database interface for accessing pipeline market data."""

    def __init__(self):
        """Initialize the MarketDataDB."""
        self.logger = logger
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                database=config.POSTGRES_DB
            )
            self.cursor = self.connection.cursor()
            self.logger.info("Database connection established")

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Retrieve historical stock data for backtesting.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume, adjusted_close
        """
        query = """
            SELECT date, open, high, low, close, volume, adjusted_close
            FROM stock_prices
            WHERE ticker = %s
                AND date >= %s
                AND date <= %s
            ORDER BY date
        """

        try:
            self.cursor.execute(query, (ticker, start_date, end_date))
            results = self.cursor.fetchall()

            if not results:
                self.logger.warning(f"No data found for {ticker} between {start_date} and {end_date}")
                return pd.DataFrame()

            df = pd.DataFrame(results, columns=[
                'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close'
            ])

            # Convert Decimal to float
            numeric_cols = ['open', 'high', 'low', 'close', 'adjusted_close']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(float)

            if 'volume' in df.columns:
                df['volume'] = df['volume'].astype(int)

            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            self.logger.info(f"Retrieved {len(df)} rows for {ticker}")
            return df

        except Exception as e:
            self.logger.error(f"Error retrieving stock data: {str(e)}")
            return pd.DataFrame()

    def get_multiple_stocks(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Retrieve data for multiple stocks.

        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with multi-index (date, ticker) or columns per ticker
        """
        all_data = {}

        try:
            for ticker in tickers:
                df = self.get_stock_data(ticker, start_date, end_date)
                if not df.empty:
                    all_data[ticker] = df

            if not all_data:
                return pd.DataFrame()

            # Combine into single DataFrame with ticker as column level
            combined = pd.concat(all_data, axis=1, keys=all_data.keys())
            return combined

        except Exception as e:
            self.logger.error(f"Error retrieving multiple stocks: {str(e)}")
            return pd.DataFrame()

    def get_available_tickers(self) -> List[str]:
        """
        Get list of all available tickers in database.

        Returns:
            List of ticker symbols
        """
        try:
            query = "SELECT DISTINCT ticker FROM stock_prices ORDER BY ticker"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [row[0] for row in results]

        except Exception as e:
            self.logger.error(f"Error retrieving tickers: {str(e)}")
            return []

    def get_date_range(self, ticker: str) -> dict:
        """
        Get available date range for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with 'earliest' and 'latest' dates
        """
        try:
            query = """
                SELECT MIN(date) as earliest, MAX(date) as latest
                FROM stock_prices
                WHERE ticker = %s
            """
            self.cursor.execute(query, (ticker,))
            result = self.cursor.fetchone()

            if result and result[0]:
                return {
                    'ticker': ticker,
                    'earliest': str(result[0]),
                    'latest': str(result[1])
                }

            return {}

        except Exception as e:
            self.logger.error(f"Error getting date range: {str(e)}")
            return {}
