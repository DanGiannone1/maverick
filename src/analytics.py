"""Analytics and reporting for maverick prediction system."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .db import get_connection, get_db_path


@dataclass
class CalibrationBucket:
    """Calibration data for a probability range."""
    range_low: float
    range_high: float
    prediction_count: int
    actual_rate: float  # % that resolved YES
    avg_predicted: float  # Average predicted probability
    calibration_error: float  # abs(actual_rate - avg_predicted)


@dataclass
class AgentStats:
    """Performance statistics for an agent."""
    agent_name: str
    total_predictions: int
    resolved_predictions: int
    avg_brier_score: float
    avg_edge: float
    win_rate: float  # % of positive edge predictions that resolved correctly


def calibration_report(agent_name: Optional[str] = None,
                       category: Optional[str] = None,
                       days: int = 30,
                       db_path: Optional[Path] = None) -> list[CalibrationBucket]:
    """Generate calibration report by probability buckets.

    Groups predictions into 10% buckets and compares predicted vs actual rates.
    Perfect calibration: 70% predictions should resolve YES 70% of the time.
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    query = """
        SELECT
            p.probability,
            o.actual_outcome
        FROM predictions p
        JOIN outcomes o ON p.id = o.prediction_id
        WHERE p.timestamp >= ?
    """
    params = [cutoff]

    if agent_name:
        query += " AND p.agent_name = ?"
        params.append(agent_name)

    if category:
        query += " AND p.category = ?"
        params.append(category)

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    # Group into 10% buckets
    buckets: dict[int, list[tuple[float, int]]] = {i: [] for i in range(10)}

    for row in rows:
        prob = row["probability"]
        outcome = row["actual_outcome"]
        bucket_idx = min(int(prob * 10), 9)  # 0-9
        buckets[bucket_idx].append((prob, outcome))

    results = []
    for idx, predictions in buckets.items():
        if not predictions:
            continue

        probs, outcomes = zip(*predictions)
        avg_predicted = sum(probs) / len(probs)
        actual_rate = sum(outcomes) / len(outcomes)

        results.append(CalibrationBucket(
            range_low=idx / 10,
            range_high=(idx + 1) / 10,
            prediction_count=len(predictions),
            actual_rate=actual_rate,
            avg_predicted=avg_predicted,
            calibration_error=abs(actual_rate - avg_predicted)
        ))

    return results


def agent_performance(agent_name: str,
                      days: int = 30,
                      db_path: Optional[Path] = None) -> AgentStats:
    """Get performance statistics for a specific agent."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    with get_connection(db_path) as conn:
        # Total predictions
        total = conn.execute("""
            SELECT COUNT(*) as count FROM predictions
            WHERE agent_name = ? AND timestamp >= ?
        """, (agent_name, cutoff)).fetchone()["count"]

        # Resolved with outcomes
        resolved = conn.execute("""
            SELECT
                COUNT(*) as count,
                AVG(o.brier_score) as avg_brier,
                AVG(p.edge) as avg_edge
            FROM predictions p
            JOIN outcomes o ON p.id = o.prediction_id
            WHERE p.agent_name = ? AND p.timestamp >= ?
        """, (agent_name, cutoff)).fetchone()

        # Win rate on positive edge predictions
        wins = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE
                    WHEN (p.probability > 0.5 AND o.actual_outcome = 1)
                      OR (p.probability < 0.5 AND o.actual_outcome = 0)
                    THEN 1 ELSE 0
                END) as wins
            FROM predictions p
            JOIN outcomes o ON p.id = o.prediction_id
            WHERE p.agent_name = ? AND p.timestamp >= ? AND p.edge > 0
        """, (agent_name, cutoff)).fetchone()

        win_rate = 0.0
        if wins["total"] > 0:
            win_rate = wins["wins"] / wins["total"]

        return AgentStats(
            agent_name=agent_name,
            total_predictions=total,
            resolved_predictions=resolved["count"] or 0,
            avg_brier_score=resolved["avg_brier"] or 0.0,
            avg_edge=resolved["avg_edge"] or 0.0,
            win_rate=win_rate
        )


