# TDD Implementation Guide for Stock Trading System

## Overview
This guide explains how to implement the stock trading system using Test-Driven Development (TDD) with AI assistance. The approach focuses on implementing one test at a time while following the established architecture patterns.

## TDD Workflow with AI

### Step 1: Context Preparation
For each test implementation, provide the AI with:

1. **Architecture Patterns** - Always include `architecture_patterns.md` as context
2. **Specific Test** - One test from the relevant slice specification
3. **Current Codebase State** - Relevant existing files that need to be modified

### Step 2: AI Instructions Template

```
Implement this specific test using TDD (Red-Green-Refactor):

[PASTE SINGLE TEST FROM SLICE SPEC]

Context:
- Follow the architecture patterns in architecture_patterns.md
- Use direct workflow instantiation and Temporal infrastructure
- Implement only what's needed to make THIS test pass
- Follow the established code conventions

Steps:
1. Write the failing test first (Red)
2. Implement minimal code to make it pass (Green)
3. Refactor if needed while keeping test green

Do not implement multiple tests or add extra functionality.
```

### Step 3: Implementation Order

Follow this logical sequence for implementing tests:

#### Phase 1: Foundation (Slice 1 - Basic Stock Monitoring)
1. **Broker Integration Tests** (Foundation)
   - `test_broker_client_initialization()`
   - `test_broker_authentication()`
   - `test_fetch_stock_price_success()`
   - `test_fetch_stock_price_invalid_symbol()`

2. **Data Model Tests**
   - `test_stock_data_model_creation()`
   - `test_stock_data_validation()`
   - `test_price_data_serialization()`

3. **Basic Monitor Activity Tests**
   - `test_monitor_stock_activity_creation()`
   - `test_monitor_stock_activity_execution()`
   - `test_monitor_stock_activity_error_handling()`

4. **Workflow Orchestration Tests**
   - `test_basic_monitor_workflow_creation()`
   - `test_monitor_workflow_execution()`
   - `test_workflow_with_base_workflow_integration()`

#### Phase 2: Alert System (Slice 2)
5. **Alert Configuration Tests**
6. **Alert Detection Tests**
7. **Alert Delivery Tests**

#### Phase 3: Multi-Stock Monitoring (Slice 3)
8. **Parallel Processing Tests**
9. **Multi-Stock Configuration Tests**
10. **Performance Tests**

#### Continue with remaining slices...

## Detailed Implementation Examples

### Example 1: Implementing Foundation Test

**AI Context:**
```
Implement this specific test using TDD:

#### `test_broker_client_initialization()`
- **Purpose**: Verify broker client can be initialized with credentials
- **Given**: Valid API credentials
- **When**: Client is initialized
- **Then**: Client is ready for API calls
- **Assertions**: Client object created, credentials validated

Context:
- Follow architecture_patterns.md
- Create the minimal broker integration needed
- Use the activity pattern from the architecture guide
- Only implement what's needed for this test
```

**Expected AI Output:**
1. Create failing test in `tests/activities/test_broker_integration.py`
2. Create minimal `activities/broker_client.py` with initialization
3. Register activity in workers/monitoring_worker.py
4. Make test pass with minimal implementation

### Example 2: Implementing Activity Test

**AI Context:**
```
Implement this specific test using TDD:

#### `test_fetch_stock_price_success()`
- **Purpose**: Verify stock price can be fetched successfully
- **Given**: Valid stock symbol
- **When**: Price fetch activity is executed
- **Then**: Current price is returned
- **Assertions**: Price data structure correct, timestamp included

Context:
- Follow architecture_patterns.md activity implementation pattern
- Use the existing Temporal activity decorator
- Return structured results as shown in architecture guide
- Mock broker API calls in tests
```

**Expected AI Output:**
1. Create failing test with mocked broker API
2. Implement `FetchStockPrice` activity following architecture pattern
3. Register activity in main_worker.py
4. Make test pass with proper error handling

### Example 3: Implementing Workflow Test

**AI Context:**
```
Implement this specific test using TDD:

#### `test_basic_monitor_workflow_creation()`
- **Purpose**: Verify basic monitoring workflow can be created
- **Given**: Stock symbol and monitoring parameters
- **When**: Workflow is instantiated
- **Then**: Workflow is ready for execution
- **Assertions**: Workflow object created, parameters stored

Context:
- Follow architecture_patterns.md workflow implementation pattern
- Use Temporal workflow decorator
- Follow the StockMonitorWorkflow example from architecture guide
- Use direct workflow instantiation pattern
```

**Expected AI Output:**
1. Create failing workflow test using Temporal testing framework
2. Implement basic `StockMonitorWorkflow` class
3. Register workflow in workers/monitoring_worker.py
4. Make test pass with minimal workflow logic

## AI Instruction Best Practices

### Do's:
- ✅ Provide exactly one test to implement
- ✅ Always include architecture_patterns.md as context
- ✅ Specify which files need to be created/modified
- ✅ Ask for Red-Green-Refactor approach
- ✅ Emphasize following existing patterns
- ✅ Request minimal implementation

