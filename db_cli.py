#!/usr/bin/env python3
"""CLI tool for database operations - allows agents to store predictions via Bash."""

import argparse
import json
import sys
from datetime import datetime

from src.db import (
    init_db, store_prediction, get_prediction, get_predictions_for_ticker,
    store_outcome, get_outcomes, store_market, get_market
)
from src.models import Prediction, ReasoningTrace, Market
from src.analytics import (
    calibration_report, agent_performance, recent_predictions,
    unresolved_markets, category_performance, format_calibration_report,
    format_agent_stats
)


def cmd_store_prediction(args):
    """Store a new prediction."""
    prediction = Prediction.create(
        ticker=args.ticker,
        agent_name=args.agent,
        probability=args.probability,
        confidence=args.confidence,
        market_price=args.market_price,
        category=args.category,
        subcategory=args.subcategory
    )

    reasoning = None
    if args.reasoning:
        key_factors = args.factors.split(',') if args.factors else []
        unknowns = args.unknowns.split(',') if args.unknowns else []
        reasoning = ReasoningTrace.create(
            prediction_id=prediction.id,
            reasoning_text=args.reasoning,
            key_factors=key_factors,
            unknowns=unknowns,
            base_rate_used=args.base_rate
        )

    pred_id = store_prediction(prediction, reasoning)

    result = {
        'prediction_id': pred_id,
        'ticker': args.ticker,
        'agent': args.agent,
        'probability': args.probability,
        'market_price': args.market_price,
        'edge': prediction.edge,
        'direction': 'BUY_YES' if prediction.edge > 0 else 'BUY_NO'
    }
    print(json.dumps(result, indent=2))


def cmd_resolve(args):
    """Resolve a prediction with actual outcome."""
    outcome_id, brier = store_outcome(
        ticker=args.ticker,
        actual_outcome=1 if args.outcome.lower() == 'yes' else 0,
        prediction_id=args.prediction_id
    )

    result = {
        'outcome_id': outcome_id,
        'prediction_id': args.prediction_id,
        'actual_outcome': args.outcome.upper(),
        'brier_score': round(brier, 4)
    }
    print(json.dumps(result, indent=2))


def cmd_calibration(args):
    """Show calibration report."""
    buckets = calibration_report(
        agent_name=args.agent,
        category=args.category,
        days=args.days
    )
    print(format_calibration_report(buckets))


def cmd_agent_stats(args):
    """Show agent performance stats."""
    stats = agent_performance(args.agent, days=args.days)
    print(format_agent_stats(stats))


def cmd_recent(args):
    """Show recent predictions."""
    preds = recent_predictions(limit=args.limit, agent_name=args.agent)

    if not preds:
        print("No predictions found.")
        return

    print(f"{'Ticker':<20} {'Agent':<12} {'Prob':>6} {'Market':>7} {'Edge':>6} {'Resolved':<8}")
    print("-" * 70)

    for p in preds:
        resolved = "YES" if p['actual_outcome'] == 1 else "NO" if p['actual_outcome'] == 0 else "-"
        print(f"{p['ticker']:<20} {p['agent_name']:<12} {p['probability']:>5.0%} {p['market_price']:>6.0%} {p['edge']:>+5.0%} {resolved:<8}")


def cmd_unresolved(args):
    """Show unresolved markets with predictions."""
    markets = unresolved_markets()

    if not markets:
        print("No unresolved predictions.")
        return

    print(f"{'Ticker':<25} {'Predictions':>6} {'Avg Prob':>9}")
    print("-" * 45)

    for m in markets:
        print(f"{m['ticker']:<25} {m['prediction_count']:>6} {m['avg_probability']:>8.0%}")


def cmd_category_stats(args):
    """Show performance by category."""
    stats = category_performance(days=args.days)

    if not stats:
        print("No predictions found.")
        return

    print(f"{'Category':<20} {'Predictions':>12} {'Resolved':>10} {'Avg Brier':>10}")
    print("-" * 55)

    for s in stats:
        brier = f"{s['avg_brier_score']:.4f}" if s['avg_brier_score'] else "-"
        print(f"{s['category']:<20} {s['prediction_count']:>12} {s['resolved_count']:>10} {brier:>10}")


