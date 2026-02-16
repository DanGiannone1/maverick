---
name: kalshi-tools
description: |
  Deterministic Python tools for Kalshi prediction markets.
  Covers API access, position sizing, and persistence.
---

# Kalshi Tools

Minimal Python toolset for prediction market operations. Agents handle filtering, reasoning, and workflows.

## Philosophy

- **Python** = math, I/O, persistence (deterministic)
- **Agents** = filtering, reasoning, analysis (judgment)

---

## API Client: `kalshi_client.py`

Core client for Kalshi API access.

### Error Handling

```python
from kalshi_client import (
    KalshiClient, KalshiExplorer, Market, Event,
    KalshiError, KalshiAuthError, KalshiRateLimitError,
    KalshiNotFoundError, KalshiNetworkError, KalshiServerError
)

# Errors are returned as dicts by default
result = client.get_market("INVALID")
if 'error' in result:
    print(result['error'])   # 'not_found', 'auth', 'rate_limit', 'timeout', etc.
    print(result['message'])
```

### Basic Usage

```python
from kalshi_client import KalshiClient, KalshiExplorer, Market, Event

# Initialize client (demo=True for paper trading)
client = KalshiClient(demo=True)

# Get events (grouped market collections)
events = client.get_events(limit=100)
events = client.get_all_events(category="Politics")

# Get markets
markets = client.get_markets(limit=100, status='open')
markets = client.get_markets(event_ticker="FED-26MAR12")
market = client.get_market(ticker="FED-26MAR12-T4.25")

# Search
events = client.search_events("federal reserve")
markets = client.search_markets("inflation")

# Orderbook
orderbook = client.get_orderbook(ticker, depth=10)

# Portfolio (authenticated)
balance = client.get_balance()
positions = client.get_positions()
orders = client.get_orders()
fills = client.get_fills(limit=100)

# Trading (authenticated)
order = client.place_order(ticker, side='yes', count=10, price=45)
client.cancel_order(order_id)
```

### Market Properties

```python
market.ticker        # Unique identifier
market.title         # Human-readable title
market.yes_bid       # Best bid (cents, 0-100)
market.yes_ask       # Best ask (cents, 0-100)
market.yes_mid       # Mid price (0-1 scale)
market.spread        # Bid-ask spread (cents)
market.volume        # Total volume
market.volume_24h    # 24-hour volume
market.open_interest # Open contracts
market.liquidity     # Available liquidity
market.close_time    # Resolution date
market.category      # Market category
```

### Explorer (High-Level Interface)

```python
from kalshi_client import KalshiExplorer

explorer = KalshiExplorer(demo=True)

# Overview
overview = explorer.overview()

# Filtering
markets = explorer.filter_markets(
    min_price=0.2, max_price=0.8,
    min_volume=100, max_spread=10,
    title_contains="fed"
)

# Pre-built filters
liquid = explorer.find_liquid_markets(min_volume=100, min_liquidity=1000)
tight = explorer.find_tight_spreads(max_spread=5)
close_calls = explorer.find_close_calls(price_range=(0.4, 0.6))
longshots = explorer.find_longshots(max_price=0.15)
favorites = explorer.find_favorites(min_price=0.85)

# Analysis
summary = explorer.market_summary(market)
stats = explorer.category_stats()
```

---

## Position Sizing: `kelly.py`

Deterministic Kelly criterion calculations.

### CLI Usage

```bash
# Kelly sizing
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence medium
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence high --bankroll 10000
python kelly.py --our-prob 0.30 --market-prob 0.45 --time-horizon months

# Payout analysis
python kelly.py --bet 1000 --market-prob 0.45 --direction NO --days 14
```

### Library Usage

```python
from kelly import calculate_kelly, calculate_payout, calculate_edge

# Kelly calculation
result = calculate_kelly(
    our_prob=0.30,
    market_prob=0.45,
    confidence="medium",      # low/medium/high
    time_horizon="weeks"      # days/weeks/months/quarters/years
)
print(result.direction)       # BUY_YES, BUY_NO, NO_TRADE
print(result.edge)            # 0.15
print(result.full_kelly)      # Full Kelly fraction
print(result.recommended)     # After confidence adjustment

# Payout calculation
payout = calculate_payout(
    bet_amount=1000,
    market_prob=0.45,
    direction="NO",
    days_to_resolution=14
)
print(payout['profit_if_win'])
print(payout['annualized_return'])
```

