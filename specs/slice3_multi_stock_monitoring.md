# Slice 3: Multi-Stock Monitoring

## Overview
End-to-End Feature: Monitor multiple stocks simultaneously using MultiStockMonitoringWorkflow with parent-child signal communication
Deliverable: System monitoring AAPL, GOOGL, MSFT with LLM-generated custom monitoring plans and real-time signal evaluation

## Architecture Pattern
This slice implements the simplified workflow pattern:
- **MultiStockMonitoringWorkflow** (Parent): Coordinates monitoring, generates LLM plans, evaluates signals
- **StockMonitoringWorkflow** (Children): Monitor individual stocks, send signals to parent
- **Signal Communication**: Real-time parent-child communication via Temporal Signals
- **Evaluation Activities**: Signal evaluation and trading decisions within parent workflow

## Multi-Worker Architecture

### Primary Workers

#### Monitoring Worker
- **Task Queue**: monitoring-queue
- **Purpose**: Execute multi-stock monitoring workflows and coordinate child workflows
- **Workflows**: `MultiStockMonitoringWorkflow`, `StockMonitoringWorkflow`
- **Activities**: Workflow coordination, signal evaluation, LLM plan generation
- **Scaling**: Multiple instances for concurrent multi-stock monitoring
- **Performance**: < 1s latency for workflow operations, handle 100+ concurrent workflows

#### Market Data Worker
- **Task Queue**: market-data-queue
- **Purpose**: Handle high-frequency market data operations for multiple stocks
- **Activities**: `FetchMultipleStockPrices`, `FetchStockPrice`, `ValidateStockSymbol`
- **Scaling**: Multiple instances for high throughput (1,000+ stocks)
- **Performance**: < 100ms for price fetching, batch operations for efficiency
- **Load Balancing**: Distribute stock price requests across instances

### Worker Coordination
- **Workflow Distribution**: Parent workflows run on monitoring workers
- **Data Fetching**: Child workflows delegate price fetching to market data workers
- **Signal Processing**: All signal evaluation remains on monitoring workers
- **Cross-Worker Communication**: Activities called across worker boundaries via Temporal

### Scaling Strategy
- **Monitoring Workers**: Scale based on number of active multi-stock workflows
- **Market Data Workers**: Scale based on API rate limits and stock volume
- **Queue Management**: Separate queues prevent market data bottlenecks from affecting workflows
- **Resource Isolation**: Worker failures don't cascade across different operational areas

## Test Specifications

### MultiStockMonitoringWorkflow Configuration Tests

#### `test_multi_stock_workflow_initialization()`
- **Purpose**: Verify MultiStockMonitoringWorkflow can be initialized with stock list
- **Given**: Stock list [AAPL, GOOGL, MSFT]
- **When**: MultiStockMonitoringWorkflow is started
- **Then**: Workflow initializes and generates monitoring plans
- **Assertions**: Workflow started, LLM planning activity called, stock list processed

#### `test_llm_monitoring_plan_generation()`
- **Purpose**: Verify LLM generates custom monitoring plans for each stock
- **Given**: Stock list with market context
- **When**: GenerateMonitoringPlans activity is executed
- **Then**: Custom monitoring plan created for each stock
- **Assertions**: Plans contain stock-specific thresholds, metrics, and conditions

#### `test_stock_list_validation()`
- **Purpose**: Verify stock list validation during configuration
- **Given**: Mix of valid and invalid stock symbols
- **When**: Configuration is validated
- **Then**: Invalid symbols are rejected
- **Assertions**: Valid symbols accepted, invalid rejected with errors

#### `test_dynamic_child_workflow_management()`
- **Purpose**: Verify child StockMonitoringWorkflows can be added/removed dynamically
- **Given**: MultiStockMonitoringWorkflow with 2 child workflows
- **When**: Third stock is added via signal
- **Then**: New child workflow is spawned with LLM-generated plan
- **Assertions**: New child started, parent tracking updated, signal communication established

#### `test_child_workflow_termination()`
- **Purpose**: Verify child workflows can be terminated gracefully
- **Given**: MultiStockMonitoringWorkflow with 3 child workflows
- **When**: Stop signal is sent to one child
- **Then**: Child workflow terminates, parent updates tracking
- **Assertions**: Child terminated cleanly, parent state updated, other children unaffected

### Parent-Child Signal Communication Tests

