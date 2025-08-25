"""Trading interface for broker abstraction."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order data structure."""
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
    """Position data structure."""
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    side: str  # "long" or "short"


@dataclass
class Account:
    """Account data structure."""
    id: str
    cash: float
    buying_power: float
    portfolio_value: float
    day_trade_count: int
    is_pattern_day_trader: bool


class ITradingProvider(ABC):
    """Interface for trading operations."""
    
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
        """Place a trading order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order details."""
        pass
    
    @abstractmethod
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None
    ) -> List[Order]:
        """Get list of orders."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions."""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol."""
        pass
    
    @abstractmethod
    async def get_account(self) -> Account:
        """Get account information."""
        pass