# Architecture Patterns for Stock Trading System

## Overview
This document defines the architectural patterns and implementation guidelines for building the stock trading system using a simplified workflow architecture. The system follows a direct chain pattern: Scanner → MultiStockMonitoringWorkflow → Individual StockMonitoringWorkflows with parent-child signal communication for real-time responsiveness.

## Core Architecture Components

### 1. Direct Workflow Pattern
The system uses direct workflow instantiation and execution for stock monitoring.

**Key Characteristics:**
- Direct workflow class instantiation
- Parent-child workflow communication via signals
- Built-in retry policies and error handling
- Real-time stock price monitoring and alerting

### 2. Signal-Based Communication
The system uses parent-child workflow communication via Temporal signals for real-time coordination.

## Implementation Patterns for Stock Trading

### Pattern 1: Activity Implementation

**Structure:**
```python
from temporalio import activity
from typing import Dict, Any

@activity.defn
async def FetchStockPrice(symbol: str) -> Dict[str, Any]:
    """Fetch current stock price from broker API."""
    # Implementation here
    return {
        "symbol": symbol,
        "price": 150.25,
        "timestamp": "2024-01-15T10:30:00Z"
    }
```

**Registration:**
```python
# In workers/monitoring_worker.py
from activities.stock_data import FetchStockPrice

worker = Worker(
    client,
    task_queue="stock-trading-queue",
    activities=[FetchStockPrice]
)
```

### Pattern 2: Direct Workflow Implementation

**Structure:**
```python
from temporalio import workflow
from datetime import timedelta
from typing import Dict, Any

@workflow.defn
class StockMonitoringWorkflow:
    """Monitors a single stock for price changes."""
    
    @workflow.run
    async def run(self, symbol: str, threshold: float) -> Dict[str, Any]:
        """Monitor stock price against threshold."""
        # Direct activity execution
        price = await workflow.execute_activity(
            FetchStockPrice,
            symbol,
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        if price > threshold:
            # Signal parent workflow
            await workflow.get_external_workflow_handle(
                self.parent_workflow_id
            ).signal("price_alert", {"symbol": symbol, "price": price})
        
        return {"symbol": symbol, "price": price, "triggered": price > threshold}
```

## Simplified Stock Trading System Architecture

### Core Workflow Pattern

The system uses a simplified three-tier workflow architecture:

1. **Scanner Workflow**: Filters market data to identify interesting stocks
2. **MultiStockMonitoringWorkflow**: Coordinates monitoring of selected stocks with LLM planning
3. **Individual StockMonitoringWorkflows**: Monitor single stocks and signal parent via Temporal Signals

### Workflow Communication Pattern

```python
# Parent-Child Signal Communication
class MultiStockMonitoringWorkflow:
    async def run(self, stock_list: List[str]):
        # Generate custom monitoring plans via LLM
        plans = await workflow.execute_activity(GenerateMonitoringPlans, stock_list)
        
        # Spawn child workflows for each stock
        child_handles = []
        for stock, plan in plans.items():
            handle = await workflow.start_child_workflow(
                StockMonitoringWorkflow.run,
                stock, plan,
                id=f"monitor-{stock}"
            )
            child_handles.append(handle)
        
        # Wait for signals from children
        while True:
            signal = await workflow.wait_condition(lambda: self._received_signal)
            
            # Process signal through evaluation activity
            decision = await workflow.execute_activity(
                EvaluateSignal, signal
            )
            
            if decision["action"] == "trade":
                await workflow.start_child_workflow(
                    TradeExecutionWorkflow.run,
                    decision["trade_params"]
                )
            elif decision["action"] == "update_plan":
                # Update monitoring plan via LLM
                new_plan = await workflow.execute_activity(
                    UpdateMonitoringPlan, signal
                )
                # Signal child to update plan
                await child_handles[signal["stock_index"]].signal(
                    "update_plan", new_plan
                )

class StockMonitoringWorkflow:
    async def run(self, symbol: str, monitoring_plan: Dict):
        while self._monitoring:
            # Execute monitoring plan
            alert = await self._check_conditions(symbol, monitoring_plan)
            
            if alert:
                # Signal parent with alert details
                await workflow.get_external_workflow_handle(
                    self._parent_workflow_id
                ).signal("stock_alert", {
                    "symbol": symbol,
                    "alert_type": alert["type"],
                    "data": alert["data"],
                    "confidence": alert["confidence"]
                })
```

