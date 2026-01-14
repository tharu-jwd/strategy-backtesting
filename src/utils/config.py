"""Configuration management for the backtesting engine."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Database configuration (shared with pipeline)
    POSTGRES_USER = os.getenv("POSTGRES_USER", "fintech")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "fintech123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "stock_data")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

    # Application configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
