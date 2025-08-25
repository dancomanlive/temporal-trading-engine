# Stock Trading System with Temporal

A stock trading system built with Temporal workflows for durable, reliable trading operations.

## Quick Start

```bash
# Build & start Temporal + worker
make up

# Stop & cleanup
make down
```

## Features

- Real-time stock price monitoring
- Multi-stock monitoring workflows
- Broker abstraction layer for different trading platforms
- Temporal workflow execution with durability and audit trails
- Mock broker mode for testing
- Docker + docker-compose setup
- Comprehensive test suite

## Environment Variables

- `BROKER_TYPE` — broker implementation to use (default: `mock`)
- `TEMPORAL_ADDRESS` — optional, default `localhost:7233`

## Testing

```bash
make test
```

## Architecture

1. Stock monitoring workflows track price changes
2. Broker abstraction layer handles different trading platforms
3. Activities execute trading operations (fetch prices, execute trades)
4. Temporal handles durability, retries, and audit trail
5. Signal-based communication between parent and child workflows