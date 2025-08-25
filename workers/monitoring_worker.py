import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

# Import workflows
from workflows.single_stock_monitoring import StockMonitoringWorkflow
from workflows.multi_stock_monitoring import MultiStockMonitoringWorkflow

# Import activities
from activities.market_data import (
    FetchStockPrice, FetchMultipleStockPrices, ValidateStockSymbol,
    SearchStockSymbols, FetchHistoricalData
)
from config.queues import MONITORING_QUEUE


async def main():
    # Get Temporal address from environment
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7234")
    
    # Connect to Temporal
    client = await Client.connect(temporal_address)
    
    # Create monitoring worker with dedicated task queue
    worker = Worker(
        client,
        task_queue=MONITORING_QUEUE,
        workflows=[
            StockMonitoringWorkflow,
            MultiStockMonitoringWorkflow,
        ],
        activities=[
            # Market data activities handled by this worker for now
            # In full multi-worker setup, these would be on market-data-queue
            FetchStockPrice,
            FetchMultipleStockPrices,
            ValidateStockSymbol,
            SearchStockSymbols,
            FetchHistoricalData,
        ],
    )
    
    print(f"Monitoring Worker starting on {MONITORING_QUEUE}...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())