### Core Activities to Implement

#### Scanner Activities
```python
# activities/scanner.py
@activity.defn
async def ScanMarketData() -> List[str]

@activity.defn
async def FilterInterestingStocks(market_data: Dict) -> List[str]
```



#### Data Activities
```python
# activities/stock_data.py
@activity.defn
async def FetchStockPrice(symbol: str) -> Dict[str, Any]

@activity.defn
async def FetchMarketData(symbols: List[str]) -> Dict[str, Any]

@activity.defn
async def GetHistoricalData(symbol: str, period: str) -> Dict[str, Any]
```

#### Evaluation Activities
```python
# activities/evaluation.py
@activity.defn
async def EvaluateSignal(signal_data: Dict) -> Dict[str, Any]

@activity.defn
async def AssessRisk(signal_data: Dict, portfolio_context: Dict) -> Dict[str, Any]
```

#### Trading Activities
```python
# activities/trading.py
@activity.defn
async def ExecuteTrade(symbol: str, action: str, quantity: int) -> Dict[str, Any]

@activity.defn
async def CancelOrder(order_id: str) -> Dict[str, Any]

@activity.defn
async def GetPortfolioStatus() -> Dict[str, Any]
```

#### Analysis Activities
```python
# activities/analysis.py
@activity.defn
async def AnalyzeMarketConditions(symbol: str) -> Dict[str, Any]

@activity.defn
async def CalculateRiskMetrics(portfolio: Dict) -> Dict[str, Any]

@activity.defn
async def GenerateTradingSignal(symbol: str, strategy: str) -> Dict[str, Any]
```

### Core Workflows to Implement

#### Primary Workflow Chain
```python
# workflows/scanner.py
@workflow.defn
class ScannerWorkflow:
    """Scans market data and filters interesting stocks for monitoring."""
    
    @workflow.run
    async def run(self) -> List[str]:
        # Scan market data
        market_data = await workflow.execute_activity(
            ScanMarketData,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Filter interesting stocks
        interesting_stocks = await workflow.execute_activity(
            FilterInterestingStocks,
            market_data,
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Start MultiStockMonitoringWorkflow with filtered stocks
        await workflow.start_child_workflow(
            MultiStockMonitoringWorkflow.run,
            interesting_stocks,
            id=f"multi-monitor-{workflow.info().workflow_id}"
        )
        
        return interesting_stocks

# workflows/monitoring.py
@workflow.defn
class MultiStockMonitoringWorkflow:
    """Coordinates monitoring of multiple stocks with LLM-generated plans."""
    
    def __init__(self):
        self._received_signals = []
        self._child_handles = {}
    
    @workflow.signal
    async def stock_alert(self, signal_data: Dict):
        """Receive alerts from child StockMonitoringWorkflows."""
        self._received_signals.append(signal_data)
    
    @workflow.run
    async def run(self, stock_list: List[str]) -> Dict[str, Any]:
        # Generate custom monitoring plans for each stock
        monitoring_plans = await workflow.execute_activity(
            GenerateMonitoringPlans,
            stock_list,
            start_to_close_timeout=timedelta(minutes=3)
        )
        
        # Spawn individual monitoring workflows
        for stock in stock_list:
            handle = await workflow.start_child_workflow(
                StockMonitoringWorkflow.run,
                stock,
                monitoring_plans[stock],
                workflow.info().workflow_id,  # parent_id for signaling
                id=f"monitor-{stock}-{workflow.info().workflow_id}"
            )
            self._child_handles[stock] = handle
        
        # Process signals from children
        while len(self._child_handles) > 0:
            await workflow.wait_condition(lambda: len(self._received_signals) > 0)
            
            signal = self._received_signals.pop(0)
            
            # Evaluate signal and decide action
            decision = await workflow.execute_activity(
                EvaluateSignal,
                signal,
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            if decision["action"] == "trade":
                # Execute trade
                await workflow.start_child_workflow(
                    TradeExecutionWorkflow.run,
                    decision["trade_params"],
                    id=f"trade-{signal['symbol']}-{workflow.info().workflow_id}"
                )
            elif decision["action"] == "update_plan":
                # Update monitoring plan
                new_plan = await workflow.execute_activity(
                    UpdateMonitoringPlan,
                    signal,
                    start_to_close_timeout=timedelta(minutes=1)
                )
                # Signal child to update its plan
                await self._child_handles[signal["symbol"]].signal(
                    "update_plan", new_plan
                )
        
        return {"status": "completed", "signals_processed": len(self._received_signals)}

@workflow.defn
class StockMonitoringWorkflow:
    """Monitors single stock according to LLM-generated plan."""
    
    def __init__(self):
        self._monitoring = True
        self._monitoring_plan = None
        self._parent_workflow_id = None
    
    @workflow.signal
    async def update_plan(self, new_plan: Dict):
        """Update monitoring plan from parent workflow."""
        self._monitoring_plan = new_plan
    
    @workflow.signal
    async def stop_monitoring(self):
        """Stop monitoring this stock."""
        self._monitoring = False
    
    @workflow.run
    async def run(self, symbol: str, monitoring_plan: Dict, parent_workflow_id: str) -> Dict[str, Any]:
        self._monitoring_plan = monitoring_plan
        self._parent_workflow_id = parent_workflow_id
        
        while self._monitoring:
            # Execute monitoring plan
            current_data = await workflow.execute_activity(
                FetchStockPrice,
                symbol,
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Check conditions based on monitoring plan
            alert = await self._evaluate_conditions(symbol, current_data, self._monitoring_plan)
            
            if alert:
                # Signal parent with alert
                parent_handle = workflow.get_external_workflow_handle(self._parent_workflow_id)
                await parent_handle.signal("stock_alert", {
                    "symbol": symbol,
                    "alert_type": alert["type"],
                    "data": current_data,
                    "confidence": alert["confidence"],
                    "timestamp": workflow.now()
                })
            
            # Wait based on monitoring plan frequency
            await workflow.sleep(self._monitoring_plan.get("check_interval", 60))
        
        return {"symbol": symbol, "status": "monitoring_stopped"}
    
    async def _evaluate_conditions(self, symbol: str, data: Dict, plan: Dict) -> Optional[Dict]:
        """Evaluate monitoring conditions based on plan."""
        # This would contain the logic to check plan conditions
        # For now, simplified example
        if "price_threshold" in plan:
            if data["price"] > plan["price_threshold"]:
                return {
                    "type": "price_threshold",
                    "confidence": 0.9
                }
        return None
```

