"""Broker factory for creating broker implementations."""
from typing import Dict, Type, Any
from interfaces.market_data import IMarketDataProvider
from interfaces.trading import ITradingProvider
from brokers.mock.market_data import MockMarketDataProvider
from brokers.mock.trading import MockTradingProvider


class BrokerFactory:
    """Factory for creating broker implementations."""
    
    _market_data_providers: Dict[str, Type[IMarketDataProvider]] = {
        "mock": MockMarketDataProvider,
    }
    
    _trading_providers: Dict[str, Type[ITradingProvider]] = {
        "mock": MockTradingProvider,
    }
    
    @classmethod
    def create_market_data_provider(
        cls, 
        broker_name: str, 
        config: Dict[str, Any]
    ) -> IMarketDataProvider:
        """Create market data provider instance."""
        if broker_name not in cls._market_data_providers:
            raise ValueError(f"Unknown broker: {broker_name}")
        
        provider_class = cls._market_data_providers[broker_name]
        return provider_class(config)
    
    @classmethod
    def create_trading_provider(
        cls, 
        broker_name: str, 
        config: Dict[str, Any]
    ) -> ITradingProvider:
        """Create trading provider instance."""
        if broker_name not in cls._trading_providers:
            raise ValueError(f"Unknown broker: {broker_name}")
        
        provider_class = cls._trading_providers[broker_name]
        return provider_class(config)
    
    @classmethod
    def register_market_data_provider(
        cls, 
        name: str, 
        provider_class: Type[IMarketDataProvider]
    ):
        """Register new market data provider."""
        cls._market_data_providers[name] = provider_class
    
    @classmethod
    def register_trading_provider(
        cls, 
        name: str, 
        provider_class: Type[ITradingProvider]
    ):
        """Register new trading provider."""
        cls._trading_providers[name] = provider_class
    
    @classmethod
    def get_available_brokers(cls) -> Dict[str, Dict[str, bool]]:
        """Get list of available brokers and their capabilities."""
        brokers = {}
        all_broker_names = set(cls._market_data_providers.keys()) | set(cls._trading_providers.keys())
        
        for broker_name in all_broker_names:
            brokers[broker_name] = {
                "market_data": broker_name in cls._market_data_providers,
                "trading": broker_name in cls._trading_providers
            }
        
        return brokers