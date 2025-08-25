# Broker Abstraction Layer Specification

## Overview
This specification defines a broker abstraction layer that allows easy replacement of Alpaca with other brokers (Interactive Brokers, TD Ameritrade, Schwab, etc.) without changing core business logic.

## Design Principles

1. **Interface Segregation**: Separate interfaces for different broker capabilities
2. **Dependency Inversion**: Core logic depends on abstractions, not concrete implementations
3. **Configuration-Driven**: Broker selection via configuration
4. **Extensibility**: Easy to add new broker implementations
5. **Testability**: Mock implementations for testing

## Core Abstractions

### 1. Market Data Interface

```python
# interfaces/market_data.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Quote:
    symbol: str
    bid_price: float
    ask_price: float
    last_price: float
    volume: int
    timestamp: datetime
    exchange: str

@dataclass
class HistoricalBar:
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    timestamp: datetime

class IMarketDataProvider(ABC):
    """Interface for market data operations"""
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Get current quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get current quotes for multiple symbols"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[HistoricalBar]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists and is tradeable"""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols matching query"""
        pass
```

### 2. Trading Interface

```python
# interfaces/trading.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: int
    filled_price: Optional[float]
    created_at: datetime
    updated_at: datetime

@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    side: str  # "long" or "short"

@dataclass
class Account:
    id: str
    cash: float
    buying_power: float
    portfolio_value: float
    day_trade_count: int
    is_pattern_day_trader: bool

class ITradingProvider(ABC):
    """Interface for trading operations"""
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "day"
    ) -> Order:
        """Place a trading order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order details"""
        pass
    
    @abstractmethod
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None
    ) -> List[Order]:
        """Get list of orders"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        pass
    
    @abstractmethod
    async def get_account(self) -> Account:
        """Get account information"""
        pass
```

### 3. Broker Factory

```python
# brokers/factory.py
from typing import Dict, Type
from interfaces.market_data import IMarketDataProvider
from interfaces.trading import ITradingProvider
from brokers.alpaca import AlpacaMarketDataProvider, AlpacaTradingProvider
from brokers.interactive_brokers import IBMarketDataProvider, IBTradingProvider
from brokers.mock import MockMarketDataProvider, MockTradingProvider

class BrokerFactory:
    """Factory for creating broker implementations"""
    
    _market_data_providers: Dict[str, Type[IMarketDataProvider]] = {
        "alpaca": AlpacaMarketDataProvider,
        "interactive_brokers": IBMarketDataProvider,
        "mock": MockMarketDataProvider,
    }
    
    _trading_providers: Dict[str, Type[ITradingProvider]] = {
        "alpaca": AlpacaTradingProvider,
        "interactive_brokers": IBTradingProvider,
        "mock": MockTradingProvider,
    }
    
    @classmethod
    def create_market_data_provider(
        cls, 
        broker_name: str, 
        config: Dict[str, Any]
    ) -> IMarketDataProvider:
        """Create market data provider instance"""
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
        """Create trading provider instance"""
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
        """Register new market data provider"""
        cls._market_data_providers[name] = provider_class
    
    @classmethod
    def register_trading_provider(
        cls, 
        name: str, 
        provider_class: Type[ITradingProvider]
    ):
        """Register new trading provider"""
        cls._trading_providers[name] = provider_class
```

### 4. Configuration Management

```python
# config/broker_config.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

@dataclass
class BrokerConfig:
    """Broker configuration"""
    name: str
    market_data_config: Dict[str, Any]
    trading_config: Dict[str, Any]
    paper_trading: bool = True
    rate_limit_requests_per_minute: int = 200
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

class BrokerConfigManager:
    """Manages broker configurations"""
    
    @staticmethod
    def get_alpaca_config() -> BrokerConfig:
        """Get Alpaca configuration from environment"""
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
        """Get Interactive Brokers configuration"""
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
        """Get mock broker configuration for testing"""
        return BrokerConfig(
            name="mock",
            market_data_config={},
            trading_config={},
            paper_trading=True
        )
```

## Broker Implementations

### 1. Alpaca Implementation

