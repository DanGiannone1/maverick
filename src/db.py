"""SQLite database layer for maverick prediction system."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    Market, MarketSnapshot, Outcome, Prediction, ReasoningTrace, Trade
)

# Default database path
DB_PATH = Path(__file__).parent.parent / "data" / "maverick.db"


def get_db_path() -> Path:
    """Get the database path, creating data directory if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
-- Predictions table: Every probability estimate with edge calculation
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    probability REAL NOT NULL,
    confidence REAL NOT NULL,
    market_price REAL NOT NULL,
    edge REAL NOT NULL,
    category TEXT,
    subcategory TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_agent_name ON predictions(agent_name);

-- Reasoning traces: Full AI reasoning text + key factors
CREATE TABLE IF NOT EXISTS reasoning_traces (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    reasoning_text TEXT NOT NULL,
    key_factors TEXT,  -- JSON array
    unknowns TEXT,     -- JSON array
    base_rate_used REAL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

CREATE INDEX IF NOT EXISTS idx_reasoning_prediction ON reasoning_traces(prediction_id);

-- Markets: Market metadata (ticker, category, resolution)
CREATE TABLE IF NOT EXISTS markets (
    ticker TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    close_time TEXT,
    resolution_time TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    result TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);

-- Market snapshots: Price history over time
CREATE TABLE IF NOT EXISTS market_snapshots (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    yes_price REAL NOT NULL,
    no_price REAL NOT NULL,
    volume INTEGER NOT NULL DEFAULT 0,
    open_interest INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES markets(ticker)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_ticker ON market_snapshots(ticker);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON market_snapshots(timestamp);

-- Outcomes: Resolution + Brier scores
CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    prediction_id TEXT NOT NULL,
    actual_outcome INTEGER NOT NULL,
    predicted_probability REAL NOT NULL,
    brier_score REAL NOT NULL,
    resolved_at TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES markets(ticker),
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_ticker ON outcomes(ticker);
CREATE INDEX IF NOT EXISTS idx_outcomes_prediction ON outcomes(prediction_id);

-- Trades: Execution tracking (future use)
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    contracts INTEGER NOT NULL,
    price REAL NOT NULL,
    filled_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id),
    FOREIGN KEY (ticker) REFERENCES markets(ticker)
);

CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
CREATE INDEX IF NOT EXISTS idx_trades_prediction ON trades(prediction_id);
"""


def init_db(db_path: Optional[Path] = None) -> Path:
    """Initialize the database schema. Returns the database path."""
    path = db_path or get_db_path()
    with get_connection(path) as conn:
        conn.executescript(SCHEMA)
    return path


# =============================================================================
# Prediction Operations
# =============================================================================

def store_prediction(prediction: Prediction,
                     reasoning: Optional[ReasoningTrace] = None,
                     db_path: Optional[Path] = None) -> str:
    """Store a prediction and optional reasoning trace. Returns prediction ID."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO predictions
            (id, ticker, agent_name, probability, confidence, market_price,
             edge, category, subcategory, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.id,
            prediction.ticker,
            prediction.agent_name,
            prediction.probability,
            prediction.confidence,
            prediction.market_price,
            prediction.edge,
            prediction.category,
            prediction.subcategory,
            prediction.timestamp.isoformat()
        ))

        if reasoning:
            conn.execute("""
                INSERT INTO reasoning_traces
                (id, prediction_id, reasoning_text, key_factors, unknowns,
                 base_rate_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reasoning.id,
                reasoning.prediction_id,
                reasoning.reasoning_text,
                json.dumps(reasoning.key_factors),
                json.dumps(reasoning.unknowns),
                reasoning.base_rate_used,
                reasoning.timestamp.isoformat()
            ))

    return prediction.id


def get_prediction(prediction_id: str,
                   db_path: Optional[Path] = None) -> Optional[Prediction]:
    """Retrieve a prediction by ID."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM predictions WHERE id = ?",
            (prediction_id,)
        ).fetchone()

        if not row:
            return None

        return Prediction(
            id=row["id"],
            ticker=row["ticker"],
            agent_name=row["agent_name"],
            probability=row["probability"],
            confidence=row["confidence"],
            market_price=row["market_price"],
            edge=row["edge"],
            category=row["category"],
            subcategory=row["subcategory"],
            timestamp=datetime.fromisoformat(row["timestamp"])
        )


