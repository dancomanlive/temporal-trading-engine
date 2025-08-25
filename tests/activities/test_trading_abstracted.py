"""Tests for trading activities using broker abstraction."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime
from activities.trading import (
    PlaceOrder, CancelOrder, GetOrderStatus, GetAllOrders,
    GetPortfolioStatus, GetPosition
)
from interfaces.trading import (
    Order, Position, Account, OrderSide, OrderType, OrderStatus
)


class TestTradingActivities:
    """Test trading activities."""
    
    @pytest.mark.asyncio
    async def test_place_order_market_success(self):
        """Test successful market order placement."""
        mock_order = Order(
            id="order_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            price=None,
            stop_price=None,
            status=OrderStatus.FILLED,
            filled_quantity=100,
            filled_price=150.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.place_order = AsyncMock(return_value=mock_order)
            
            result = await PlaceOrder(
                symbol="AAPL",
                side="buy",
                order_type="market",
                quantity=100
            )
            
            assert result["success"] is True
            assert result["order_id"] == "order_123"
            assert result["symbol"] == "AAPL"
            assert result["side"] == "buy"
            assert result["order_type"] == "market"
            assert result["quantity"] == 100
            assert result["status"] == "filled"
            assert result["filled_quantity"] == 100
            assert result["filled_price"] == 150.0
    
    @pytest.mark.asyncio
    async def test_place_order_limit_success(self):
        """Test successful limit order placement."""
        mock_order = Order(
            id="order_456",
            symbol="GOOGL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=2500.0,
            stop_price=None,
            status=OrderStatus.PENDING,
            filled_quantity=0,
            filled_price=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.place_order = AsyncMock(return_value=mock_order)
            
            result = await PlaceOrder(
                symbol="GOOGL",
                side="sell",
                order_type="limit",
                quantity=50,
                price=2500.0
            )
            
            assert result["success"] is True
            assert result["order_id"] == "order_456"
            assert result["symbol"] == "GOOGL"
            assert result["side"] == "sell"
            assert result["order_type"] == "limit"
            assert result["quantity"] == 50
            assert result["price"] == 2500.0
            assert result["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_place_order_stop_loss(self):
        """Test stop loss order placement."""
        mock_order = Order(
            id="order_789",
            symbol="MSFT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=75,
            price=None,
            stop_price=300.0,
            status=OrderStatus.PENDING,
            filled_quantity=0,
            filled_price=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.place_order = AsyncMock(return_value=mock_order)
            
            result = await PlaceOrder(
                symbol="MSFT",
                side="sell",
                order_type="stop",
                quantity=75,
                stop_price=300.0
            )
            
            assert result["success"] is True
            assert result["stop_price"] == 300.0
            assert result["order_type"] == "stop"
    
    @pytest.mark.asyncio
    async def test_place_order_failure(self):
        """Test order placement failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.place_order = AsyncMock(side_effect=Exception("Insufficient funds"))
            
            result = await PlaceOrder(
                symbol="AAPL",
                side="buy",
                order_type="market",
                quantity=1000000  # Unrealistic quantity
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "Insufficient funds" in result["error"]
            assert result["symbol"] == "AAPL"
            assert result["side"] == "buy"
            assert result["quantity"] == 1000000
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self):
        """Test successful order cancellation."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.cancel_order = AsyncMock(return_value=True)
            
            result = await CancelOrder("order_123")
            
            assert result["success"] is True
            assert result["order_id"] == "order_123"
            assert result["cancelled"] is True
    
    @pytest.mark.asyncio
    async def test_cancel_order_failure(self):
        """Test order cancellation failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.cancel_order = AsyncMock(side_effect=Exception("Order not found"))
            
            result = await CancelOrder("invalid_order")
            
            assert result["success"] is False
            assert "error" in result
            assert "Order not found" in result["error"]
            assert result["order_id"] == "invalid_order"
    
    @pytest.mark.asyncio
    async def test_get_order_status_success(self):
        """Test successful order status retrieval."""
        mock_order = Order(
            id="order_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=145.0,
            stop_price=None,
            status=OrderStatus.PARTIALLY_FILLED,
            filled_quantity=50,
            filled_price=144.5,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_order = AsyncMock(return_value=mock_order)
            
            result = await GetOrderStatus("order_123")
            
            assert result["success"] is True
            assert result["order_id"] == "order_123"
            assert result["symbol"] == "AAPL"
            assert result["status"] == "partially_filled"
            assert result["filled_quantity"] == 50
            assert result["filled_price"] == 144.5
    
    @pytest.mark.asyncio
    async def test_get_order_status_failure(self):
        """Test order status retrieval failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_order = AsyncMock(side_effect=Exception("Order not found"))
            
            result = await GetOrderStatus("invalid_order")
            
            assert result["success"] is False
            assert "error" in result
            assert result["order_id"] == "invalid_order"
    
    @pytest.mark.asyncio
    async def test_get_all_orders_success(self):
        """Test successful retrieval of all orders."""
        mock_orders = [
            Order(
                id=f"order_{i}",
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
                price=None,
                stop_price=None,
                status=OrderStatus.FILLED,
                filled_quantity=100,
                filled_price=150.0 + i,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(3)
        ]
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_orders = AsyncMock(return_value=mock_orders)
            
            result = await GetAllOrders()
            
            assert result["success"] is True
            assert len(result["orders"]) == 3
            assert result["count"] == 3
            assert result["filter_status"] is None
            assert result["filter_symbol"] is None
            
            # Check first order
            first_order = result["orders"][0]
            assert first_order["order_id"] == "order_0"
            assert first_order["symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_get_all_orders_filtered(self):
        """Test retrieval of filtered orders."""
        mock_orders = []
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_orders = AsyncMock(return_value=mock_orders)
            
            result = await GetAllOrders(status="filled", symbol="AAPL")
            
            assert result["success"] is True
            assert result["orders"] == []
            assert result["count"] == 0
            assert result["filter_status"] == "filled"
            assert result["filter_symbol"] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_get_all_orders_failure(self):
        """Test orders retrieval failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_orders = AsyncMock(side_effect=Exception("API Error"))
            
            result = await GetAllOrders()
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio_status_success(self):
        """Test successful portfolio status retrieval."""
        mock_account = Account(
            id="account_123",
            cash=10000.0,
            buying_power=20000.0,
            portfolio_value=50000.0,
            day_trade_count=2,
            is_pattern_day_trader=False
        )
        
        mock_positions = [
            Position(
                symbol="AAPL",
                quantity=100,
                avg_cost=145.0,
                market_value=15000.0,
                unrealized_pnl=500.0,
                side="long"
            ),
            Position(
                symbol="GOOGL",
                quantity=25,
                avg_cost=2400.0,
                market_value=62500.0,
                unrealized_pnl=2500.0,
                side="long"
            )
        ]
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_account = AsyncMock(return_value=mock_account)
            mock_provider.get_positions = AsyncMock(return_value=mock_positions)
            
            result = await GetPortfolioStatus()
            
            assert result["success"] is True
            assert result["account"]["id"] == "account_123"
            assert result["account"]["cash"] == 10000.0
            assert result["account"]["buying_power"] == 20000.0
            assert result["account"]["portfolio_value"] == 50000.0
            assert len(result["positions"]) == 2
            assert result["total_positions"] == 2
            
            # Check first position
            first_position = result["positions"][0]
            assert first_position["symbol"] == "AAPL"
            assert first_position["quantity"] == 100
            assert first_position["unrealized_pnl"] == 500.0
    
    @pytest.mark.asyncio
    async def test_get_portfolio_status_failure(self):
        """Test portfolio status retrieval failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_account = AsyncMock(side_effect=Exception("Account access error"))
            
            result = await GetPortfolioStatus()
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_position_success(self):
        """Test successful position retrieval."""
        mock_position = Position(
            symbol="AAPL",
            quantity=100,
            avg_cost=145.0,
            market_value=15000.0,
            unrealized_pnl=500.0,
            side="long"
        )
        
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_position = AsyncMock(return_value=mock_position)
            
            result = await GetPosition("AAPL")
            
            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["quantity"] == 100
            assert result["avg_cost"] == 145.0
            assert result["market_value"] == 15000.0
            assert result["unrealized_pnl"] == 500.0
            assert result["side"] == "long"
            assert result["has_position"] is True
    
    @pytest.mark.asyncio
    async def test_get_position_no_position(self):
        """Test position retrieval when no position exists."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_position = AsyncMock(return_value=None)
            
            result = await GetPosition("TSLA")
            
            assert result["success"] is True
            assert result["symbol"] == "TSLA"
            assert result["has_position"] is False
    
    @pytest.mark.asyncio
    async def test_get_position_failure(self):
        """Test position retrieval failure."""
        with patch('activities.trading.trading_provider') as mock_provider:
            mock_provider.get_position = AsyncMock(side_effect=Exception("Position access error"))
            
            result = await GetPosition("AAPL")
            
            assert result["success"] is False
            assert "error" in result
            assert result["symbol"] == "AAPL"


if __name__ == "__main__":
    pytest.main([__file__])