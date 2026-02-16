#!/usr/bin/env python3
"""
Finder - Scan Kalshi for reasoning-amenable opportunities.

Excludes sports/crypto. Returns markets sorted by volume.

Usage:
    python finder.py                    # Default scan
    python finder.py --days 30          # Max days to resolution
    python finder.py --min-vol 100      # Min volume
    python finder.py --max-vol 50000    # Max volume (for "medium" opportunities)
    python finder.py --limit 20         # Max results
    python finder.py --json             # JSON output
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from kalshi_client import KalshiClient


# Exclude sports, crypto, parlays
EXCLUDE_PREFIXES = [
    'KXMV',       # Multi-game parlays
    'KXNBA', 'KXNFL', 'KXMLB', 'KXNHL',  # Major sports
    'KXSOCCER', 'KXTENNIS', 'KXGOLF', 'KXUFC', 'KXMMA',  # Other sports
    'KXESPORTS', 'KXNCAA', 'KXCBB', 'KXCFB',  # Esports, college
    'KXBTC', 'KXETH', 'KXSOL', 'KXXRP',  # Crypto prices
]


# Known good series by category
GOOD_SERIES = {
    'Economics': ['KXFED', 'KXCPI', 'KXGDP', 'KXJOBS', 'KXUNEMPLOYMENT', 'KXPCE',
                  'KXINFLATION', 'KXRECESSION', 'KXGASRETAIL', 'KXRETAIL'],
    'Politics': ['KXCABLEAVE', 'KXTRUTHSOCIAL', 'KXSHUTDOWN', 'KXTARIFF',
                 'KXWARSH', 'KXEXECORDER', 'KXIMPEACH', 'KXINSURRECTION',
                 'KXVETOOVERRIDE', 'KXUSAEXPANDTERRITORY'],
    'Tech': ['KXIPO', 'KXEARNINGS', 'KXSPACEX', 'KXSTARSHIP'],
    'Financials': ['KXSP500', 'KXDOW', 'KXNASDAQ', 'KXVIX'],
    'Climate': ['KXHURRICANE', 'KXTEMP', 'KXWEATHER'],
}


def find_opportunities(
    max_days: int = 30,
    min_volume: int = 100,
    max_volume: int = None,
    limit: int = 50
) -> list:
    """
    Find reasoning-amenable markets by querying known good series.

    Returns list sorted by volume (descending).
    """
    client = KalshiClient(demo=False)
    now = datetime.now(timezone.utc)

    candidates = []

    # Query each known good series
    for category, series_list in GOOD_SERIES.items():
        for series in series_list:
            try:
                result = client._request('GET', '/markets', {
                    'series_ticker': series,
                    'status': 'open',
                    'limit': 50
                })

                for m in result.get('markets', []):
                    # Check volume
                    vol = m.get('volume') or 0
                    if vol < min_volume:
                        continue
                    if max_volume and vol > max_volume:
                        continue

                    # Must have price
                    if not m.get('yes_bid') and not m.get('yes_ask'):
                        continue

                    # Check time horizon
                    close_time = m.get('close_time')
                    days_to_close = None
                    if close_time:
                        try:
                            ct = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                            days_to_close = (ct - now).days
                            if days_to_close < 0 or days_to_close > max_days:
                                continue
                        except:
                            continue

                    price = m.get('yes_ask') or m.get('yes_bid') or m.get('last_price') or 0

                    candidates.append({
                        'ticker': m.get('ticker', ''),
                        'title': (m.get('title') or '')[:70],
                        'price': price,
                        'volume': vol,
                        'days': days_to_close,
                        'category': category,
                        'series': series,
                    })
            except Exception:
                continue  # Skip series that error

    # Sort by volume descending
    candidates.sort(key=lambda x: x['volume'], reverse=True)
    return candidates[:limit]


def print_table(candidates: list):
    """Print as formatted table."""
    if not candidates:
        print("No candidates found.")
        return

    print(f"\n{'='*95}")
    print(f"FINDER - {len(candidates)} opportunities")
    print(f"{'='*95}\n")

    print(f"{'#':<3} {'TICKER':<30} {'CAT':<10} {'PRICE':>6} {'VOL':>10} {'DAYS':>5}")
    print(f"{'-'*3} {'-'*30} {'-'*10} {'-'*6} {'-'*10} {'-'*5}")

    for i, c in enumerate(candidates, 1):
        ticker = c['ticker'][:30]
        cat = c.get('category', '')[:10]
        price = f"{c['price']}c" if c['price'] else "---"
        vol = f"{c['volume']:,}"
        days = str(c['days']) if c['days'] is not None else "---"

        print(f"{i:<3} {ticker:<30} {cat:<10} {price:>6} {vol:>10} {days:>5}")

    print(f"\n{'='*95}\n")


def main():
    parser = argparse.ArgumentParser(description='Find reasoning-amenable Kalshi markets')
    parser.add_argument('--days', type=int, default=30, help='Max days to resolution (default: 30)')
    parser.add_argument('--min-vol', type=int, default=100, help='Min volume (default: 100)')
    parser.add_argument('--max-vol', type=int, default=None, help='Max volume (for medium opportunities)')
    parser.add_argument('--limit', type=int, default=30, help='Max results (default: 30)')
    parser.add_argument('--json', action='store_true', help='JSON output')

    args = parser.parse_args()

    try:
        candidates = find_opportunities(
            max_days=args.days,
            min_volume=args.min_vol,
            max_volume=args.max_vol,
            limit=args.limit
        )

        if args.json:
            print(json.dumps(candidates, indent=2))
        else:
            print_table(candidates)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
