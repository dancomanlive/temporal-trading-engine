"""Tests for market data activities using broker abstraction."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from activities.market_data import (
    FetchStockPrice, FetchMultipleStockPrices, ValidateStockSymbol,
    SearchStockSymbols, FetchHistoricalData
)
from interfaces.market_data import Quote, HistoricalBar
from datetime import datetime, timedelta


class TestMarketDataActivities:
    """Test market data activities."""
    
    @pytest.mark.asyncio
    async def test_fetch_stock_price_success(self):
        """Test successful stock price fetch."""
        # Mock the market data provider
        mock_quote = Quote(
            symbol="AAPL",
            price=150.0,
            bid=149.95,
            ask=150.05,
            volume=1000000,
            timestamp=datetime.now(),
            exchange="NASDAQ"
        )
        
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_quote = AsyncMock(return_value=mock_quote)
            
            result = await FetchStockPrice("AAPL")
            
            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["price"] == 150.0
            assert result["bid"] == 149.95
            assert result["ask"] == 150.05
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_fetch_stock_price_failure(self):
        """Test stock price fetch failure."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_quote = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception) as exc_info:
                await FetchStockPrice("INVALID")
            
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_stock_prices_success(self):
        """Test successful multiple stock prices fetch."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        mock_quotes = [
            Quote(symbol=symbol, price=100.0 + i * 50, bid=99.0 + i * 50, 
                  ask=101.0 + i * 50, volume=1000000 + i * 100000, 
                  timestamp=datetime.now(), exchange="NASDAQ")
            for i, symbol in enumerate(symbols)
        ]
        
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_quotes = AsyncMock(return_value=mock_quotes)
            
            result = await FetchMultipleStockPrices(symbols)
            
            assert result["success"] is True
            assert len(result["quotes"]) == 3
            assert result["total_symbols"] == 3
            assert result["successful_fetches"] == 3
            assert result["failed_fetches"] == 0
            
            for i, quote_data in enumerate(result["quotes"]):
                assert quote_data["symbol"] == symbols[i]
                assert quote_data["price"] == 100.0 + i * 50
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_stock_prices_partial_failure(self):
        """Test multiple stock prices fetch with some failures."""
        symbols = ["AAPL", "INVALID", "MSFT"]
        
        def mock_get_quotes(symbols_list):
            quotes = []
            for symbol in symbols_list:
                if symbol != "INVALID":
                    quotes.append(Quote(
                        symbol=symbol, price=150.0, bid=149.0, 
                        ask=151.0, volume=1000000, timestamp=datetime.now(),
                        exchange="NASDAQ"
                    ))
                else:
                    raise Exception(f"Invalid symbol: {symbol}")
            return quotes
        
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_quotes = AsyncMock(side_effect=mock_get_quotes)
            
            result = await FetchMultipleStockPrices(symbols)
            
            assert result["success"] is False
            assert "error" in result
            assert result["total_symbols"] == 3
    
    @pytest.mark.asyncio
    async def test_validate_stock_symbol_valid(self):
        """Test validating a valid stock symbol."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.validate_symbol = AsyncMock(return_value=True)
            
            result = await ValidateStockSymbol("AAPL")
            
            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_stock_symbol_invalid(self):
        """Test validating an invalid stock symbol."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.validate_symbol = AsyncMock(return_value=False)
            
            result = await ValidateStockSymbol("INVALID")
            
            assert result["success"] is True
            assert result["symbol"] == "INVALID"
            assert result["valid"] is False
    
    @pytest.mark.asyncio
    async def test_validate_stock_symbol_error(self):
        """Test stock symbol validation with error."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.validate_symbol = AsyncMock(side_effect=Exception("Validation error"))
            
            result = await ValidateStockSymbol("AAPL")
            
            assert result["success"] is False
            assert result["symbol"] == "AAPL"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_search_stock_symbols_success(self):
        """Test successful stock symbol search."""
        mock_results = ["AAPL - Apple Inc.", "AAPLW - Apple Inc. Warrant"]
        
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.search_symbols = AsyncMock(return_value=mock_results)
            
            result = await SearchStockSymbols("Apple")
            
            assert result["success"] is True
            assert result["query"] == "Apple"
            assert result["results"] == mock_results
            assert result["count"] == 2
    
    @pytest.mark.asyncio
    async def test_search_stock_symbols_no_results(self):
        """Test stock symbol search with no results."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.search_symbols = AsyncMock(return_value=[])
            
            result = await SearchStockSymbols("NonExistentCompany")
            
            assert result["success"] is True
            assert result["query"] == "NonExistentCompany"
            assert result["results"] == []
            assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_search_stock_symbols_error(self):
        """Test stock symbol search with error."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.search_symbols = AsyncMock(side_effect=Exception("Search error"))
            
            result = await SearchStockSymbols("Apple")
            
            assert result["success"] is False
            assert result["query"] == "Apple"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_success(self):
        """Test successful historical data fetch."""
        start_date = "2023-01-01"
        end_date = "2023-01-05"
        
        mock_bars = [
            HistoricalBar(
                symbol="AAPL",
                timestamp=datetime(2023, 1, i+1),
                open=150.0 + i,
                high=155.0 + i,
                low=149.0 + i,
                close=154.0 + i,
                volume=1000000 + i * 100000
            )
            for i in range(5)
        ]
        
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_historical_data = AsyncMock(return_value=mock_bars)
            
            result = await FetchHistoricalData("AAPL", start_date, end_date, "1Day")
            
            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["start_date"] == start_date
            assert result["end_date"] == end_date
            assert result["timeframe"] == "1Day"
            assert len(result["bars"]) == 5
            assert result["total_bars"] == 5
            
            # Check first bar
            first_bar = result["bars"][0]
            assert first_bar["open"] == 150.0
            assert first_bar["high"] == 155.0
            assert first_bar["low"] == 149.0
            assert first_bar["close"] == 154.0
            assert first_bar["volume"] == 1000000
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_no_data(self):
        """Test historical data fetch with no data."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_historical_data = AsyncMock(return_value=[])
            
            result = await FetchHistoricalData("AAPL", "2023-01-01", "2023-01-02", "1Day")
            
            assert result["success"] is True
            assert result["symbol"] == "AAPL"
            assert result["bars"] == []
            assert result["total_bars"] == 0
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_error(self):
        """Test historical data fetch with error."""
        with patch('activities.market_data.market_data_provider') as mock_provider:
            mock_provider.get_historical_data = AsyncMock(side_effect=Exception("Data fetch error"))
            
            result = await FetchHistoricalData("AAPL", "2023-01-01", "2023-01-02", "1Day")
            
            assert result["success"] is False
            assert result["symbol"] == "AAPL"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_invalid_dates(self):
        """Test historical data fetch with invalid date format."""
        result = await FetchHistoricalData("AAPL", "invalid-date", "2023-01-02", "1Day")
        
        assert result["success"] is False
        assert result["symbol"] == "AAPL"
        assert "error" in result
        assert "Invalid isoformat string" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])