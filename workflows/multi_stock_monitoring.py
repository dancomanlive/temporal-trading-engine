"""Multi-stock monitoring workflow using broker abstraction."""
from datetime import timedelta
from temporalio import workflow
from typing import Dict, Any, List
from .single_stock_monitoring import StockMonitoringWorkflow


@workflow.defn
class MultiStockMonitoringWorkflow:
    """Monitor multiple stocks simultaneously."""
    
    @workflow.run
    async def run(
        self,
        symbols: List[str],
        monitoring_duration_minutes: int = 60,
        check_interval_seconds: int = 30,
        price_change_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """Monitor multiple stocks.
        
        Args:
            symbols: List of stock symbols to monitor
            monitoring_duration_minutes: How long to monitor
            check_interval_seconds: How often to check prices
            price_change_threshold: Price change threshold for alerts
            
        Returns:
            Dict containing results for all monitored stocks
        """
        workflow.logger.info(f"Starting multi-stock monitoring for {len(symbols)} symbols")
        
        # Start child workflows for parallel execution
        child_workflows = []
        for symbol in symbols:
            try:
                # Start child workflow for each symbol
                child_workflow = await workflow.start_child_workflow(
                    StockMonitoringWorkflow.run,
                    args=[symbol, monitoring_duration_minutes, check_interval_seconds, price_change_threshold],
                    id=f"stock-monitor-{symbol}-{workflow.uuid4()}"
                    # Use same task queue as parent workflow
                )
                child_workflows.append((symbol, child_workflow))
                workflow.logger.info(f"Started monitoring child workflow for {symbol}")
            except Exception as e:
                workflow.logger.error(f"Failed to start monitoring for {symbol}: {str(e)}")
                child_workflows.append((symbol, None))
        
        # Collect results from all child workflows
        results = {}
        for symbol, child_workflow in child_workflows:
            try:
                if child_workflow:
                    result = await child_workflow
                    results[symbol] = result
                else:
                    results[symbol] = {
                        "success": False,
                        "error": "Failed to start child workflow",
                        "symbol": symbol
                    }
            except Exception as e:
                workflow.logger.error(f"Error collecting result for {symbol}: {str(e)}")
                results[symbol] = {
                    "success": False,
                    "error": str(e),
                    "symbol": symbol
                }
        
        # Compile summary
        successful_monitors = sum(1 for r in results.values() if r.get("success", False))
        total_alerts = sum(len(r.get("alerts_triggered", [])) for r in results.values())
        
        summary = {
            "success": True,
            "total_symbols": len(symbols),
            "successful_monitors": successful_monitors,
            "failed_monitors": len(symbols) - successful_monitors,
            "total_alerts": total_alerts,
            "monitoring_duration_minutes": monitoring_duration_minutes,
            "results": results
        }
        
        workflow.logger.info(
            f"Multi-stock monitoring completed. "
            f"Successful: {successful_monitors}/{len(symbols)}. "
            f"Total alerts: {total_alerts}"
        )
        
        return summary