#### `test_child_workflow_spawning()`
- **Purpose**: Verify MultiStockMonitoringWorkflow spawns child workflows correctly
- **Given**: MultiStockMonitoringWorkflow with stock list [AAPL, GOOGL, MSFT]
- **When**: Workflow starts and generates monitoring plans
- **Then**: Three child StockMonitoringWorkflows are spawned
- **Assertions**: Each child has unique ID, custom monitoring plan, signal communication established

#### `test_signal_communication_setup()`
- **Purpose**: Verify signal communication is established between parent and children
- **Given**: Parent workflow with spawned children
- **When**: Children are initialized
- **Then**: Signal handlers are registered for bidirectional communication
- **Assertions**: Parent can receive signals from children, children can receive updates from parent

#### `test_child_workflow_independence()`
- **Purpose**: Verify child workflows operate independently while maintaining communication
- **Given**: Three child workflows monitoring different stocks
- **When**: One child encounters error or alert
- **Then**: Other children continue unaffected, parent receives error signal
- **Assertions**: Failed child isolated, others maintain state, parent notified

#### `test_signal_based_alert_propagation()`
- **Purpose**: Verify alerts are sent from children to parent via signals
- **Given**: Child workflow detecting price threshold breach
- **When**: Alert condition is met
- **Then**: Child sends alert signal to parent workflow
- **Assertions**: Signal received by parent, alert data intact, timing recorded

#### `test_concurrent_signal_handling()`
- **Purpose**: Verify parent can handle simultaneous signals from multiple children
- **Given**: Multiple children sending signals simultaneously
- **When**: Signals arrive at parent
- **Then**: All signals are processed without loss
- **Assertions**: No signal loss, proper ordering maintained, all children acknowledged

#### `test_workflow_resource_management()`
- **Purpose**: Verify proper resource allocation across workflows
- **Given**: Multiple workflows consuming resources
- **When**: System runs under load
- **Then**: Resources are allocated fairly
- **Assertions**: No resource starvation, balanced allocation

### Parallel Data Fetching Tests

#### `test_concurrent_price_fetching()`
- **Purpose**: Verify price data is fetched concurrently for all stocks
- **Given**: 3 stocks configured for monitoring
- **When**: Price fetch cycle occurs
- **Then**: All prices are fetched in parallel
- **Assertions**: Concurrent API calls made, total time minimized

#### `test_api_rate_limit_management()`
- **Purpose**: Verify API rate limits are respected across all stocks
- **Given**: Multiple stocks requiring API calls
- **When**: Rate limit is approached
- **Then**: Calls are throttled appropriately
- **Assertions**: Rate limit not exceeded, all stocks eventually updated

#### `test_failed_fetch_isolation()`
- **Purpose**: Verify failed fetch for one stock doesn't affect others
- **Given**: API failure for AAPL, success for GOOGL/MSFT
- **When**: Fetch cycle completes
- **Then**: GOOGL/MSFT data is processed normally
- **Assertions**: Partial failure handled, successful data processed

#### `test_staggered_fetch_timing()`
- **Purpose**: Verify fetch timing can be staggered to avoid API bursts
- **Given**: Staggered timing configuration
- **When**: Fetch cycles execute
- **Then**: API calls are spread over time
- **Assertions**: Timing distribution matches configuration

### Signal-Based Alert Processing Tests

#### `test_child_alert_signal_generation()`
- **Purpose**: Verify child workflows generate proper alert signals
- **Given**: StockMonitoringWorkflow detecting threshold breach
- **When**: Alert condition is met
- **Then**: Structured alert signal is sent to parent
- **Assertions**: Signal contains stock symbol, alert type, market data, confidence level

#### `test_parent_signal_evaluation()`
- **Purpose**: Verify parent workflow evaluates received signals correctly
- **Given**: MultiStockMonitoringWorkflow receiving alert signal
- **When**: EvaluateSignal activity is executed
- **Then**: Signal is analyzed and action is determined
- **Assertions**: Signal processed, risk assessed, action plan generated

#### `test_simultaneous_signal_processing()`
- **Purpose**: Verify parent can process multiple simultaneous signals
- **Given**: Multiple children sending alerts simultaneously
- **When**: All signals arrive at parent
- **Then**: Each signal is evaluated independently
- **Assertions**: No signal loss, proper evaluation order, all children acknowledged

#### `test_signal_based_plan_updates()`
- **Purpose**: Verify monitoring plans can be updated via signals
- **Given**: Parent workflow with evaluation results
- **When**: Plan update is needed based on market conditions
- **Then**: UpdateMonitoringPlan activity generates new plans for children
- **Assertions**: New plans generated, signals sent to children, plans updated

