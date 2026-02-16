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

# Run the operating model with /operate
# Creates 3 tasks: Find → Research → Challenge
# 11 subagents total (3 finders + 3 researchers + 1 verifier + 3 challengers + 1 verifier)
# Orchestrator synthesizes final report with probability estimates
```

## Skills

Shared frameworks in `.claude/skills/`:

| Skill | Invocation | Purpose |
|-------|------------|---------|
| **operating-model** | `/operate` | Find → Research → Challenge with parallel subagents |
| **kalshi-tools** | - | Tool catalog: kelly.py, kalshi_client.py, db, analytics |
| **kelly-sizing** | - | Position sizing framework |
| **probability-estimation** | - | Base rates, reference classes, calibration |

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
from kalshi_client import KalshiClient

client = KalshiClient(demo=False)
market = client.get_market("TICKER")
results = client.search_markets("inflation")
```

## Workflow: The Operating Model

Run with `/operate`. Task-list driven with parallel subagents.

**Tasks:**
1. **Find bets** - 3 finders (economics, politics, tech) → orchestrator picks top 3
2. **Research bets** - 3 researchers (1 per candidate) → verifier approves
3. **Challenge & vet** - 3 challengers (1 per candidate) → verifier approves

**Final:** Orchestrator synthesizes report with probability estimates, edge, recommendations.

| Step | Subagents | What Happens |
|------|-----------|--------------|
| Find | 3 parallel | Search different categories, return candidates |
| Research | 3 parallel + verifier | Deep research on each candidate |
| Challenge | 3 parallel + verifier | Attack thesis, find holes |
| Synthesize | orchestrator | Probability estimates, Kelly sizing, final report |

**Key protocol:** No self-signoff. Only verifiers mark tasks complete.

**Time budget:** 5-7 minutes total.

See `operating-model` skill for full details.

## Documentation

Deeper strategic context in `docs/`:

- `THESIS.md` - Core philosophy and reasoning edge
- `PLAYBOOK.md` - Daily operations reference

## Key Principles

1. **Parallel by default** - 3 subagents per step, run simultaneously
2. **Verifiers approve** - No self-signoff, verifiers mark tasks complete
3. **Research before reasoning** - Gather facts first
4. **Edge > 10 points** - Don't trade marginal opportunities
5. **Kelly discipline** - Never exceed fractional Kelly
6. **Track calibration** - Measure Brier scores over time
