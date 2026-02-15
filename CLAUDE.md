# Maverick

AI-powered prediction market analysis system. Uses deep reasoning to find mispriced markets on Kalshi.

## Philosophy

**The market has the same information you do. The edge is processing it better.**

- **Python tools** = deterministic math, API access, persistence
- **AI agents** = reasoning, filtering, judgment, analysis

## Quick Start

```bash
# Initialize database (one-time)
python scripts/init_db.py

# Scan for opportunities (use Finder agent)
# Analyze with first principles (use Reasoner agent)
# Size positions (use kelly.py)
```

## Agents

Eight specialized agents in `.claude/agents/`:

| Agent | Purpose |
|-------|---------|
| **finder** | Scan markets for reasoning opportunities |
| **reasoner** | First-principles analysis, causal chains |
| **forecaster** | Base rates, calibration, Bayesian updating |
| **researcher** | Targeted fact-finding (on demand) |
| **devils-advocate** | Attack theses, find flaws |
| **philosopher** | Question assumptions, framing, unknowns |
| **quant** | Kelly sizing, risk limits, portfolio |
| **market-maker** | Liquidity, spreads, execution |

## Skills

Shared frameworks in `.claude/skills/`:

| Skill | Purpose |
|-------|---------|
| **kalshi-tools** | Tool catalog: kelly.py, kalshi_client.py, db, analytics |
| **kelly-sizing** | Position sizing framework |
| **probability-estimation** | Base rates, reference classes, calibration |
| **triage-markets** | Multi-agent orchestration workflow |

## Python Tools

Minimal deterministic toolset:

| File | Purpose |
|------|---------|
| `kelly.py` | Position sizing (CLI + library) |
| `kalshi_client.py` | Kalshi API client |
| `src/db.py` | SQLite persistence |
| `src/analytics.py` | Calibration, Brier scores |
| `src/models.py` | Data models |

### Kelly CLI

```bash
# Position sizing
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence medium

# Payout analysis
python kelly.py --bet 1000 --market-prob 0.45 --direction NO --days 14
```

### Kalshi Client

```python
from kalshi_client import KalshiClient, KalshiExplorer

client = KalshiClient(demo=True)
markets = client.get_markets(limit=100, status='open')
market = client.get_market("TICKER")
```

## Workflow

1. **Find** - Finder agent scans for short-term, reasoning-amenable markets
2. **Reason** - Reasoner applies first principles before any research
3. **Calibrate** - Forecaster checks base rates and confidence
4. **Challenge** - Devil's Advocate attacks the thesis
5. **Size** - Quant calculates Kelly position
6. **Execute** - Market Maker checks liquidity and true edge
7. **Record** - Store prediction in database for calibration tracking

## Documentation

Deeper strategic context in `docs/`:

- `THESIS.md` - Core philosophy and reasoning edge
- `AI_EDGE.md` - Domain expertise strategy
- `PLAYBOOK.md` - Daily operations reference

## Key Principles

1. **Reasoning before research** - Think first, don't anchor on headlines
2. **Capital velocity** - Short-term bets compound faster
3. **Kelly discipline** - Never exceed fractional Kelly
4. **Falsifiability** - Know what would change your mind
5. **Track calibration** - Measure Brier scores over time