### Performance & Scalability Tests

#### `test_parent_child_performance_scaling()`
- **Purpose**: Verify parent-child architecture scales with stock count
- **Given**: MultiStockMonitoringWorkflow with 10+ child workflows
- **When**: System operates under normal load
- **Then**: Signal processing and evaluation remain efficient
- **Assertions**: Signal latency < 50ms, evaluation throughput maintained

#### `test_signal_communication_overhead()`
- **Purpose**: Verify signal communication doesn't create performance bottlenecks
- **Given**: High frequency of signals between parent and children
- **When**: Signal throughput is measured
- **Then**: Communication overhead remains minimal
- **Assertions**: Signal processing < 10ms, no queue buildup

#### `test_child_workflow_resource_isolation()`
- **Purpose**: Verify child workflows don't interfere with each other's performance
- **Given**: Multiple child workflows with different monitoring frequencies
- **When**: Resource usage is monitored
- **Then**: Each child operates independently without blocking
- **Assertions**: No resource contention, independent execution confirmed

#### `test_parent_evaluation_activity_performance()`
- **Purpose**: Verify evaluation activities can handle concurrent signal processing
- **Given**: Multiple signals arriving simultaneously at parent
- **When**: EvaluateSignal activities are executed
- **Then**: All evaluations complete within acceptable time
- **Assertions**: Evaluation time < 100ms per signal, no blocking between evaluations

### Data Consistency Tests

#### `test_timestamp_synchronization()`
- **Purpose**: Verify timestamps are synchronized across all stock data
- **Given**: Data fetched for multiple stocks
- **When**: Timestamps are compared
- **Then**: All timestamps are within acceptable variance
- **Assertions**: Time drift < 1 second across all stocks

#### `test_data_integrity_across_stocks()`
- **Purpose**: Verify data integrity is maintained for all stocks
- **Given**: Data processing for multiple stocks
- **When**: Data validation occurs
- **Then**: All data passes integrity checks
- **Assertions**: No data corruption, validation passes

#### `test_atomic_updates_across_stocks()`
- **Purpose**: Verify updates are atomic within each stock's context
- **Given**: Price updates for multiple stocks
- **When**: System failure occurs during update
- **Then**: Each stock's data remains consistent
- **Assertions**: No partial updates, data consistency maintained

### Error Handling & Recovery Tests

#### `test_partial_system_failure_recovery()`
- **Purpose**: Verify recovery when some stocks fail monitoring
- **Given**: API failure for subset of stocks
- **When**: System attempts recovery
- **Then**: Failed stocks resume monitoring when possible
- **Assertions**: Selective recovery, working stocks unaffected

#### `test_cascading_failure_prevention()`
- **Purpose**: Verify failure in one stock doesn't cascade to others
- **Given**: Critical error in one stock's workflow
- **When**: Error occurs
- **Then**: Other workflows continue normally
- **Assertions**: Error containment, no cascade effect

#### `test_system_recovery_after_total_failure()`
- **Purpose**: Verify system can recover all stocks after total failure
- **Given**: Complete system failure
- **When**: System restarts
- **Then**: All stock monitoring resumes
- **Assertions**: Full recovery, all workflows restored

### Monitoring & Observability Tests

#### `test_parent_workflow_metrics_collection()`
- **Purpose**: Verify metrics are collected for MultiStockMonitoringWorkflow
- **Given**: Parent workflow managing multiple children
- **When**: Metrics collection occurs
- **Then**: Parent workflow metrics are captured (signal processing, evaluation times)
- **Assertions**: Parent metrics available, child count tracked, signal throughput measured

#### `test_child_workflow_metrics_aggregation()`
- **Purpose**: Verify child workflow metrics are aggregated at parent level
- **Given**: Multiple child workflows with individual metrics
- **When**: Aggregation is performed
- **Then**: System-wide metrics are calculated from child data
- **Assertions**: Aggregation accurate, per-stock and total metrics available

#### `test_signal_communication_monitoring()`
- **Purpose**: Verify signal communication is monitored and tracked
- **Given**: Active signal communication between parent and children
- **When**: Communication monitoring occurs
- **Then**: Signal metrics are captured (frequency, latency, success rate)
- **Assertions**: Signal metrics accurate, communication health tracked