```python
# brokers/alpaca/market_data.py
from interfaces.market_data import IMarketDataProvider, Quote, HistoricalBar
from typing import Dict, List, Any
from datetime import datetime
import alpaca_trade_api as tradeapi

class AlpacaMarketDataProvider(IMarketDataProvider):
    """Alpaca implementation of market data interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api = tradeapi.REST(
            config["api_key"],
            config["secret_key"],
            config["base_url"]
        )
    
    async def get_quote(self, symbol: str) -> Quote:
        """Get current quote from Alpaca"""
        try:
            quote_data = self.api.get_latest_quote(symbol)
            return Quote(
                symbol=symbol,
                bid_price=quote_data.bid_price,
                ask_price=quote_data.ask_price,
                last_price=quote_data.ask_price,  # Use ask as last for simplicity
                volume=0,  # Alpaca doesn't provide volume in quote
                timestamp=quote_data.timestamp,
                exchange="ALPACA"
            )
        except Exception as e:
            raise Exception(f"Failed to get quote for {symbol}: {str(e)}")
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get multiple quotes from Alpaca"""
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = await self.get_quote(symbol)
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[HistoricalBar]:
        """Get historical data from Alpaca"""
        try:
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start_date.isoformat(),
                end=end_date.isoformat()
            )
            
            return [
                HistoricalBar(
                    symbol=symbol,
                    open_price=bar.open,
                    high_price=bar.high,
                    low_price=bar.low,
                    close_price=bar.close,
                    volume=bar.volume,
                    timestamp=bar.timestamp
                )
                for bar in bars
            ]
        except Exception as e:
            raise Exception(f"Failed to get historical data for {symbol}: {str(e)}")
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate symbol with Alpaca"""
        try:
            self.api.get_asset(symbol)
            return True
        except:
            return False
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search symbols (simplified implementation)"""
        # Alpaca doesn't have a search API, so this is a basic implementation
        try:
            asset = self.api.get_asset(query.upper())
            return [{
                "symbol": asset.symbol,
                "name": asset.name,
                "exchange": asset.exchange
            }]
        except:
            return []
```

### 2. Mock Implementation for Testing

```python
# brokers/mock/market_data.py
from interfaces.market_data import IMarketDataProvider, Quote, HistoricalBar
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

class MockMarketDataProvider(IMarketDataProvider):
    """Mock implementation for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 300.0,
            "TSLA": 800.0,
        }
    
    async def get_quote(self, symbol: str) -> Quote:
        """Generate mock quote"""
        if symbol not in self.base_prices:
            raise Exception(f"Symbol {symbol} not found")
        
        base_price = self.base_prices[symbol]
        variation = random.uniform(-0.02, 0.02)  # ±2% variation
        current_price = base_price * (1 + variation)
        
        return Quote(
            symbol=symbol,
            bid_price=current_price - 0.01,
            ask_price=current_price + 0.01,
            last_price=current_price,
            volume=random.randint(100000, 1000000),
            timestamp=datetime.now(),
            exchange="MOCK"
        )
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Generate mock quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = await self.get_quote(symbol)
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[HistoricalBar]:
        """Generate mock historical data"""
        if symbol not in self.base_prices:
            raise Exception(f"Symbol {symbol} not found")
        
        bars = []
        current_date = start_date
        base_price = self.base_prices[symbol]
        
        while current_date <= end_date:
            variation = random.uniform(-0.05, 0.05)  # ±5% daily variation
            open_price = base_price * (1 + variation)
            high_price = open_price * (1 + random.uniform(0, 0.03))
            low_price = open_price * (1 - random.uniform(0, 0.03))
            close_price = open_price * (1 + random.uniform(-0.02, 0.02))
            
            bars.append(HistoricalBar(
                symbol=symbol,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=random.randint(100000, 1000000),
                timestamp=current_date
            ))
            
            current_date += timedelta(days=1)
            base_price = close_price  # Use previous close as next base
        
        return bars
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate mock symbol"""
        return symbol in self.base_prices
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search mock symbols"""
        results = []
        for symbol in self.base_prices.keys():
            if query.upper() in symbol:
                results.append({
                    "symbol": symbol,
                    "name": f"{symbol} Corporation",
                    "exchange": "MOCK"
                })
        return results
```

## Updated Activity Implementations

### 1. Market Data Activities