### Don'ts:
- ❌ Don't ask AI to implement multiple tests at once
- ❌ Don't provide entire slice specifications
- ❌ Don't ask for complete feature implementation
- ❌ Don't skip the failing test step
- ❌ Don't ask for extra functionality beyond the test

## File Organization Strategy

### Test Files Structure
```
tests/
├── activities/
│   ├── test_broker_integration.py
│   ├── test_stock_data.py
│   ├── test_trading.py
│   └── test_analysis.py
├── workflows/
│   ├── test_monitoring.py
│   ├── test_trading.py
│   └── test_portfolio.py
├── integration/
│   ├── test_base_workflow_integration.py
│   ├── test_end_to_end.py
│   └── test_slice_integration.py
└── fixtures/
    ├── mock_data.py
    └── test_helpers.py
```

### Implementation Files Structure
```
activities/
├── broker_client.py
├── stock_data.py
├── trading.py
└── analysis.py

workflows/
├── monitoring.py
├── trading.py
└── portfolio.py
```

## Mock and Fixture Strategy

### Mock Broker API
```python
# tests/fixtures/mock_broker.py
class MockBrokerClient:
    def __init__(self):
        self.is_authenticated = True
    
    async def get_latest_quote(self, symbol):
        return MockQuote(symbol=symbol, ask_price=150.25)

# Use in tests
@pytest.fixture
def mock_broker_client(monkeypatch):
    mock_client = MockBrokerClient()
    monkeypatch.setattr("activities.broker_client.broker_client", mock_client)
    return mock_client
```

### Test Data Fixtures
```python
# tests/fixtures/test_data.py
@pytest.fixture
def sample_stock_data():
    return {
        "symbol": "AAPL",
        "price": 150.25,
        "timestamp": "2024-01-15T10:30:00Z",
        "volume": 1000000
    }

@pytest.fixture
def sample_portfolio():
    return {
        "cash": 10000.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 10, "avg_cost": 145.0},
            {"symbol": "GOOGL", "quantity": 5, "avg_cost": 2800.0}
        ]
    }
```

## Progress Tracking

### Test Implementation Checklist
For each slice, track progress:

```markdown
## Slice 1: Basic Stock Monitoring
- [ ] test_broker_client_initialization
- [ ] test_broker_authentication  
- [ ] test_fetch_stock_price_success
- [ ] test_fetch_stock_price_invalid_symbol
- [ ] test_stock_data_model_creation
- [ ] test_stock_data_validation
- [ ] test_monitor_stock_activity_creation
- [ ] test_monitor_stock_activity_execution
- [ ] test_basic_monitor_workflow_creation
- [ ] test_monitor_workflow_execution
```

### Implementation Status
Track which components are implemented:

```markdown
## Implementation Status
### Activities
- [ ] BrokerClient (initialization, authentication)
- [ ] FetchStockPrice
- [ ] MonitorStock
- [ ] SendAlert

### Workflows  
- [ ] StockMonitorWorkflow
- [ ] BasicScannerWorkflow

### Worker Registration
- [ ] Activities registered in workers/monitoring_worker.py
- [ ] Workflows registered in workers/monitoring_worker.py
```

## Quality Gates

### Before Moving to Next Test
- ✅ Current test passes
- ✅ All existing tests still pass
- ✅ Code follows architecture patterns
- ✅ Proper error handling implemented
- ✅ Worker registration updated if needed
- ✅ No extra functionality beyond test requirements

### Before Moving to Next Slice
- ✅ All slice tests pass
- ✅ Integration tests pass
- ✅ End-to-end test for slice works
- ✅ Documentation updated
- ✅ Performance requirements met

## Example AI Conversation Flow

### Conversation 1: First Test
```
Human: Implement the first test from Slice 1 using TDD.

[Include architecture_patterns.md and test_broker_client_initialization spec]

AI: I'll implement the failing test first, then create the minimal BrokerClient to make it pass.

[Creates test file, implements minimal client, updates worker registration]
```

### Conversation 2: Second Test
```
Human: Now implement the next test: test_broker_authentication

[Include architecture_patterns.md and test spec]

AI: I'll add the authentication test and extend the BrokerClient with authentication logic.

[Adds test, implements auth, makes test pass]
```

### Conversation 3: Activity Test
```
Human: Implement test_fetch_stock_price_success

[Include architecture_patterns.md, test spec, and current BrokerClient code]

AI: I'll create the FetchStockPrice activity following the architecture pattern.

[Creates activity test, implements activity, registers in workers/monitoring_worker]
```

This approach ensures:
- ✅ One test at a time (focused implementation)
- ✅ Architecture patterns followed consistently
- ✅ Minimal implementation (no over-engineering)
- ✅ Proper TDD cycle (Red-Green-Refactor)
- ✅ Integration with existing infrastructure
- ✅ Quality gates at each step

## Summary

The key to successful TDD implementation is:
1. **One test at a time** - Never ask AI to implement multiple tests
2. **Architecture context** - Always provide architecture_patterns.md
3. **Minimal implementation** - Only implement what's needed for the current test
4. **Follow patterns** - Use the established direct workflow patterns
5. **Quality gates** - Ensure each test passes before moving to the next

This approach will result in a robust, well-tested stock trading system that follows your established architecture patterns.