### Confidence Multipliers

| Confidence | Kelly Fraction |
|------------|----------------|
| low | 25% |
| medium | 40% |
| high | 50% |

### Time Multipliers

| Horizon | Multiplier |
|---------|------------|
| days | 1.0 |
| weeks | 0.7 |
| months | 0.5 |
| quarters | 0.3 |
| years | 0.2 |

---

## Database CLI: `db_cli.py`

Command-line interface for agents to store and query predictions.

### Store Predictions

```bash
# Basic prediction
python db_cli.py store --ticker KXFED-26FEB15 --agent reasoner \
    --probability 0.30 --confidence 0.7 --market-price 0.45 \
    --category economics

# With reasoning trace
python db_cli.py store --ticker KXFED-26FEB15 --agent reasoner \
    --probability 0.30 --confidence 0.7 --market-price 0.45 \
    --reasoning "Fed unlikely to cut due to..." \
    --factors "inflation,employment" --unknowns "geopolitics"
```

### Resolve Predictions

```bash
python db_cli.py resolve --ticker KXFED-26FEB15 \
    --prediction-id pred_abc123 --outcome NO
```

### Query Data

```bash
# Recent predictions
python db_cli.py recent --limit 20 --agent reasoner

# Unresolved markets
python db_cli.py unresolved

# Calibration report
python db_cli.py calibration --agent reasoner --days 90

# Agent performance
python db_cli.py agent-stats --agent reasoner

# Category breakdown
python db_cli.py category-stats --days 30

# Get specific prediction
python db_cli.py get --prediction-id pred_abc123
```

### Initialize

```bash
python db_cli.py init
```

---

## Database Library: `src/db.py`

Direct Python access for persistence.

```python
from src.db import init_db, store_prediction, get_prediction, store_outcome
from src.models import Prediction, ReasoningTrace

# Initialize (one-time)
init_db()

# Store prediction
prediction = Prediction.create(
    ticker="FED-26MAR12-T4.25",
    agent_name="reasoner",
    probability=0.25,
    confidence=0.7,
    market_price=0.35,
    category="economics"
)
reasoning = ReasoningTrace.create(
    prediction_id=prediction.id,
    reasoning_text="First principles analysis...",
    key_factors=["Fed signaling", "Inflation data"],
    unknowns=["Geopolitical events"],
    base_rate_used=0.15
)
pred_id = store_prediction(prediction, reasoning)

# Retrieve
pred = get_prediction(pred_id)
preds = get_predictions_for_ticker("FED-26MAR12-T4.25")

# Resolve (when market settles)
outcome_id, brier_score = store_outcome(
    ticker="FED-26MAR12-T4.25",
    actual_outcome=1,  # 1=YES, 0=NO
    prediction_id=pred_id
)
```

---

## Analytics: `src/analytics.py`

Calibration and performance tracking.

```python
from src.analytics import (
    calibration_report,
    agent_performance,
    recent_predictions,
    unresolved_markets,
    format_calibration_report
)

# Calibration by probability bucket
buckets = calibration_report(agent_name="reasoner", days=30)
print(format_calibration_report(buckets))

# Agent performance
stats = agent_performance("reasoner", days=30)
print(f"Brier: {stats.avg_brier_score:.3f}")
print(f"Win rate: {stats.win_rate:.1%}")

# Recent predictions
recent = recent_predictions(limit=20)

# Markets needing resolution
pending = unresolved_markets()
```

---

## Setup

```bash
# Initialize database (one-time)
python scripts/init_db.py

# Verify setup
python scripts/test_db.py
```

---

## File Structure

```
maverick/
├── kelly.py              # Position sizing (CLI + library)
├── kalshi_client.py      # API client (CLI + library)
├── db_cli.py             # Database CLI for agents
├── requirements.txt      # Python dependencies
├── src/
│   ├── models.py         # Data models (Prediction, Outcome, etc.)
│   ├── db.py             # SQLite persistence
│   └── analytics.py      # Calibration, Brier scores
├── data/
│   └── maverick.db       # SQLite database
└── scripts/
    ├── init_db.py        # Database initialization
    └── test_db.py        # Verification script
```
