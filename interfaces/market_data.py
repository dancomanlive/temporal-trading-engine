"""Market data interface for broker abstraction."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Quote:
    """Stock quote data structure."""
    symbol: str
    price: float  # Last traded price
    bid: float    # Bid price
    ask: float    # Ask price
    volume: int
    timestamp: datetime
    exchange: str = "MOCK"


@dataclass
class HistoricalBar:
    """Historical price bar data structure."""
    symbol: str
    open: float   # Opening price
    high: float   # High price
    low: float    # Low price
    close: float  # Closing price
    volume: int
    timestamp: datetime


class IMarketDataProvider(ABC):
    """Interface for market data operations."""
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Get current quote for a symbol."""
        pass
    
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Get current quotes for multiple symbols."""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1Day"
    ) -> List[HistoricalBar]:
        """Get historical price data."""
        pass
    
    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists and is tradeable."""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols matching query."""
        pass