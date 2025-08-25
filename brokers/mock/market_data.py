"""Mock market data provider for testing."""
from interfaces.market_data import IMarketDataProvider, Quote, HistoricalBar
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random


class MockMarketDataProvider(IMarketDataProvider):
    """Mock implementation for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2800.0,
            "MSFT": 300.0,
            "TSLA": 800.0,
            "AMZN": 3200.0,
            "NVDA": 450.0,
            "META": 280.0,
            "NFLX": 400.0,
        }
    
    async def get_quote(self, symbol: str) -> Quote:
        """Generate mock quote."""
        if symbol not in self.base_prices:
            raise Exception(f"Symbol {symbol} not found")
        
        base_price = self.base_prices[symbol]
        variation = random.uniform(-0.02, 0.02)  # ±2% variation
        current_price = base_price * (1 + variation)
        
        return Quote(
            symbol=symbol,
            price=current_price,
            bid=current_price - 0.01,
            ask=current_price + 0.01,
            volume=random.randint(100000, 1000000),
            timestamp=datetime.now(),
            exchange="MOCK"
        )
    
    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Generate mock quotes for multiple symbols."""
        quotes = []
        for symbol in symbols:
            quotes.append(await self.get_quote(symbol))
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[HistoricalBar]:
        """Generate mock historical data."""
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
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.randint(100000, 1000000),
                timestamp=current_date
            ))
            
            current_date += timedelta(days=1)
            base_price = close_price  # Use previous close as next base
        
        return bars
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate mock symbol."""
        return symbol in self.base_prices
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search mock symbols."""
        results = []
        # Map of company names for better search
        company_names = {
            "AAPL": "Apple Inc.",
            "GOOGL": "Alphabet Inc.",
            "MSFT": "Microsoft Corporation",
            "TSLA": "Tesla Inc.",
            "AMZN": "Amazon.com Inc.",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms Inc.",
            "NFLX": "Netflix Inc.",
        }
        
        query_lower = query.lower()
        for symbol in self.base_prices.keys():
            company_name = company_names.get(symbol, f"{symbol} Corporation")
            # Search in both symbol and company name
            if (query_lower in symbol.lower() or 
                query_lower in company_name.lower()):
                results.append({
                    "symbol": symbol,
                    "name": company_name,
                    "exchange": "MOCK"
                })
        return results