```python
# activities/market_data.py
from temporalio import activity
from typing import Dict, List, Any
from datetime import datetime
from brokers.factory import BrokerFactory
from config.broker_config import BrokerConfigManager
import os

# Get broker configuration
BROKER_NAME = os.getenv("BROKER_NAME", "alpaca")
config_manager = BrokerConfigManager()

if BROKER_NAME == "alpaca":
    broker_config = config_manager.get_alpaca_config()
elif BROKER_NAME == "interactive_brokers":
    broker_config = config_manager.get_interactive_brokers_config()
else:
    broker_config = config_manager.get_mock_config()

# Create market data provider
market_data_provider = BrokerFactory.create_market_data_provider(
    broker_config.name,
    broker_config.market_data_config
)

@activity.defn
async def FetchStockPrice(symbol: str) -> Dict[str, Any]:
    """Fetch current stock price using configured broker"""
    try:
        quote = await market_data_provider.get_quote(symbol)
        return {
            "success": True,
            "symbol": quote.symbol,
            "price": quote.last_price,
            "bid": quote.bid_price,
            "ask": quote.ask_price,
            "volume": quote.volume,
            "timestamp": quote.timestamp.isoformat(),
            "exchange": quote.exchange
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }

@activity.defn
async def FetchMultipleStockPrices(symbols: List[str]) -> Dict[str, Any]:
    """Fetch prices for multiple stocks"""
    try:
        quotes = await market_data_provider.get_quotes(symbols)
        return {
            "success": True,
            "quotes": {
                symbol: {
                    "price": quote.last_price,
                    "bid": quote.bid_price,
                    "ask": quote.ask_price,
                    "volume": quote.volume,
                    "timestamp": quote.timestamp.isoformat()
                }
                for symbol, quote in quotes.items()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbols": symbols
        }

@activity.defn
async def ValidateStockSymbol(symbol: str) -> Dict[str, Any]:
    """Validate if stock symbol exists"""
    try:
        is_valid = await market_data_provider.validate_symbol(symbol)
        return {
            "success": True,
            "symbol": symbol,
            "is_valid": is_valid
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }
```

### 2. Trading Activities

```python
# activities/trading.py
from temporalio import activity
from typing import Dict, Any, Optional
from brokers.factory import BrokerFactory
from config.broker_config import BrokerConfigManager
from interfaces.trading import OrderSide, OrderType
import os

# Get broker configuration
BROKER_NAME = os.getenv("BROKER_NAME", "alpaca")
config_manager = BrokerConfigManager()

if BROKER_NAME == "alpaca":
    broker_config = config_manager.get_alpaca_config()
elif BROKER_NAME == "interactive_brokers":
    broker_config = config_manager.get_interactive_brokers_config()
else:
    broker_config = config_manager.get_mock_config()

# Create trading provider
trading_provider = BrokerFactory.create_trading_provider(
    broker_config.name,
    broker_config.trading_config
)

@activity.defn
async def PlaceOrder(
    symbol: str,
    side: str,
    order_type: str,
    quantity: int,
    price: Optional[float] = None
) -> Dict[str, Any]:
    """Place trading order using configured broker"""
    try:
        order = await trading_provider.place_order(
            symbol=symbol,
            side=OrderSide(side),
            order_type=OrderType(order_type),
            quantity=quantity,
            price=price
        )
        
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "status": order.status.value,
            "created_at": order.created_at.isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol,
            "side": side,
            "quantity": quantity
        }

@activity.defn
async def GetPortfolioStatus() -> Dict[str, Any]:
    """Get current portfolio status"""
    try:
        account = await trading_provider.get_account()
        positions = await trading_provider.get_positions()
        
        return {
            "success": True,
            "account": {
                "cash": account.cash,
                "buying_power": account.buying_power,
                "portfolio_value": account.portfolio_value
            },
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl
                }
                for pos in positions
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Updated Test Specifications

### 1. Broker Abstraction Tests

```python
# tests/test_broker_abstraction.py
import pytest
from brokers.factory import BrokerFactory
from interfaces.market_data import IMarketDataProvider
from interfaces.trading import ITradingProvider

class TestBrokerFactory:
    """Test broker factory functionality"""
    
    def test_create_alpaca_market_data_provider(self):
        """Test creation of Alpaca market data provider"""
        config = {"api_key": "test", "secret_key": "test", "base_url": "test"}
        provider = BrokerFactory.create_market_data_provider("alpaca", config)
        assert isinstance(provider, IMarketDataProvider)
    
    def test_create_mock_market_data_provider(self):
        """Test creation of mock market data provider"""
        provider = BrokerFactory.create_market_data_provider("mock", {})
        assert isinstance(provider, IMarketDataProvider)
    
    def test_unknown_broker_raises_error(self):
        """Test that unknown broker raises error"""
        with pytest.raises(ValueError, match="Unknown broker"):
            BrokerFactory.create_market_data_provider("unknown", {})
    
    def test_register_custom_provider(self):
        """Test registering custom provider"""
        from brokers.mock.market_data import MockMarketDataProvider
        
        BrokerFactory.register_market_data_provider("custom", MockMarketDataProvider)
        provider = BrokerFactory.create_market_data_provider("custom", {})
        assert isinstance(provider, IMarketDataProvider)
