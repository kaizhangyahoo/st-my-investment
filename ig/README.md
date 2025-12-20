# IG WebAPI Python Client

A Python-native client library for interacting with IG's REST and Streaming APIs, translated from the official `ig-webapi-java-sample`.

## Features
- **REST API Support**: Comprehensive session management (V2/V3), position retrieval, and basic trading operations.
- **Streaming Client**: Lightstreamer-compatible websocket client for real-time market data.
- **Data Models**: Structured dataclasses for `UserSession`, `Position`, and `MarketData`.

## Directory Structure
- `__init__.py`: Package entry point.
- `rest.py`: `IGRestClient` implementation.
- `streaming.py`: `IGStreamingClient` for real-time updates.
- `models.py`: Dataclasses for API entities.
- `utils.py`: Helper functions for formatting and encryption.
- `sample.py`: Example console application.

## Getting Started

### Prerequisites
Ensure you have the following dependencies installed:
```bash
pip install requests websocket-client
```

### Usage
1. Create a `no_git_push.json` file in the root directory (this is git-ignored) with your credentials:
```json
{
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "api_key": "YOUR_API_KEY",
    "acc_type": "DEMO"
}
```

2. Run the sample script to verify connection:
```bash
python ig/sample.py
```

## Implementation Details
- **Authentication**: Supports Version 3 (OAuth) authentication.
- **Lightstreamer**: Implements a basic websocket wrapper for IG's Lightstreamer endpoint. 
