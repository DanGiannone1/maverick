#!/usr/bin/env python3
"""Quick test of the database layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import (
    store_prediction, get_prediction, store_outcome,
    store_market, get_market, store_market_snapshot
)
from src.models import Prediction, ReasoningTrace, Market, MarketSnapshot
from src.analytics import (
    calibration_report, recent_predictions, unresolved_markets,
    format_calibration_report
)


def test_workflow():
    print("Testing maverick database workflow...\n")

    # 1. Store a market
    print("1. Storing market metadata...")
    market = Market(
        ticker="TEST-2024-DEMO",
        title="Will this demo work?",
        category="test",
        subcategory="verification"
    )
    store_market(market)
    retrieved_market = get_market("TEST-2024-DEMO")
    assert retrieved_market is not None
    print(f"   Market stored: {retrieved_market.ticker}")

    # 2. Store a prediction with reasoning
    print("\n2. Storing prediction with reasoning...")
    prediction = Prediction.create(
        ticker="TEST-2024-DEMO",
        agent_name="test_agent",
        probability=0.75,
        confidence=0.85,
        market_price=0.60,
        category="test"
    )
    reasoning = ReasoningTrace.create(
        prediction_id=prediction.id,
        reasoning_text="This is a test prediction to verify the database works.",
        key_factors=["factor1", "factor2"],
        unknowns=["unknown1"],
        base_rate_used=0.5
    )
    pred_id = store_prediction(prediction, reasoning)
    print(f"   Prediction stored: {pred_id}")
    print(f"   Edge: {prediction.edge:+.1%}")

    # 3. Verify prediction retrieval
    print("\n3. Retrieving prediction...")
    retrieved = get_prediction(pred_id)
    assert retrieved is not None
    assert retrieved.probability == 0.75
    assert abs(retrieved.edge - 0.15) < 0.0001
    print(f"   Retrieved: {retrieved.ticker} @ {retrieved.probability:.1%}")

    # 4. Store a market snapshot
    print("\n4. Storing market snapshot...")
    snapshot = MarketSnapshot.create(
        ticker="TEST-2024-DEMO",
        yes_price=0.62,
        no_price=0.38,
        volume=1000,
        open_interest=500
    )
    snap_id = store_market_snapshot(snapshot)
    print(f"   Snapshot stored: {snap_id}")

    # 5. Check unresolved markets
    print("\n5. Checking unresolved markets...")
    unresolved = unresolved_markets()
    print(f"   Found {len(unresolved)} unresolved market(s)")
    for m in unresolved:
        print(f"   - {m['ticker']}: {m['prediction_count']} prediction(s)")

    # 6. Resolve the market (YES outcome)
    print("\n6. Resolving market as YES...")
    outcome_id, brier = store_outcome("TEST-2024-DEMO", 1, pred_id)
    print(f"   Outcome stored: {outcome_id}")
    print(f"   Brier score: {brier:.4f}")

    # Verify Brier calculation: (0.75 - 1)^2 = 0.0625
    expected_brier = (0.75 - 1) ** 2
    assert abs(brier - expected_brier) < 0.0001, f"Expected {expected_brier}, got {brier}"
    print(f"   Brier calculation verified: (0.75 - 1)² = {expected_brier:.4f}")

    # 7. Check recent predictions
    print("\n7. Checking recent predictions...")
    recent = recent_predictions(limit=5)
    print(f"   Found {len(recent)} recent prediction(s)")
    for p in recent:
        status = "RESOLVED" if p["resolved"] else "PENDING"
        print(f"   - {p['ticker']}: {p['probability']:.1%} [{status}]")

    # 8. Generate calibration report
    print("\n8. Generating calibration report...")
    buckets = calibration_report(days=30)
    if buckets:
        print(format_calibration_report(buckets))
    else:
        print("   No resolved predictions for calibration yet.")

    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    test_workflow()
