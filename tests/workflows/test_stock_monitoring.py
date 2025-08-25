"""Tests for stock monitoring workflows."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.client import WorkflowFailureError

from workflows.single_stock_monitoring import StockMonitoringWorkflow
from workflows.multi_stock_monitoring import MultiStockMonitoringWorkflow
from activities.market_data import (
    FetchStockPrice, FetchMultipleStockPrices, ValidateStockSymbol,
    SearchStockSymbols, FetchHistoricalData
)
from interfaces.market_data import Quote
from brokers.factory import BrokerFactory
from config.queues import TEST_QUEUE


class TestStockMonitoringWorkflow:
    """Test cases for StockMonitoringWorkflow."""
    
    @pytest.mark.asyncio
    async def test_basic_monitoring_workflow_starts(self):
        """Test that monitoring workflow can start successfully."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TEST_QUEUE,
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                # Mock the activities
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    
                    def mock_get_quote(symbol):
                        return Quote(
                            symbol=symbol,
                            price=150.0,
                            bid=149.95,
                            ask=150.05,
                            volume=1000000,
                            timestamp=datetime.now(),
                            exchange="NASDAQ"
                        )
                    
                    mock_provider.get_quote = AsyncMock(side_effect=mock_get_quote)
                    
                    result = await env.client.execute_workflow(
                    StockMonitoringWorkflow.run,
                    args=["AAPL", 1, 1, 0.05],  # symbol, monitoring_duration_minutes, check_interval_seconds, price_change_threshold
                    id="test-monitor-start",
                    task_queue=TEST_QUEUE
                )
                    
                    assert result["success"] is True
                    assert result["symbol"] == "AAPL"
                    assert "final_price" in result
                    assert "total_price_checks" in result
    
    @pytest.mark.asyncio
    async def test_workflow_handles_invalid_symbol(self):
        """Test workflow handles invalid stock symbol."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TEST_QUEUE,
                workflows=[StockMonitoringWorkflow],
                activities=[ValidateStockSymbol]
            ):
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=False)
                    
                    result = await env.client.execute_workflow(
                    StockMonitoringWorkflow.run,
                    args=["INVALID", 1, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                    id="test-invalid-symbol",
                    task_queue=TEST_QUEUE
                )
                    
                    assert result["success"] is False
                    assert "Invalid stock symbol" in result["error"]
                    assert result["symbol"] == "INVALID"
    
    @pytest.mark.asyncio
    async def test_workflow_schedules_periodic_monitoring(self):
        """Test workflow schedules monitoring activities at correct intervals."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TEST_QUEUE,
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                call_count = 0
                
                def mock_get_quote(symbol):
                    nonlocal call_count
                    call_count += 1
                    return Quote(
                        symbol=symbol,
                        price=150.0 + call_count,  # Varying price
                        bid=149.95 + call_count,
                        ask=150.05 + call_count,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    )
                
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(side_effect=mock_get_quote)
                    
                    result = await env.client.execute_workflow(
                    StockMonitoringWorkflow.run,
                    args=["AAPL", 1, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                    id="test-periodic-monitoring",
                    task_queue=TEST_QUEUE
                )
                    
                    assert result["success"] is True
                    assert result["total_price_checks"] >= 2  # Should have multiple checks
                    assert call_count >= 2  # Should have called get_quote multiple times
    
    @pytest.mark.asyncio
    async def test_workflow_handles_activity_failure(self):
        """Test workflow handles activity failures gracefully."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TEST_QUEUE,
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                call_count = 0
                
                def mock_get_quote_with_failure(symbol):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("Temporary broker failure")
                    return Quote(
                        symbol=symbol,
                        price=150.0,
                        bid=149.95,
                        ask=150.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    )
                
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(side_effect=mock_get_quote_with_failure)
                    
                    result = await env.client.execute_workflow(
                    StockMonitoringWorkflow.run,
                    args=["AAPL", 1, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                    id="test-activity-failure",
                    task_queue=TEST_QUEUE
                )
                    
                    # Workflow should complete successfully despite initial failure
                    assert result["success"] is True
                    assert call_count >= 2  # Should have retried
    
    @pytest.mark.asyncio
    async def test_workflow_maintains_state_between_polls(self):
        """Test workflow maintains state across polling cycles."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue=TEST_QUEUE,
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                prices = [150.0, 155.0, 160.0]  # Increasing prices
                call_count = 0
                
                def mock_get_quote_varying_price(symbol):
                    nonlocal call_count
                    price = prices[min(call_count, len(prices) - 1)]
                    call_count += 1
                    return Quote(
                        symbol=symbol,
                        price=price,
                        bid=price - 0.05,
                        ask=price + 0.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    )
                
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(side_effect=mock_get_quote_varying_price)
                    
                    result = await env.client.execute_workflow(
                    StockMonitoringWorkflow.run,
                    args=["AAPL", 1, 1, 0.03],  # symbol, monitoring_duration_minutes, check_interval_seconds, price_change_threshold
                    id="test-state-maintenance",
                    task_queue=TEST_QUEUE
                )
                    
                    assert result["success"] is True
                    assert result["total_price_checks"] >= 2
                    # Should have detected price changes and triggered alerts
                    assert result["total_alerts"] > 0
    
    @pytest.mark.asyncio
    async def test_workflow_can_be_stopped_gracefully(self):
        """Test workflow can be stopped via signal."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(return_value=Quote(
                        symbol="AAPL",
                        price=150.0,
                        bid=149.95,
                        ask=150.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    ))
                    
                    # Start workflow with long duration
                    handle = await env.client.start_workflow(
                        StockMonitoringWorkflow.run,
                        args=["AAPL", 60, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                        id="test-stop-gracefully",
                        task_queue=TEST_QUEUE
                    )
                    
                    # Wait a bit then send stop signal
                    await asyncio.sleep(0.1)
                    await handle.signal(StockMonitoringWorkflow.stop_monitoring)
                    
                    result = await handle.result()
                    
                    assert result["success"] is True
                    # Should have stopped early
                    assert result["monitoring_completed"] is False


class TestMultiStockMonitoringWorkflow:
    """Test cases for MultiStockMonitoringWorkflow."""
    
    @pytest.mark.asyncio
    async def test_parallel_workflow_creation(self):
        """Test separate workflows are created for each stock."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[MultiStockMonitoringWorkflow, StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    
                    def mock_get_quote(symbol):
                        return Quote(
                            symbol=symbol,
                            price=150.0,
                            bid=149.95,
                            ask=150.05,
                            volume=1000000,
                            timestamp=datetime.now(),
                            exchange="NASDAQ"
                        )
                    
                    mock_provider.get_quote = AsyncMock(side_effect=mock_get_quote)
                    
                    symbols = ["AAPL", "GOOGL", "MSFT"]
                    result = await env.client.execute_workflow(
                        MultiStockMonitoringWorkflow.run,
                        args=[symbols, 1, 1],  # symbols, monitoring_duration_minutes, check_interval_seconds
                        id="test-parallel-creation",
                        task_queue=TEST_QUEUE
                    )
                    
                    assert result["success"] is True
                    assert result["total_symbols"] == 3
                    assert result["successful_monitors"] == 3
                    assert result["failed_monitors"] == 0
                    assert len(result["results"]) == 3
                    
                    # Check each symbol has results
                    for symbol in symbols:
                        assert symbol in result["results"]
                        assert result["results"][symbol]["success"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_independence(self):
        """Test workflows operate independently when one fails."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[MultiStockMonitoringWorkflow, StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                def mock_validate_symbol(symbol):
                    # Make INVALID symbol fail validation
                    return symbol != "INVALID"
                
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(side_effect=mock_validate_symbol)
                    mock_provider.get_quote = AsyncMock(return_value=Quote(
                        symbol="AAPL",
                        price=150.0,
                        bid=149.95,
                        ask=150.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    ))
                    
                    symbols = ["AAPL", "INVALID", "MSFT"]
                    result = await env.client.execute_workflow(
                    MultiStockMonitoringWorkflow.run,
                    args=[symbols, 1, 1],  # symbols, monitoring_duration_minutes, check_interval_seconds
                    id="test-workflow-independence",
                    task_queue=TEST_QUEUE
                )
                    
                    assert result["success"] is True
                    assert result["total_symbols"] == 3
                    assert result["successful_monitors"] == 2  # AAPL and MSFT
                    assert result["failed_monitors"] == 1     # INVALID
                    
                    # Check successful workflows completed
                    assert result["results"]["AAPL"]["success"] is True
                    assert result["results"]["MSFT"]["success"] is True
                    assert result["results"]["INVALID"]["success"] is False


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_single_stock_monitoring(self):
        """Test complete monitoring flow with broker abstraction."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                # Use actual broker factory with mock broker
                with patch('config.broker_config.BrokerConfigManager.get_config_by_name') as mock_config:
                    mock_config.return_value = {
                        "name": "mock",
                        "type": "mock",
                        "config": {}
                    }
                    
                    # Initialize broker factory
                    factory = BrokerFactory()
                    market_data_provider = factory.create_market_data_provider("mock", {})
                    
                    with patch('activities.market_data.market_data_provider', market_data_provider):
                        result = await env.client.execute_workflow(
                            StockMonitoringWorkflow.run,
                            args=["AAPL", 1, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                            id="test-e2e-single-stock",
                            task_queue=TEST_QUEUE
                        )
                        
                        assert result["success"] is True
                        assert result["symbol"] == "AAPL"
                        assert result["final_price"] > 0
                        assert result["total_price_checks"] >= 1
                        assert "initial_price" in result
                        assert "total_change_percent" in result
    
    @pytest.mark.asyncio
    async def test_monitoring_produces_expected_logs(self):
        """Test monitoring produces correct log output."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(return_value=Quote(
                        symbol="AAPL",
                        price=150.0,
                        bid=149.95,
                        ask=150.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    ))
                    
                    # Capture workflow logs
                    with patch('temporalio.workflow.logger') as mock_logger:
                        result = await env.client.execute_workflow(
                                 StockMonitoringWorkflow.run,
                                 args=["AAPL", 1, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                                 id="test-logging",
                                 task_queue=TEST_QUEUE
                             )
                        
                        assert result["success"] is True
                        
                        # Verify logging calls were made
                        assert mock_logger.info.called
                        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
                        
                        # Check for expected log messages
                        start_logs = [log for log in log_calls if "Starting stock monitoring" in log]
                        assert len(start_logs) > 0
                        
                        completion_logs = [log for log in log_calls if "Monitoring completed" in log]
                        assert len(completion_logs) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_query_functionality(self):
        """Test workflow query methods work correctly."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[StockMonitoringWorkflow],
                activities=[
                    ValidateStockSymbol,
                    FetchStockPrice
                ]
            ):
                with patch('activities.market_data.market_data_provider') as mock_provider:
                    mock_provider.validate_symbol = AsyncMock(return_value=True)
                    mock_provider.get_quote = AsyncMock(return_value=Quote(
                        symbol="AAPL",
                        price=150.0,
                        bid=149.95,
                        ask=150.05,
                        volume=1000000,
                        timestamp=datetime.now(),
                        exchange="NASDAQ"
                    ))
                    
                    # Start long-running workflow
                    handle = await env.client.start_workflow(
                        StockMonitoringWorkflow.run,
                        args=["AAPL", 60, 1],  # symbol, monitoring_duration_minutes, check_interval_seconds
                        id="test-queries",
                        task_queue=TEST_QUEUE
                    )
                    
                    # Wait a bit for some activity
                    await asyncio.sleep(0.1)
                    
                    # Test queries
                    status = await handle.query(StockMonitoringWorkflow.get_current_status)
                    assert "monitoring_active" in status
                    assert "total_price_checks" in status
                    assert "total_alerts" in status
                    
                    price_history = await handle.query(StockMonitoringWorkflow.get_price_history)
                    assert isinstance(price_history, list)
                    
                    alerts = await handle.query(StockMonitoringWorkflow.get_alerts)
                    assert isinstance(alerts, list)
                    
                    # Stop the workflow
                    await handle.signal(StockMonitoringWorkflow.stop_monitoring)
                    await handle.result()


if __name__ == "__main__":
    pytest.main([__file__])