def get_predictions_for_ticker(ticker: str,
                               db_path: Optional[Path] = None) -> list[Prediction]:
    """Get all predictions for a market ticker."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE ticker = ? ORDER BY timestamp DESC",
            (ticker,)
        ).fetchall()

        return [
            Prediction(
                id=row["id"],
                ticker=row["ticker"],
                agent_name=row["agent_name"],
                probability=row["probability"],
                confidence=row["confidence"],
                market_price=row["market_price"],
                edge=row["edge"],
                category=row["category"],
                subcategory=row["subcategory"],
                timestamp=datetime.fromisoformat(row["timestamp"])
            )
            for row in rows
        ]


def get_reasoning(prediction_id: str,
                  db_path: Optional[Path] = None) -> Optional[ReasoningTrace]:
    """Get reasoning trace for a prediction."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM reasoning_traces WHERE prediction_id = ?",
            (prediction_id,)
        ).fetchone()

        if not row:
            return None

        return ReasoningTrace(
            id=row["id"],
            prediction_id=row["prediction_id"],
            reasoning_text=row["reasoning_text"],
            key_factors=json.loads(row["key_factors"]) if row["key_factors"] else [],
            unknowns=json.loads(row["unknowns"]) if row["unknowns"] else [],
            base_rate_used=row["base_rate_used"],
            timestamp=datetime.fromisoformat(row["timestamp"])
        )


# =============================================================================
# Market Operations
# =============================================================================

def store_market(market: Market, db_path: Optional[Path] = None) -> str:
    """Store or update market metadata. Returns ticker."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO markets
            (ticker, title, category, subcategory, close_time, resolution_time,
             status, result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                title = excluded.title,
                category = excluded.category,
                subcategory = excluded.subcategory,
                close_time = excluded.close_time,
                resolution_time = excluded.resolution_time,
                status = excluded.status,
                result = excluded.result,
                updated_at = excluded.updated_at
        """, (
            market.ticker,
            market.title,
            market.category,
            market.subcategory,
            market.close_time.isoformat() if market.close_time else None,
            market.resolution_time.isoformat() if market.resolution_time else None,
            market.status,
            market.result,
            market.created_at.isoformat(),
            market.updated_at.isoformat()
        ))

    return market.ticker


def get_market(ticker: str, db_path: Optional[Path] = None) -> Optional[Market]:
    """Get market by ticker."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM markets WHERE ticker = ?",
            (ticker,)
        ).fetchone()

        if not row:
            return None

        return Market(
            ticker=row["ticker"],
            title=row["title"],
            category=row["category"],
            subcategory=row["subcategory"],
            close_time=datetime.fromisoformat(row["close_time"]) if row["close_time"] else None,
            resolution_time=datetime.fromisoformat(row["resolution_time"]) if row["resolution_time"] else None,
            status=row["status"],
            result=row["result"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )


def store_market_snapshot(snapshot: MarketSnapshot,
                          db_path: Optional[Path] = None) -> str:
    """Store a market price snapshot. Returns snapshot ID."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO market_snapshots
            (id, ticker, yes_price, no_price, volume, open_interest, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.id,
            snapshot.ticker,
            snapshot.yes_price,
            snapshot.no_price,
            snapshot.volume,
            snapshot.open_interest,
            snapshot.timestamp.isoformat()
        ))

    return snapshot.id


