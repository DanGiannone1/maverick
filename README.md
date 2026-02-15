# Maverick

AI-powered prediction market analysis. Uses deep reasoning to find mispriced markets.

## Setup

```bash
# Install dependencies
pip install requests cryptography python-dotenv

# Configure API keys in .env
cp .env.example .env

# Initialize database
python scripts/init_db.py
```

## Usage

See [CLAUDE.md](CLAUDE.md) for full documentation.

```bash
# Position sizing
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence medium

# Market data
python -c "from kalshi_client import KalshiClient; c = KalshiClient(demo=True); print(c.get_markets(limit=5))"
```

## Architecture

- **Python tools** (`kelly.py`, `kalshi_client.py`, `src/`) - Deterministic operations
- **AI agents** (`.claude/agents/`) - Reasoning and analysis
- **Skills** (`.claude/skills/`) - Shared frameworks

## License

Private.
