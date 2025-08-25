"""Market data activities using broker abstraction."""
from temporalio import activity
from typing import Dict, Any, List
from brokers.factory import BrokerFactory
from config.broker_config import BrokerConfigManager
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

# Create market data provider
market_data_provider = BrokerFactory.create_market_data_provider(
    broker_config.name,
    broker_config.market_data_config
)


@activity.defn
async def FetchStockPrice(symbol: str) -> Dict[str, Any]:
    """Fetch current stock price from configured broker."""
    try:
        quote = await market_data_provider.get_quote(symbol)
        
        return {
            "success": True,
            "symbol": quote.symbol,
            "price": quote.price,
            "bid": quote.bid,
            "ask": quote.ask,
            "volume": quote.volume,
            "timestamp": quote.timestamp.isoformat(),
            "exchange": quote.exchange
        }
    except Exception as e:
        logger.error(f"Failed to fetch stock price for {symbol}: {str(e)}")
        raise


@activity.defn
async def FetchMultipleStockPrices(symbols: List[str]) -> Dict[str, Any]:
    """Fetch current stock prices for multiple symbols from configured broker."""
    try:
        quotes = await market_data_provider.get_quotes(symbols)
        
        quote_data = []
        for quote in quotes:
            quote_data.append({
                "symbol": quote.symbol,
                "price": quote.price,
                "bid": quote.bid,
                "ask": quote.ask,
                "volume": quote.volume,
                "timestamp": quote.timestamp.isoformat(),
                "exchange": quote.exchange
            })
        
        return {
            "success": True,
            "quotes": quote_data,
            "total_symbols": len(symbols),
            "successful_fetches": len(quotes),
            "failed_fetches": len(symbols) - len(quotes)
        }
    except Exception as e:
        logger.error(f"Failed to fetch stock prices for {symbols}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbols": symbols,
            "total_symbols": len(symbols)
        }


@activity.defn
async def ValidateStockSymbol(symbol: str) -> Dict[str, Any]:
    """Validate if stock symbol exists using configured broker."""
    try:
        is_valid = await market_data_provider.validate_symbol(symbol)
        return {
            "success": True,
            "symbol": symbol,
            "valid": is_valid
        }
    except Exception as e:
        logger.error(f"Failed to validate symbol {symbol}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


@activity.defn
async def SearchStockSymbols(query: str) -> Dict[str, Any]:
    """Search for stock symbols matching query using configured broker."""
    try:
        results = await market_data_provider.search_symbols(query)
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Failed to search symbols for '{query}': {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


@activity.defn
async def FetchHistoricalData(
    symbol: str, 
    start_date: str, 
    end_date: str, 
    timeframe: str = "1Day"
) -> Dict[str, Any]:
    """Get historical price data using configured broker."""
    try:
        from datetime import datetime
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        bars = await market_data_provider.get_historical_data(
            symbol, start_dt, end_dt, timeframe
        )
        
        bars_data = []
        for bar in bars:
            bars_data.append({
                "symbol": bar.symbol,
                "timestamp": bar.timestamp.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            })
        
        return {
            "success": True,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "timeframe": timeframe,
            "bars": bars_data,
            "total_bars": len(bars_data)
        }
    except Exception as e:
        logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "timeframe": timeframe
        }