def recent_predictions(limit: int = 20,
                       agent_name: Optional[str] = None,
                       db_path: Optional[Path] = None) -> list[dict]:
    """Get recent predictions with their current status."""
    query = """
        SELECT
            p.id,
            p.ticker,
            p.agent_name,
            p.probability,
            p.market_price,
            p.edge,
            p.timestamp,
            o.actual_outcome,
            o.brier_score
        FROM predictions p
        LEFT JOIN outcomes o ON p.id = o.prediction_id
    """
    params = []

    if agent_name:
        query += " WHERE p.agent_name = ?"
        params.append(agent_name)

    query += " ORDER BY p.timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "agent_name": row["agent_name"],
                "probability": row["probability"],
                "market_price": row["market_price"],
                "edge": row["edge"],
                "timestamp": row["timestamp"],
                "resolved": row["actual_outcome"] is not None,
                "actual_outcome": row["actual_outcome"],
                "brier_score": row["brier_score"]
            }
            for row in rows
        ]


def unresolved_markets(db_path: Optional[Path] = None) -> list[dict]:
    """Get markets with predictions that haven't been resolved yet."""
    with get_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT DISTINCT
                p.ticker,
                m.title,
                m.category,
                m.close_time,
                COUNT(p.id) as prediction_count,
                AVG(p.probability) as avg_probability,
                MAX(p.timestamp) as latest_prediction
            FROM predictions p
            LEFT JOIN markets m ON p.ticker = m.ticker
            LEFT JOIN outcomes o ON p.id = o.prediction_id
            WHERE o.id IS NULL
            GROUP BY p.ticker
            ORDER BY latest_prediction DESC
        """).fetchall()

        return [
            {
                "ticker": row["ticker"],
                "title": row["title"],
                "category": row["category"],
                "close_time": row["close_time"],
                "prediction_count": row["prediction_count"],
                "avg_probability": row["avg_probability"],
                "latest_prediction": row["latest_prediction"]
            }
            for row in rows
        ]


def category_performance(days: int = 30,
                         db_path: Optional[Path] = None) -> list[dict]:
    """Get performance breakdown by category."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    with get_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT
                p.category,
                COUNT(*) as prediction_count,
                COUNT(o.id) as resolved_count,
                AVG(o.brier_score) as avg_brier,
                AVG(p.edge) as avg_edge
            FROM predictions p
            LEFT JOIN outcomes o ON p.id = o.prediction_id
            WHERE p.timestamp >= ?
            GROUP BY p.category
            ORDER BY prediction_count DESC
        """, (cutoff,)).fetchall()

        return [
            {
                "category": row["category"] or "uncategorized",
                "prediction_count": row["prediction_count"],
                "resolved_count": row["resolved_count"],
                "avg_brier_score": row["avg_brier"],
                "avg_edge": row["avg_edge"]
            }
            for row in rows
        ]


def format_calibration_report(buckets: list[CalibrationBucket]) -> str:
    """Format calibration report as a readable table."""
    lines = [
        "Calibration Report",
        "=" * 60,
        f"{'Range':<12} {'Count':>8} {'Predicted':>10} {'Actual':>10} {'Error':>10}",
        "-" * 60
    ]

    total_error = 0.0
    total_count = 0

    for bucket in buckets:
        lines.append(
            f"{bucket.range_low:.0%}-{bucket.range_high:.0%}  "
            f"{bucket.prediction_count:>8} "
            f"{bucket.avg_predicted:>10.1%} "
            f"{bucket.actual_rate:>10.1%} "
            f"{bucket.calibration_error:>10.1%}"
        )
        total_error += bucket.calibration_error * bucket.prediction_count
        total_count += bucket.prediction_count

    if total_count > 0:
        lines.append("-" * 60)
        lines.append(f"Weighted avg calibration error: {total_error / total_count:.1%}")

    return "\n".join(lines)


def format_agent_stats(stats: AgentStats) -> str:
    """Format agent statistics as a readable summary."""
    return f"""
Agent: {stats.agent_name}
{'=' * 40}
Total Predictions:    {stats.total_predictions}
Resolved:             {stats.resolved_predictions}
Average Brier Score:  {stats.avg_brier_score:.4f}
Average Edge:         {stats.avg_edge:+.1%}
Win Rate (edge > 0):  {stats.win_rate:.1%}

Brier Score Guide:
  0.00 = Perfect prediction
  0.25 = Random guessing
  1.00 = Always wrong
""".strip()
