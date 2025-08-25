"""Broker configuration management."""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os


@dataclass
class BrokerConfig:
    """Broker configuration data structure."""
    name: str
    market_data_config: Dict[str, Any]
    trading_config: Dict[str, Any]
    paper_trading: bool = True
    rate_limit_requests_per_minute: int = 200
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


class BrokerConfigManager:
    """Manages broker configurations."""
    
    @staticmethod
    def get_alpaca_config() -> BrokerConfig:
        """Get Alpaca configuration from environment."""
        return BrokerConfig(
            name="alpaca",
            market_data_config={
                "api_key": os.getenv("ALPACA_API_KEY"),
                "secret_key": os.getenv("ALPACA_SECRET_KEY"),
                "base_url": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            },
            trading_config={
                "api_key": os.getenv("ALPACA_API_KEY"),
                "secret_key": os.getenv("ALPACA_SECRET_KEY"),
                "base_url": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            },
            paper_trading=os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"
        )
    
    @staticmethod
    def get_interactive_brokers_config() -> BrokerConfig:
        """Get Interactive Brokers configuration."""
        return BrokerConfig(
            name="interactive_brokers",
            market_data_config={
                "host": os.getenv("IB_HOST", "127.0.0.1"),
                "port": int(os.getenv("IB_PORT", "7497")),
                "client_id": int(os.getenv("IB_CLIENT_ID", "1")),
            },
            trading_config={
                "host": os.getenv("IB_HOST", "127.0.0.1"),
                "port": int(os.getenv("IB_PORT", "7497")),
                "client_id": int(os.getenv("IB_CLIENT_ID", "1")),
            },
            paper_trading=os.getenv("IB_PAPER_TRADING", "true").lower() == "true"
        )
    
    @staticmethod
    def get_mock_config() -> BrokerConfig:
        """Get mock broker configuration for testing."""
        return BrokerConfig(
            name="mock",
            market_data_config={},
            trading_config={},
            paper_trading=True
        )
    
    @staticmethod
    def get_config_by_name(broker_name: str) -> BrokerConfig:
        """Get configuration by broker name."""
        if broker_name == "alpaca":
            return BrokerConfigManager.get_alpaca_config()
        elif broker_name == "interactive_brokers":
            return BrokerConfigManager.get_interactive_brokers_config()
        elif broker_name == "mock":
            return BrokerConfigManager.get_mock_config()
        else:
            raise ValueError(f"Unknown broker: {broker_name}")