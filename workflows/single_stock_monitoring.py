"""Single stock monitoring workflow using broker abstraction."""
import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any, List


@workflow.defn
class StockMonitoringWorkflow:
    """Basic stock monitoring workflow that fetches and tracks stock prices."""
    
    def __init__(self):
        self.monitoring_active = True
        self.price_history: List[Dict[str, Any]] = []
        self.alerts_triggered: List[Dict[str, Any]] = []
    
    @workflow.run
    async def run(
        self,
        symbol: str,
        monitoring_duration_minutes: int = 60,
        check_interval_seconds: int = 30,
        price_change_threshold: float = 0.05  # 5% change threshold
    ) -> Dict[str, Any]:
        """Run stock monitoring workflow.
        
        Args:
            symbol: Stock symbol to monitor
            monitoring_duration_minutes: How long to monitor (default 60 minutes)
            check_interval_seconds: How often to check price (default 30 seconds)
            price_change_threshold: Price change threshold for alerts (default 5%)
            
        Returns:
            Dict containing monitoring results and alerts
        """
        workflow.logger.info(f"Starting stock monitoring for {symbol}")
        
        # Validate symbol first
        validation_result = await workflow.execute_activity(
            "ValidateStockSymbol",
            symbol,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3
            )
        )
        
        if not validation_result.get("valid", False):
            return {
                "success": False,
                "error": f"Invalid stock symbol: {symbol}",
                "symbol": symbol
            }
        
        # Get initial price
        try:
            initial_price_result = await workflow.execute_activity(
                "FetchStockPrice",
                symbol,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3
                )
            )
            initial_price = initial_price_result["price"]
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch initial price for {symbol}: {str(e)}",
                "symbol": symbol
            }
        self.price_history.append({
            "timestamp": workflow.now().isoformat(),
            "price": initial_price,
            "change_percent": 0.0
        })
        
        workflow.logger.info(f"Initial price for {symbol}: ${initial_price}")
        
        # Monitor for specified duration
        end_time = workflow.now() + timedelta(minutes=monitoring_duration_minutes)
        
        while workflow.now() < end_time and self.monitoring_active:
            # Fetch current price
            try:
                current_price_result = await workflow.execute_activity(
                    "FetchStockPrice",
                    symbol,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=10),
                        maximum_attempts=3
                    )
                )
                
                current_price = current_price_result["price"]
                change_percent = ((current_price - initial_price) / initial_price) * 100
                
                # Record price data
                price_data = {
                    "timestamp": workflow.now().isoformat(),
                    "price": current_price,
                    "change_percent": change_percent
                }
                self.price_history.append(price_data)
                
                # Check for significant price changes
                if abs(change_percent) >= (price_change_threshold * 100):
                    alert = {
                        "timestamp": workflow.now().isoformat(),
                        "symbol": symbol,
                        "price": current_price,
                        "initial_price": initial_price,
                        "change_percent": change_percent,
                        "threshold": price_change_threshold * 100,
                        "alert_type": "price_change"
                    }
                    self.alerts_triggered.append(alert)
                    
                    workflow.logger.info(
                        f"ALERT: {symbol} price changed {change_percent:.2f}% "
                        f"from ${initial_price} to ${current_price}"
                    )
                
                workflow.logger.info(
                    f"{symbol}: ${current_price} ({change_percent:+.2f}%)"
                )
                    
            except Exception as e:
                workflow.logger.error(f"Error monitoring {symbol}: {str(e)}")
            
            # Wait for next check interval (only if we still have time)
            if workflow.now() < end_time:
                await asyncio.sleep(check_interval_seconds)
        
        # Compile final results
        final_price = self.price_history[-1]["price"] if self.price_history else initial_price
        total_change_percent = ((final_price - initial_price) / initial_price) * 100 if self.price_history else 0.0
        
        result = {
            "success": True,
            "symbol": symbol,
            "monitoring_duration_minutes": monitoring_duration_minutes,
            "check_interval_seconds": check_interval_seconds,
            "initial_price": initial_price,
            "final_price": final_price,
            "total_change_percent": total_change_percent,
            "price_history": self.price_history,
            "alerts_triggered": self.alerts_triggered,
            "total_price_checks": len(self.price_history),
            "total_alerts": len(self.alerts_triggered),
            "monitoring_completed": workflow.now() >= end_time
        }
        
        workflow.logger.info(
            f"Monitoring completed for {symbol}. "
            f"Final price: ${final_price} ({total_change_percent:+.2f}%). "
            f"Alerts triggered: {len(self.alerts_triggered)}"
        )
        
        return result
    
    @workflow.signal
    async def stop_monitoring(self):
        """Signal to stop monitoring early."""
        workflow.logger.info("Received stop monitoring signal")
        self.monitoring_active = False
    
    @workflow.query
    def get_current_status(self) -> Dict[str, Any]:
        """Query current monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "total_price_checks": len(self.price_history),
            "total_alerts": len(self.alerts_triggered),
            "latest_price": self.price_history[-1] if self.price_history else None,
            "recent_alerts": self.alerts_triggered[-5:] if self.alerts_triggered else []
        }
    
    @workflow.query
    def get_price_history(self) -> List[Dict[str, Any]]:
        """Query complete price history."""
        return self.price_history
    
    @workflow.query
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Query all triggered alerts."""
        return self.alerts_triggered