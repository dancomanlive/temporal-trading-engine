"""Tests for broker abstraction layer."""
import pytest
import asyncio
from datetime import datetime, timedelta
from interfaces.market_data import IMarketDataProvider, Quote, HistoricalBar
from interfaces.trading import ITradingProvider, OrderSide, OrderType, OrderStatus
from brokers.mock.market_data import MockMarketDataProvider
from brokers.mock.trading import MockTradingProvider
from brokers.factory import BrokerFactory
from config.broker_config import BrokerConfigManager


class TestMockMarketDataProvider:
    """Test mock market data provider."""
    
    @pytest.fixture
    def provider(self):
        return MockMarketDataProvider({})
    
    @pytest.mark.asyncio
    async def test_get_quote(self, provider):
        """Test getting a single quote."""
        quote = await provider.get_quote("AAPL")
        
        assert isinstance(quote, Quote)
        assert quote.symbol == "AAPL"
        assert quote.price > 0
        assert quote.bid > 0
        assert quote.ask > 0
        assert quote.bid <= quote.price <= quote.ask
        assert isinstance(quote.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_get_quotes_multiple(self, provider):
        """Test getting multiple quotes."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        quotes = await provider.get_quotes(symbols)
        
        assert len(quotes) == len(symbols)
        for quote in quotes:
            assert isinstance(quote, Quote)
            assert quote.symbol in symbols
            assert quote.price > 0
    
    @pytest.mark.asyncio
    async def test_get_historical_data(self, provider):
        """Test getting historical data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        bars = await provider.get_historical_data(
            "AAPL", start_date, end_date, "1Day"
        )
        
        assert len(bars) > 0
        for bar in bars:
            assert isinstance(bar, HistoricalBar)
            assert bar.symbol == "AAPL"
            assert bar.open > 0
            assert bar.high >= bar.open
            assert bar.low <= bar.open
            assert bar.close > 0
            assert bar.volume >= 0
    
    @pytest.mark.asyncio
    async def test_validate_symbol(self, provider):
        """Test symbol validation."""
        # Valid symbols
        assert await provider.validate_symbol("AAPL") is True
        assert await provider.validate_symbol("GOOGL") is True
        
        # Invalid symbols
        assert await provider.validate_symbol("INVALID") is False
        assert await provider.validate_symbol("NOTREAL") is False
    
    @pytest.mark.asyncio
    async def test_search_symbols(self, provider):
        """Test symbol search."""
        results = await provider.search_symbols("Apple")
        
        assert len(results) > 0
        assert any(result["symbol"] == "AAPL" for result in results)
        
        # Test case insensitive search
        results_lower = await provider.search_symbols("apple")
        assert len(results_lower) > 0


class TestMockTradingProvider:
    """Test mock trading provider."""
    
    @pytest.fixture
    def provider(self):
        return MockTradingProvider({})
    
    @pytest.mark.asyncio
    async def test_place_order(self, provider):
        """Test placing an order."""
        order = await provider.place_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100
        assert order.status in [OrderStatus.PENDING, OrderStatus.FILLED]
        assert order.id is not None
    
    @pytest.mark.asyncio
    async def test_place_limit_order(self, provider):
        """Test placing a limit order."""
        order = await provider.place_order(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=150.0
        )
        
        assert order.order_type == OrderType.LIMIT
        assert order.price == 150.0
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, provider):
        """Test canceling an order."""
        # Place an order first
        order = await provider.place_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=140.0
        )
        
        # Cancel the order
        success = await provider.cancel_order(order.id)
        assert success is True
        
        # Get the order to verify it's cancelled
        cancelled_order = await provider.get_order(order.id)
        assert cancelled_order.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_orders(self, provider):
        """Test getting orders."""
        # Place a few orders
        await provider.place_order(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )
        await provider.place_order(
            symbol="GOOGL", side=OrderSide.SELL, order_type=OrderType.LIMIT, quantity=50, price=2500.0
        )
        
        # Get all orders
        orders = await provider.get_orders()
        assert len(orders) >= 2
        
        # Get orders for specific symbol
        aapl_orders = await provider.get_orders(symbol="AAPL")
        assert all(order.symbol == "AAPL" for order in aapl_orders)
    
    @pytest.mark.asyncio
    async def test_get_positions(self, provider):
        """Test getting positions."""
        positions = await provider.get_positions()
        assert isinstance(positions, list)
        # Mock provider should have some default positions
        assert len(positions) > 0
    
    @pytest.mark.asyncio
    async def test_get_account(self, provider):
        """Test getting account information."""
        account = await provider.get_account()
        
        assert account.id is not None
        assert account.cash >= 0
        assert account.buying_power >= 0
        assert account.portfolio_value >= 0
        assert isinstance(account.day_trade_count, int)
        assert isinstance(account.is_pattern_day_trader, bool)