def cmd_get(args):
    """Get a specific prediction."""
    pred = get_prediction(args.prediction_id)
    if not pred:
        print(f"Prediction {args.prediction_id} not found.")
        sys.exit(1)

    result = {
        'id': pred.id,
        'ticker': pred.ticker,
        'agent': pred.agent_name,
        'probability': pred.probability,
        'confidence': pred.confidence,
        'market_price': pred.market_price,
        'edge': pred.edge,
        'category': pred.category,
        'timestamp': pred.timestamp.isoformat()
    }
    print(json.dumps(result, indent=2))


def cmd_init(args):
    """Initialize the database."""
    path = init_db()
    print(f"Database initialized at: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Maverick database CLI - store and query predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store a prediction
  %(prog)s store --ticker KXFED-26FEB15 --agent reasoner --probability 0.30 \\
      --confidence 0.7 --market-price 0.45 --category economics

  # Store with reasoning
  %(prog)s store --ticker KXFED-26FEB15 --agent reasoner --probability 0.30 \\
      --confidence 0.7 --market-price 0.45 --reasoning "Fed unlikely to cut..."

  # Resolve a prediction
  %(prog)s resolve --ticker KXFED-26FEB15 --prediction-id pred_abc123 --outcome NO

  # Check calibration
  %(prog)s calibration --agent reasoner --days 90

  # Agent performance
  %(prog)s agent-stats --agent reasoner

  # Recent predictions
  %(prog)s recent --limit 20

  # Unresolved markets
  %(prog)s unresolved
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # store command
    store_p = subparsers.add_parser('store', help='Store a new prediction')
    store_p.add_argument('--ticker', required=True, help='Market ticker')
    store_p.add_argument('--agent', required=True, help='Agent name')
    store_p.add_argument('--probability', type=float, required=True, help='Predicted probability (0-1)')
    store_p.add_argument('--confidence', type=float, required=True, help='Confidence level (0-1)')
    store_p.add_argument('--market-price', type=float, required=True, help='Current market price (0-1)')
    store_p.add_argument('--category', help='Market category')
    store_p.add_argument('--subcategory', help='Market subcategory')
    store_p.add_argument('--reasoning', help='Full reasoning text')
    store_p.add_argument('--factors', help='Key factors (comma-separated)')
    store_p.add_argument('--unknowns', help='Key unknowns (comma-separated)')
    store_p.add_argument('--base-rate', type=float, help='Base rate used')
    store_p.set_defaults(func=cmd_store_prediction)

    # resolve command
    resolve_p = subparsers.add_parser('resolve', help='Resolve a prediction')
    resolve_p.add_argument('--ticker', required=True, help='Market ticker')
    resolve_p.add_argument('--prediction-id', required=True, help='Prediction ID to resolve')
    resolve_p.add_argument('--outcome', required=True, choices=['yes', 'no', 'YES', 'NO'], help='Actual outcome')
    resolve_p.set_defaults(func=cmd_resolve)

    # calibration command
    cal_p = subparsers.add_parser('calibration', help='Show calibration report')
    cal_p.add_argument('--agent', help='Filter by agent name')
    cal_p.add_argument('--category', help='Filter by category')
    cal_p.add_argument('--days', type=int, default=90, help='Lookback period in days')
    cal_p.set_defaults(func=cmd_calibration)

    # agent-stats command
    stats_p = subparsers.add_parser('agent-stats', help='Show agent performance')
    stats_p.add_argument('--agent', required=True, help='Agent name')
    stats_p.add_argument('--days', type=int, default=90, help='Lookback period in days')
    stats_p.set_defaults(func=cmd_agent_stats)

    # recent command
    recent_p = subparsers.add_parser('recent', help='Show recent predictions')
    recent_p.add_argument('--limit', type=int, default=20, help='Number of predictions')
    recent_p.add_argument('--agent', help='Filter by agent name')
    recent_p.set_defaults(func=cmd_recent)

    # unresolved command
    unres_p = subparsers.add_parser('unresolved', help='Show unresolved predictions')
    unres_p.set_defaults(func=cmd_unresolved)

    # category-stats command
    cat_p = subparsers.add_parser('category-stats', help='Show performance by category')
    cat_p.add_argument('--days', type=int, default=90, help='Lookback period in days')
    cat_p.set_defaults(func=cmd_category_stats)

    # get command
    get_p = subparsers.add_parser('get', help='Get a specific prediction')
    get_p.add_argument('--prediction-id', required=True, help='Prediction ID')
    get_p.set_defaults(func=cmd_get)

    # init command
    init_p = subparsers.add_parser('init', help='Initialize database')
    init_p.set_defaults(func=cmd_init)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