#### Trading Workflows
```python
# workflows/trading.py
@workflow.defn
class TradeExecutionWorkflow:
    """Executes trades with risk management."""
    
    @workflow.run
    async def run(self, trade_params: Dict) -> Dict[str, Any]:
        # Risk assessment
        risk_assessment = await workflow.execute_activity(
            AssessRisk,
            trade_params,
            {},  # portfolio_context
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        if risk_assessment["approved"]:
            # Execute trade
            trade_result = await workflow.execute_activity(
                ExecuteTrade,
                trade_params["symbol"],
                trade_params["action"],
                trade_params["quantity"],
                start_to_close_timeout=timedelta(minutes=2)
            )
            return trade_result
        else:
            return {"status": "rejected", "reason": risk_assessment["reason"]}
```

## Implementation Guidelines

### 1. Activity Design Principles

**Single Responsibility:**
- Each activity should have one clear purpose
- Activities should be stateless and idempotent
- Use clear, descriptive names

**Error Handling:**
- Always return structured results with success/error indicators
- Use appropriate Temporal retry policies
- Log important events and errors

**Example:**
```python
@activity.defn
async def FetchStockPrice(symbol: str) -> Dict[str, Any]:
    try:
        # Broker API call
        price_data = await broker_client.get_latest_quote(symbol)
        return {
            "success": True,
            "symbol": symbol,
            "price": price_data.ask_price,
            "timestamp": price_data.timestamp.isoformat()
        }
    except Exception as e:
        activity.logger.error(f"Failed to fetch price for {symbol}: {e}")
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }
```

### 2. Workflow Design Principles

**Deterministic Execution:**
- Use Temporal's deterministic patterns
- Avoid non-deterministic operations in workflow code
- Use activities for external API calls

**State Management:**
- Use workflow state for coordination
- Pass data between activities through workflow state
- Handle partial failures gracefully

