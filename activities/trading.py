"""Trading activities using broker abstraction."""
from temporalio import activity
from typing import Dict, Any, Optional, List
from brokers.factory import BrokerFactory
from config.broker_config import BrokerConfigManager
from interfaces.trading import OrderSide, OrderType, OrderStatus
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get broker configuration
BROKER_NAME = os.getenv("BROKER_NAME", "mock")
config_manager = BrokerConfigManager()

try:
    broker_config = config_manager.get_config_by_name(BROKER_NAME)
except ValueError:
    logger.warning(f"Unknown broker '{BROKER_NAME}', falling back to mock")
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
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: str = "day"
) -> Dict[str, Any]:
    """Place trading order using configured broker."""
    try:
        order = await trading_provider.place_order(
            symbol=symbol,
            side=OrderSide(side),
            order_type=OrderType(order_type),
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force
        )
        
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": order.quantity,
            "price": order.price,
            "stop_price": order.stop_price,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "filled_price": order.filled_price,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to place order for {symbol}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol,
            "side": side,
            "quantity": quantity
        }


@activity.defn
async def CancelOrder(order_id: str) -> Dict[str, Any]:
    """Cancel trading order using configured broker."""
    try:
        success = await trading_provider.cancel_order(order_id)
        
        return {
            "success": success,
            "order_id": order_id,
            "cancelled": success
        }
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "order_id": order_id
        }


@activity.defn
async def GetOrderStatus(order_id: str) -> Dict[str, Any]:
    """Get order status using configured broker."""
    try:
        order = await trading_provider.get_order(order_id)
        
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": order.quantity,
            "price": order.price,
            "stop_price": order.stop_price,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "filled_price": order.filled_price,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get order status for {order_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "order_id": order_id
        }


@activity.defn
async def GetAllOrders(
    status: Optional[str] = None,
    symbol: Optional[str] = None
) -> Dict[str, Any]:
    """Get all orders using configured broker."""
    try:
        order_status = OrderStatus(status) if status else None
        orders = await trading_provider.get_orders(order_status, symbol)
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "order_id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": order.quantity,
                "price": order.price,
                "stop_price": order.stop_price,
                "status": order.status.value,
                "filled_quantity": order.filled_quantity,
                "filled_price": order.filled_price,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "orders": orders_data,
            "count": len(orders_data),
            "filter_status": status,
            "filter_symbol": symbol
        }
    except Exception as e:
        logger.error(f"Failed to get orders: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "filter_status": status,
            "filter_symbol": symbol
        }


@activity.defn
async def GetPortfolioStatus() -> Dict[str, Any]:
    """Get current portfolio status using configured broker."""
    try:
        account = await trading_provider.get_account()
        positions = await trading_provider.get_positions()
        
        positions_data = []
        for position in positions:
            positions_data.append({
                "symbol": position.symbol,
                "quantity": position.quantity,
                "avg_cost": position.avg_cost,
                "market_value": position.market_value,
                "unrealized_pnl": position.unrealized_pnl,
                "side": position.side
            })
        
        return {
            "success": True,
            "account": {
                "id": account.id,
                "cash": account.cash,
                "buying_power": account.buying_power,
                "portfolio_value": account.portfolio_value,
                "day_trade_count": account.day_trade_count,
                "is_pattern_day_trader": account.is_pattern_day_trader
            },
            "positions": positions_data,
            "total_positions": len(positions_data)
        }
    except Exception as e:
        logger.error(f"Failed to get portfolio status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def GetPosition(symbol: str) -> Dict[str, Any]:
    """Get position for specific symbol using configured broker."""
    try:
        position = await trading_provider.get_position(symbol)
        
        if position:
            return {
                "success": True,
                "symbol": position.symbol,
                "quantity": position.quantity,
                "avg_cost": position.avg_cost,
                "market_value": position.market_value,
                "unrealized_pnl": position.unrealized_pnl,
                "side": position.side,
                "has_position": True
            }
        else:
            return {
                "success": True,
                "symbol": symbol,
                "has_position": False
            }
    except Exception as e:
        logger.error(f"Failed to get position for {symbol}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }