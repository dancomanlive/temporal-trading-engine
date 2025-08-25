#!/usr/bin/env python3
"""Demo script to start workflows for viewing in Temporal UI."""

import asyncio
from datetime import datetime
from temporalio.client import Client
from workflows.single_stock_monitoring import StockMonitoringWorkflow
from workflows.multi_stock_monitoring import MultiStockMonitoringWorkflow
from config.queues import MONITORING_QUEUE


async def start_demo_workflows():
    """Start demo workflows to view in Temporal UI."""
    # Connect to Temporal
    client = await Client.connect("localhost:7234")
    
    print("Starting demo workflows...")
    
    # Start multi-stock monitoring workflow (Slice 3)
    multi_stock_handle = await client.start_workflow(
        MultiStockMonitoringWorkflow.run,
        args=[
            ["AAPL", "GOOGL", "MSFT"],  # symbols
            2,                           # monitoring_duration_minutes (2 minutes)
            30,                          # check_interval_seconds
            0.03                         # price_change_threshold (3%)
        ],
        id=f"multi-stock-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue=MONITORING_QUEUE
    )
    print(f"Started multi-stock workflow: {multi_stock_handle.id}")
    
    print("\n=== Demo Workflows Started ===")
    print(f"Multi-Stock Workflow ID: {multi_stock_handle.id}")
    print("\nYou can now view these workflows in the Temporal UI at:")
    print("http://localhost:8080")
    print("\nWorkflow will run for 2 minutes and then complete.")
    print("Watch the logs and workflow history in the UI!")
    
    # Optionally wait for completion and show results
    print("\nWaiting for workflow to complete...")
    
    try:
        multi_result = await multi_stock_handle.result()
        print(f"\nMulti-stock result: {multi_result['total_symbols']} stocks monitored")
        print(f"Successful monitors: {multi_result['successful_monitors']}")
        print(f"Total alerts: {multi_result['total_alerts']}")
        
        for symbol, result in multi_result['results'].items():
            if result.get('success'):
                alerts = len(result.get('alerts_triggered', []))
                print(f"  {symbol}: {alerts} alerts")
            else:
                print(f"  {symbol}: Failed - {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Multi-stock workflow error: {e}")


if __name__ == "__main__":
    asyncio.run(start_demo_workflows())