**Example:**
```python
@workflow.defn
class StockMonitorWorkflow:
    def __init__(self):
        self._monitoring = False
        self._last_price = None
    
    @workflow.run
    async def run(self, symbol: str, threshold: float) -> Dict[str, Any]:
        self._monitoring = True
        
        while self._monitoring:
            # Fetch current price
            price_result = await workflow.execute_activity(
                FetchStockPrice,
                symbol,
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            if price_result["success"]:
                current_price = price_result["price"]
                
                # Check threshold
                if current_price >= threshold:
                    # Trigger alert
                    await workflow.execute_activity(
                        SendAlert,
                        f"Price alert: {symbol} reached {current_price}",
                        start_to_close_timeout=timedelta(seconds=10)
                    )
                    break
            
            # Wait before next check
            await workflow.sleep(60)  # Check every minute
        
        return {"symbol": symbol, "final_price": current_price}
```

### 3. Direct Workflow Registration

**Simplified Worker Configuration:**
```python
# workers/monitoring_worker.py - Direct workflow and activity registration
from workflows.single_stock_monitoring import StockMonitoringWorkflow
from workflows.multi_stock_monitoring import MultiStockMonitoringWorkflow
from activities.stock_data import FetchStockPrice, FetchMarketData
from activities.trading import ExecuteTrade, GetPortfolioStatus
from activities.analysis import AnalyzeMarketConditions, CalculateRiskMetrics

worker = Worker(
    client,
    task_queue="stock-trading-queue",
    workflows=[
        StockMonitoringWorkflow,
        MultiStockMonitoringWorkflow,
    ],
    activities=[
        FetchStockPrice,
        FetchMarketData,
        ExecuteTrade,
        GetPortfolioStatus,
        AnalyzeMarketConditions,
        CalculateRiskMetrics,
    ]
)
```



## Testing Patterns

### 1. Activity Testing
```python
# tests/activities/test_stock_data.py
import pytest
from activities.stock_data import FetchStockPrice

@pytest.mark.asyncio
async def test_fetch_stock_price_success():
    result = await FetchStockPrice("AAPL")
    assert result["success"] is True
    assert result["symbol"] == "AAPL"
    assert "price" in result
    assert "timestamp" in result
```

### 2. Workflow Testing
```python
# tests/workflows/test_monitoring.py
import pytest
from temporalio.testing import WorkflowEnvironment
from workflows.monitoring import StockMonitorWorkflow

@pytest.mark.asyncio
async def test_stock_monitor_workflow():
    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[StockMonitorWorkflow],
            activities=[FetchStockPrice]
        ):
            result = await env.client.execute_workflow(
                StockMonitorWorkflow.run,
                "AAPL",
                150.0,
                id="test-monitor",
                task_queue="test-queue"
            )
            assert result["symbol"] == "AAPL"
```

### 3. Integration Testing
```python
# tests/integration/test_workflow_integration.py
@pytest.mark.asyncio
async def test_stock_monitoring_workflow_integration():
    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[StockMonitoringWorkflow],
            activities=[FetchStockPrice]
        ):
            result = await env.client.execute_workflow(
                StockMonitoringWorkflow.run,
                "AAPL",
                150.0,
                id="test-integration",
                task_queue="test-queue"
            )
            
            assert result["symbol"] == "AAPL"
            assert "price" in result
```

## Migration Strategy

### Phase 1: Foundation
1. Remove existing fraud/customer support activities and workflows
2. Implement core stock data activities
3. Register activities and workflows with Temporal workers
4. Create basic monitoring workflows

### Phase 2: Trading Implementation
1. Implement broker API integration activities
2. Create trading execution workflows
3. Add risk management activities
4. Implement portfolio management workflows

### Phase 3: Advanced Features
1. Add LLM analysis activities
2. Implement complex trading strategies
3. Add performance analytics
4. Create production monitoring and alerting

## Best Practices

1. **Consistent Naming**: Use clear, consistent naming for activities and workflows
2. **Error Handling**: Always return structured results with success indicators
3. **Logging**: Use Temporal's logging for debugging and monitoring
4. **Documentation**: Keep activity and workflow documentation up-to-date
5. **Testing**: Write comprehensive tests for all activities and workflows
6. **Modularity**: Keep activities focused and workflows composable
7. **Configuration**: Use environment variables for API keys and settings
8. **Monitoring**: Implement proper observability for production systems

This architecture provides a solid foundation for implementing the stock trading system while leveraging the existing Temporal infrastructure.