def snapshot_from_kalshi_market(market_data: dict) -> MarketSnapshot:
    """Create a MarketSnapshot from Kalshi API market data.

    Expected fields from kalshi_client.py market response:
    - ticker: str
    - yes_bid/yes_ask or last_price: price info
    - volume: int
    - open_interest: int
    """
    ticker = market_data.get("ticker", "")

    # Get raw prices from Kalshi API (in cents, 0-100)
    yes_price = market_data.get("yes_ask") or market_data.get("last_price", 0)
    no_price = market_data.get("no_ask")

    # Normalize YES price to 0-1 range first
    if yes_price > 1:
        yes_price = yes_price / 100

    # Normalize NO price, or derive from YES price if not provided
    if no_price is not None:
        if no_price > 1:
            no_price = no_price / 100
    else:
        no_price = 1 - yes_price if yes_price else 0

    return MarketSnapshot.create(
        ticker=ticker,
        yes_price=yes_price,
        no_price=no_price,
        volume=market_data.get("volume", 0),
        open_interest=market_data.get("open_interest", 0)
    )


# =============================================================================
# Outcome Operations
# =============================================================================

def store_outcome(ticker: str, actual_outcome: int, prediction_id: str,
                  db_path: Optional[Path] = None) -> tuple[str, float]:
    """Store market resolution and calculate Brier score.

    Args:
        ticker: Market ticker
        actual_outcome: 1 for YES, 0 for NO
        prediction_id: ID of the prediction to resolve

    Returns:
        Tuple of (outcome_id, brier_score)
    """
    prediction = get_prediction(prediction_id, db_path)
    if not prediction:
        raise ValueError(f"Prediction {prediction_id} not found")

    outcome = Outcome.create(
        ticker=ticker,
        prediction_id=prediction_id,
        actual_outcome=actual_outcome,
        predicted_probability=prediction.probability
    )

    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO outcomes
            (id, ticker, prediction_id, actual_outcome, predicted_probability,
             brier_score, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            outcome.id,
            outcome.ticker,
            outcome.prediction_id,
            outcome.actual_outcome,
            outcome.predicted_probability,
            outcome.brier_score,
            outcome.resolved_at.isoformat()
        ))

        # Update market status
        conn.execute("""
            UPDATE markets SET status = 'resolved', result = ?, updated_at = ?
            WHERE ticker = ?
        """, (
            "yes" if actual_outcome == 1 else "no",
            datetime.utcnow().isoformat(),
            ticker
        ))

    return outcome.id, outcome.brier_score


def get_outcomes(ticker: Optional[str] = None,
                 agent_name: Optional[str] = None,
                 limit: int = 100,
                 db_path: Optional[Path] = None) -> list[Outcome]:
    """Query outcomes with optional filters."""
    query = """
        SELECT o.*, p.agent_name
        FROM outcomes o
        JOIN predictions p ON o.prediction_id = p.id
        WHERE 1=1
    """
    params = []

    if ticker:
        query += " AND o.ticker = ?"
        params.append(ticker)

    if agent_name:
        query += " AND p.agent_name = ?"
        params.append(agent_name)

    query += " ORDER BY o.resolved_at DESC LIMIT ?"
    params.append(limit)

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            Outcome(
                id=row["id"],
                ticker=row["ticker"],
                prediction_id=row["prediction_id"],
                actual_outcome=row["actual_outcome"],
                predicted_probability=row["predicted_probability"],
                brier_score=row["brier_score"],
                resolved_at=datetime.fromisoformat(row["resolved_at"])
            )
            for row in rows
        ]


# =============================================================================
# Trade Operations (Future Use)
# =============================================================================

def store_trade(trade: Trade, db_path: Optional[Path] = None) -> str:
    """Store a trade record. Returns trade ID."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO trades
            (id, prediction_id, ticker, side, contracts, price, filled_at,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.id,
            trade.prediction_id,
            trade.ticker,
            trade.side,
            trade.contracts,
            trade.price,
            trade.filled_at.isoformat() if trade.filled_at else None,
            trade.status,
            trade.created_at.isoformat()
        ))

    return trade.id