#### `test_workflow_hierarchy_health_checks()`
- **Purpose**: Verify health checks work for parent-child workflow hierarchy
- **Given**: MultiStockMonitoringWorkflow with child workflows
- **When**: Health check is requested
- **Then**: Hierarchical health status is reported
- **Assertions**: Parent health status, child health status, signal communication health

### Configuration Management Tests

#### `test_hot_reload_stock_configuration()`
- **Purpose**: Verify stock configuration can be reloaded without restart
- **Given**: Running system with stock configuration
- **When**: Configuration is updated and reloaded
- **Then**: Changes take effect without system restart
- **Assertions**: Hot reload successful, no service interruption

#### `test_configuration_validation_with_multiple_stocks()`
- **Purpose**: Verify configuration validation works with complex setups
- **Given**: Complex multi-stock configuration
- **When**: Validation is performed
- **Then**: All aspects are validated correctly
- **Assertions**: Comprehensive validation, clear error messages

#### `test_configuration_rollback()`
- **Purpose**: Verify ability to rollback configuration changes
- **Given**: Configuration change that causes issues
- **When**: Rollback is initiated
- **Then**: Previous configuration is restored
- **Assertions**: Rollback successful, system stability restored

### Integration Tests

#### `test_end_to_end_signal_based_monitoring()`
- **Purpose**: Verify complete parent-child signal-based monitoring flow
- **Given**: MultiStockMonitoringWorkflow configured for AAPL, GOOGL, MSFT
- **When**: Complete monitoring cycle runs with signal communication
- **Then**: Children monitor stocks, send signals to parent, parent evaluates and responds
- **Assertions**: Complete signal flow verified, evaluation activities executed, actions taken

#### `test_llm_plan_generation_integration()`
- **Purpose**: Verify LLM planning integrates with signal-based monitoring
- **Given**: Market conditions requiring plan updates
- **When**: Parent receives signals and determines plan updates needed
- **Then**: LLM generates new plans, signals sent to children, monitoring updated
- **Assertions**: LLM integration working, plans updated, children receive new instructions

#### `test_evaluation_to_trading_integration()`
- **Purpose**: Verify signal evaluation leads to trading decisions
- **Given**: Alert signals indicating trading opportunities
- **When**: Parent evaluates signals and determines trading action needed
- **Then**: Trading workflow is initiated with evaluated recommendations
- **Assertions**: Evaluation results passed to trading, trading workflow started, risk assessment included

### Load Testing

#### `test_10_stock_concurrent_monitoring()`
- **Purpose**: Verify system can handle 10 stocks concurrently
- **Given**: 10 stocks configured for monitoring
- **When**: System runs for extended period
- **Then**: All stocks are monitored reliably
- **Assertions**: Performance acceptable, no failures

#### `test_50_stock_monitoring_capacity()`
- **Purpose**: Verify system capacity with 50 stocks
- **Given**: 50 stocks configured
- **When**: System operates under load
- **Then**: System handles load within limits
- **Assertions**: Resource usage acceptable, response times good

#### `test_burst_load_handling()`
- **Purpose**: Verify system handles burst loads across all stocks
- **Given**: Sudden spike in market activity
- **When**: All stocks require rapid processing
- **Then**: System handles burst without failure
- **Assertions**: Burst handled, no data loss

### Data Storage Tests

#### `test_multi_stock_data_partitioning()`
- **Purpose**: Verify data is properly partitioned by stock
- **Given**: Data from multiple stocks
- **When**: Data is stored
- **Then**: Each stock's data is properly partitioned
- **Assertions**: Data isolation, efficient queries

#### `test_cross_stock_data_queries()`
- **Purpose**: Verify ability to query data across multiple stocks
- **Given**: Historical data for multiple stocks
- **When**: Cross-stock query is executed
- **Then**: Correct data is returned
- **Assertions**: Query results accurate, performance acceptable

#### `test_data_retention_per_stock()`
- **Purpose**: Verify data retention policies work per stock
- **Given**: Different retention policies per stock
- **When**: Cleanup process runs
- **Then**: Correct data is retained/removed per stock
- **Assertions**: Retention policies enforced correctly

## Success Criteria
- All multi-stock tests pass
- System can monitor 10+ stocks simultaneously
- Individual stock failures don't affect others
- Performance scales linearly with stock count
- Memory usage remains stable under load
- All stocks maintain independent alert thresholds
- System recovers gracefully from partial failures
- Cross-stock correlation analysis works correctly