class TestBrokerFactory:
    """Test broker factory."""
    
    def test_create_market_data_provider_mock(self):
        """Test creating mock market data provider."""
        provider = BrokerFactory.create_market_data_provider("mock", {})
        assert isinstance(provider, MockMarketDataProvider)
    
    def test_create_trading_provider_mock(self):
        """Test creating mock trading provider."""
        provider = BrokerFactory.create_trading_provider("mock", {})
        assert isinstance(provider, MockTradingProvider)
    
    def test_create_unknown_provider(self):
        """Test creating provider for unknown broker."""
        with pytest.raises(ValueError, match="Unknown broker"):
            BrokerFactory.create_market_data_provider("unknown", {})
        
        with pytest.raises(ValueError, match="Unknown broker"):
            BrokerFactory.create_trading_provider("unknown", {})


class TestBrokerConfigManager:
    """Test broker configuration manager."""
    
    def test_get_mock_config(self):
        """Test getting mock configuration."""
        config = BrokerConfigManager.get_mock_config()
        
        assert config.name == "mock"
        assert config.market_data_config == {}
        assert config.trading_config == {}
    
    def test_get_config_by_name_mock(self):
        """Test getting configuration by name."""
        config_manager = BrokerConfigManager()
        config = config_manager.get_config_by_name("mock")
        
        assert config.name == "mock"
    
    def test_get_config_by_name_unknown(self):
        """Test getting configuration for unknown broker."""
        config_manager = BrokerConfigManager()
        
        with pytest.raises(ValueError, match="Unknown broker"):
            config_manager.get_config_by_name("unknown")


class TestIntegration:
    """Integration tests for broker abstraction."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_market_data(self):
        """Test end-to-end market data flow."""
        # Get configuration
        config_manager = BrokerConfigManager()
        config = config_manager.get_mock_config()
        
        # Create provider
        provider = BrokerFactory.create_market_data_provider(
            config.name, config.market_data_config
        )
        
        # Test workflow
        symbol = "AAPL"
        
        # Validate symbol
        is_valid = await provider.validate_symbol(symbol)
        assert is_valid is True
        
        # Get quote
        quote = await provider.get_quote(symbol)
        assert quote.symbol == symbol
        assert quote.price > 0
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        bars = await provider.get_historical_data(symbol, start_date, end_date, "1Hour")
        assert len(bars) > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_trading(self):
        """Test end-to-end trading flow."""
        # Get configuration
        config_manager = BrokerConfigManager()
        config = config_manager.get_mock_config()
        
        # Create provider
        provider = BrokerFactory.create_trading_provider(
            config.name, config.trading_config
        )
        
        # Test workflow
        symbol = "AAPL"
        
        # Place order
        order = await provider.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )
        assert order.symbol == symbol
        
        # Get order status
        retrieved_order = await provider.get_order(order.id)
        assert retrieved_order.id == order.id
        
        # Get account info
        account = await provider.get_account()
        assert account.cash >= 0
        
        # Get positions
        positions = await provider.get_positions()
        assert isinstance(positions, list)


if __name__ == "__main__":
    pytest.main([__file__])