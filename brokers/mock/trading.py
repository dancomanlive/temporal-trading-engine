"""Mock trading provider for testing."""
from interfaces.trading import (
    ITradingProvider, Order, Position, Account,
    OrderType, OrderSide, OrderStatus
)
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import random


class MockTradingProvider(ITradingProvider):
    """Mock implementation for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.account = Account(
            id="mock_account_123",
            cash=100000.0,
            buying_power=200000.0,
            portfolio_value=100000.0,
            day_trade_count=0,
            is_pattern_day_trader=False
        )
        
        # Mock stock prices for position calculations
        self.stock_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 300.0,
            "TSLA": 800.0,
            "AMZN": 3200.0,
            "NVDA": 450.0,
            "META": 280.0,
            "NFLX": 400.0,
        }
        
        # Initialize some default positions for testing
        self.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            avg_cost=145.0,
            market_value=15000.0,
            unrealized_pnl=500.0,
            side="long"
        )
        self.positions["GOOGL"] = Position(
            symbol="GOOGL",
            quantity=10,
            avg_cost=2750.0,
            market_value=28000.0,
            unrealized_pnl=500.0,
            side="long"
        )
    
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
        """Place a mock trading order."""
        order_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Simulate order execution for market orders
        if order_type == OrderType.MARKET:
            status = OrderStatus.FILLED
            filled_quantity = quantity
            filled_price = self.stock_prices.get(symbol, 100.0)
        else:
            # Limit orders start as pending
            status = OrderStatus.PENDING
            filled_quantity = 0
            filled_price = None
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=status,
            filled_quantity=filled_quantity,
            filled_price=filled_price,
            created_at=current_time,
            updated_at=current_time
        )
        
        self.orders[order_id] = order
        
        # Update positions for filled orders
        if status == OrderStatus.FILLED:
            await self._update_position(order)
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a mock order."""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        return True
    
    async def get_order(self, order_id: str) -> Order:
        """Get mock order details."""
        if order_id not in self.orders:
            raise Exception(f"Order {order_id} not found")
        return self.orders[order_id]
    
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None
    ) -> List[Order]:
        """Get list of mock orders."""
        orders = list(self.orders.values())
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        return orders
    
    async def get_positions(self) -> List[Position]:
        """Get current mock positions."""
        return list(self.positions.values())
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get mock position for specific symbol."""
        return self.positions.get(symbol)
    
    async def get_account(self) -> Account:
        """Get mock account information."""
        # Update portfolio value based on positions
        portfolio_value = self.account.cash
        for position in self.positions.values():
            portfolio_value += position.market_value
        
        self.account.portfolio_value = portfolio_value
        return self.account
    
    async def _update_position(self, order: Order):
        """Update position based on filled order."""
        symbol = order.symbol
        current_price = self.stock_prices.get(symbol, 100.0)
        
        if symbol not in self.positions:
            # Create new position
            if order.side == OrderSide.BUY:
                quantity = order.filled_quantity
                side = "long"
            else:
                quantity = -order.filled_quantity
                side = "short"
            
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=order.filled_price or current_price,
                market_value=abs(quantity) * current_price,
                unrealized_pnl=0.0,
                side=side
            )
        else:
            # Update existing position
            position = self.positions[symbol]
            
            if order.side == OrderSide.BUY:
                new_quantity = position.quantity + order.filled_quantity
            else:
                new_quantity = position.quantity - order.filled_quantity
            
            if new_quantity == 0:
                # Position closed
                del self.positions[symbol]
            else:
                # Update position
                position.quantity = new_quantity
                position.side = "long" if new_quantity > 0 else "short"
                position.market_value = abs(new_quantity) * current_price
                position.unrealized_pnl = (current_price - position.avg_cost) * new_quantity
        
        # Update account cash
        if order.side == OrderSide.BUY:
            self.account.cash -= order.filled_quantity * (order.filled_price or current_price)
        else:
            self.account.cash += order.filled_quantity * (order.filled_price or current_price)