```

### 2. Updated Activity Tests

```python
# tests/activities/test_market_data_abstracted.py
import pytest
from unittest.mock import patch, AsyncMock
from activities.market_data import FetchStockPrice, ValidateStockSymbol
from interfaces.market_data import Quote
from datetime import datetime

class TestMarketDataActivities:
    """Test market data activities with broker abstraction"""
    
    @patch('activities.market_data.market_data_provider')
    async def test_fetch_stock_price_success(self, mock_provider):
        """Test successful stock price fetch with any broker"""
        # Arrange
        mock_quote = Quote(
            symbol="AAPL",
            bid_price=149.99,
            ask_price=150.01,
            last_price=150.00,
            volume=1000000,
            timestamp=datetime.now(),
            exchange="TEST"
        )
        mock_provider.get_quote = AsyncMock(return_value=mock_quote)
        
        # Act
        result = await FetchStockPrice("AAPL")
        
        # Assert
        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.00
        mock_provider.get_quote.assert_called_once_with("AAPL")
    
    @patch('activities.market_data.market_data_provider')
    async def test_fetch_stock_price_broker_error(self, mock_provider):
        """Test handling of broker-specific errors"""
        # Arrange
        mock_provider.get_quote = AsyncMock(side_effect=Exception("Broker API error"))
        
        # Act
        result = await FetchStockPrice("INVALID")
        
        # Assert
        assert result["success"] is False
        assert "Broker API error" in result["error"]
        assert result["symbol"] == "INVALID"
    
    @patch('activities.market_data.market_data_provider')
    async def test_validate_symbol_with_different_brokers(self, mock_provider):
        """Test symbol validation works with any broker"""
        # Arrange
        mock_provider.validate_symbol = AsyncMock(return_value=True)
        
        # Act
        result = await ValidateStockSymbol("AAPL")
        
        # Assert
        assert result["success"] is True
        assert result["is_valid"] is True
        mock_provider.validate_symbol.assert_called_once_with("AAPL")
```

## Migration Strategy

### Phase 1: Create Abstraction Layer
1. Create interface definitions
2. Implement broker factory
3. Create configuration management
4. Add mock implementations for testing

### Phase 2: Implement Alpaca Adapter
1. Create Alpaca market data provider
2. Create Alpaca trading provider
3. Update existing activities to use abstraction
4. Update tests to use mock providers

### Phase 3: Add Additional Brokers
1. Implement Interactive Brokers adapter
2. Implement TD Ameritrade adapter
3. Add broker-specific configuration
4. Add broker-specific tests

### Phase 4: Update All Specifications
1. Update all slice specifications to use abstraction
2. Remove Alpaca-specific references
3. Add broker selection tests
4. Update architecture patterns

## Configuration Examples

### Environment Variables
```bash
# Broker Selection
BROKER_NAME=alpaca  # or "interactive_brokers", "mock"

# Alpaca Configuration
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_PAPER_TRADING=true

# Interactive Brokers Configuration
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
IB_PAPER_TRADING=true
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  trading-system:
    build: .
    environment:
      - BROKER_NAME=alpaca
      - ALPACA_API_KEY=${ALPACA_API_KEY}
      - ALPACA_SECRET_KEY=${ALPACA_SECRET_KEY}
      - ALPACA_PAPER_TRADING=true
    # ... other configuration
```

## Benefits of This Abstraction

1. **Easy Broker Switching**: Change `BROKER_NAME` environment variable
2. **Testability**: Use mock implementations for testing
3. **Extensibility**: Add new brokers without changing core logic
4. **Consistency**: Unified interface across all brokers
5. **Configuration-Driven**: No code changes needed for broker switching
6. **Error Handling**: Consistent error handling across brokers
7. **Type Safety**: Strong typing with interfaces and data classes

## Summary

This broker abstraction layer provides:
- Clean separation between business logic and broker-specific code
- Easy replacement of Alpaca with other brokers
- Consistent interfaces for market data and trading operations
- Configuration-driven broker selection
- Comprehensive testing with mock implementations
- Type-safe implementations with proper error handling

The abstraction ensures that the core trading system logic remains unchanged when switching brokers, making the system truly broker-agnostic.