"""
Kalshi API Client - Flexible exploration and research module
"""
import os
import time
import base64
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Market:
    """Represents a Kalshi market (betting contract)"""
    ticker: str
    title: str
    event_ticker: str
    status: str
    # Prices (in cents, 0-100)
    yes_bid: Optional[int] = None
    yes_ask: Optional[int] = None
    no_bid: Optional[int] = None
    no_ask: Optional[int] = None
    last_price: Optional[int] = None
    # Volume & liquidity
    volume: int = 0
    volume_24h: int = 0
    open_interest: int = 0
    liquidity: int = 0
    # Metadata
    close_time: Optional[str] = None
    category: Optional[str] = None
    subtitle: Optional[str] = None
    raw: Dict = field(default_factory=dict)

    @property
    def yes_mid(self) -> Optional[float]:
        """Mid price for YES (0-1 scale)"""
        if self.yes_bid is not None and self.yes_ask is not None:
            return (self.yes_bid + self.yes_ask) / 200
        return self.last_price / 100 if self.last_price else None

    @property
    def spread(self) -> Optional[int]:
        """Bid-ask spread in cents"""
        if self.yes_bid is not None and self.yes_ask is not None:
            return self.yes_ask - self.yes_bid
        return None

    @classmethod
    def from_api(cls, data: Dict, category: str = None) -> 'Market':
        return cls(
            ticker=data.get('ticker', ''),
            title=data.get('title', ''),
            event_ticker=data.get('event_ticker', ''),
            status=data.get('status', ''),
            yes_bid=data.get('yes_bid'),
            yes_ask=data.get('yes_ask'),
            no_bid=data.get('no_bid'),
            no_ask=data.get('no_ask'),
            last_price=data.get('last_price'),
            volume=data.get('volume', 0),
            volume_24h=data.get('volume_24h', 0),
            open_interest=data.get('open_interest', 0),
            liquidity=data.get('liquidity', 0),
            close_time=data.get('close_time'),
            subtitle=data.get('subtitle', ''),
            category=category,
            raw=data
        )


@dataclass
class Event:
    """Represents a Kalshi event (container for markets)"""
    ticker: str
    title: str
    category: str
    series_ticker: str
    markets: List[Market] = field(default_factory=list)
    raw: Dict = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: Dict) -> 'Event':
        return cls(
            ticker=data.get('event_ticker', ''),
            title=data.get('title', ''),
            category=data.get('category', ''),
            series_ticker=data.get('series_ticker', ''),
            raw=data
        )


class KalshiClient:
    """Flexible Kalshi API client for exploration and research"""

    DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2"
    PROD_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, demo: bool = True):
        self.base_url = self.DEMO_URL if demo else self.PROD_URL
        self.key_id = os.getenv('KALSHI_DEMO_KEY_ID') if demo else os.getenv('KALSHI_PROD_KEY_ID')
        private_key_str = os.getenv('KALSHI_DEMO_PRIVATE_KEY') if demo else os.getenv('KALSHI_PROD_PRIVATE_KEY')

        if private_key_str:
            self.private_key = serialization.load_pem_private_key(
                private_key_str.encode(), password=None
            )
        else:
            self.private_key = None

        self._events_cache: Dict[str, Event] = {}
        self._markets_cache: Dict[str, Market] = {}

    def _sign(self, method: str, path: str, timestamp: str) -> str:
        """Sign request with RSA-PSS"""
        if not self.private_key:
            return ""
        msg = f"{timestamp}{method}/trade-api/v2{path}".encode('utf-8')
        sig = self.private_key.sign(
            msg,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(sig).decode('utf-8')

    def _request(self, method: str, path: str, params: Dict = None, auth: bool = False) -> Dict:
        """Make API request"""
        headers = {'Accept-Encoding': 'identity'}

        if auth and self.private_key:
            timestamp = str(int(time.time() * 1000))
            headers.update({
                'KALSHI-ACCESS-KEY': self.key_id,
                'KALSHI-ACCESS-SIGNATURE': self._sign(method, path, timestamp),
                'KALSHI-ACCESS-TIMESTAMP': timestamp,
            })

        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/json'

        url = f"{self.base_url}{path}"

        try:
            if method == 'GET':
                r = requests.get(url, headers=headers, params=params, timeout=30)
            else:
                r = requests.request(method, url, headers=headers, json=params, timeout=30)

            if r.status_code in (200, 201):
                return r.json()
            else:
                return {'error': r.status_code, 'message': r.text[:500]}
        except Exception as e:
            return {'error': 'exception', 'message': str(e)}

    # ==================== EVENTS ====================

    def get_events(self, limit: int = 100, cursor: str = None,
                   category: str = None, series: str = None,
                   status: str = None) -> List[Event]:
        """Fetch events with optional filtering"""
        params = {'limit': min(limit, 200)}
        if cursor:
            params['cursor'] = cursor
        if status:
            params['status'] = status

        result = self._request('GET', '/events', params)
        events = []

        for e_data in result.get('events', []):
            event = Event.from_api(e_data)

            # Apply filters
            if category and event.category.lower() != category.lower():
                continue
            if series and event.series_ticker != series:
                continue

            events.append(event)
            self._events_cache[event.ticker] = event

        return events

    def get_all_events(self, category: str = None) -> List[Event]:
        """Fetch all events with pagination"""
        all_events = []
        cursor = None

        for _ in range(50):  # Max 50 pages
            params = {'limit': 200}
            if cursor:
                params['cursor'] = cursor

            result = self._request('GET', '/events', params)
            events = result.get('events', [])

            for e_data in events:
                event = Event.from_api(e_data)
                if category and event.category.lower() != category.lower():
                    continue
                all_events.append(event)
                self._events_cache[event.ticker] = event

            cursor = result.get('cursor')
            if not cursor or not events:
                break

        return all_events

    def get_categories(self) -> Dict[str, int]:
        """Get all categories with event counts"""
        events = self.get_all_events()
        categories = {}
        for e in events:
            cat = e.category or 'Unknown'
            categories[cat] = categories.get(cat, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: -x[1]))

    # ==================== MARKETS ====================

    def get_markets(self, limit: int = 100, cursor: str = None,
                    status: str = 'open', event_ticker: str = None,
                    series_ticker: str = None, tickers: List[str] = None) -> List[Market]:
        """Fetch markets with filtering"""
        params = {'limit': min(limit, 1000)}
        if cursor:
            params['cursor'] = cursor
        if status:
            params['status'] = status
        if event_ticker:
            params['event_ticker'] = event_ticker
        if series_ticker:
            params['series_ticker'] = series_ticker
        if tickers:
            params['tickers'] = ','.join(tickers)

        result = self._request('GET', '/markets', params)
        markets = []

        for m_data in result.get('markets', []):
            market = Market.from_api(m_data)
            markets.append(market)
            self._markets_cache[market.ticker] = market

        return markets

    def get_all_markets(self, status: str = 'open') -> List[Market]:
        """Fetch all markets with pagination"""
        all_markets = []
        cursor = None

        for _ in range(100):  # Max 100 pages
            params = {'limit': 1000}
            if status:
                params['status'] = status
            if cursor:
                params['cursor'] = cursor

            result = self._request('GET', '/markets', params)
            markets = result.get('markets', [])

            for m_data in markets:
                market = Market.from_api(m_data)
                all_markets.append(market)
                self._markets_cache[market.ticker] = market

            cursor = result.get('cursor')
            if not cursor or not markets:
                break

        return all_markets

    def get_market(self, ticker: str) -> Optional[Market]:
        """Get single market by ticker"""
        result = self._request('GET', f'/markets/{ticker}')
        if 'market' in result:
            return Market.from_api(result['market'])
        return None

    def get_orderbook(self, ticker: str, depth: int = 10) -> Dict:
        """Get orderbook for a market"""
        result = self._request('GET', f'/markets/{ticker}/orderbook', {'depth': depth})
        return result.get('orderbook', {})

    # ==================== SEARCH ====================

    def search_events(self, query: str, limit: int = 50) -> List[Event]:
        """Search events by keyword in title"""
        query_lower = query.lower()
        events = self.get_all_events()
        matches = []

        for e in events:
            if query_lower in e.title.lower():
                matches.append(e)
                if len(matches) >= limit:
                    break

        return matches

    def search_markets(self, query: str, status: str = 'open', limit: int = 50) -> List[Market]:
        """Search markets by keyword in title"""
        query_lower = query.lower()
        markets = self.get_all_markets(status=status)
        matches = []

        for m in markets:
            if query_lower in m.title.lower():
                matches.append(m)
                if len(matches) >= limit:
                    break

        return matches

    # ==================== SERIES ====================

    def get_series(self, limit: int = 100, cursor: str = None) -> List[Dict]:
        """Fetch series (recurring event templates)"""
        params = {'limit': min(limit, 1000)}
        if cursor:
            params['cursor'] = cursor

        result = self._request('GET', '/series', params)
        return result.get('series', [])

    # ==================== PORTFOLIO (Auth Required) ====================

    def get_balance(self) -> Optional[Dict]:
        """Get account balance (requires auth)"""
        result = self._request('GET', '/portfolio/balance', auth=True)
        return result if 'error' not in result else None

    def get_positions(self) -> List[Dict]:
        """Get open positions (requires auth)"""
        result = self._request('GET', '/portfolio/positions', auth=True)
        return result.get('market_positions', [])

    def get_orders(self, status: str = None) -> List[Dict]:
        """Get orders (requires auth)"""
        params = {}
        if status:
            params['status'] = status
        result = self._request('GET', '/portfolio/orders', params, auth=True)
        return result.get('orders', [])

    def get_fills(self, limit: int = 100) -> List[Dict]:
        """Get trade fills/history (requires auth)"""
        result = self._request('GET', '/portfolio/fills', {'limit': limit}, auth=True)
        return result.get('fills', [])

    def place_order(self, ticker: str, side: str, count: int,
                    price: int = None, order_type: str = 'limit') -> Dict:
        """
        Place an order on a market.

        Args:
            ticker: Market ticker (e.g., 'KXHIGHDEN-26FEB15-T71')
            side: 'yes' or 'no'
            count: Number of contracts
            price: Price in cents (1-99) for limit orders
            order_type: 'limit' or 'market'

        Returns:
            Order response dict with order_id, status, etc.
        """
        import uuid

        order = {
            'ticker': ticker,
            'action': 'buy',
            'side': side,
            'type': order_type,
            'count': count,
            'client_order_id': str(uuid.uuid4()),
        }

        if order_type == 'limit' and price is not None:
            order['yes_price'] = price if side == 'yes' else (100 - price)

        result = self._request('POST', '/portfolio/orders', order, auth=True)
        return result

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order"""
        result = self._request('DELETE', f'/portfolio/orders/{order_id}', auth=True)
        return result


# ==================== EXPLORER CLASS ====================

class KalshiExplorer:
    """High-level exploration and research interface"""

    def __init__(self, demo: bool = True):
        self.client = KalshiClient(demo=demo)
        self._markets_cache: List[Market] = []
        self._events_cache: List[Event] = []

    def load_all_markets(self, status: str = 'open', force: bool = False) -> List[Market]:
        """Load all markets into cache"""
        if not self._markets_cache or force:
            self._markets_cache = self.client.get_all_markets(status=status)
        return self._markets_cache

    def load_all_events(self, force: bool = False) -> List[Event]:
        """Load all events into cache"""
        if not self._events_cache or force:
            self._events_cache = self.client.get_all_events()
        return self._events_cache

    def overview(self) -> Dict:
        """Get high-level overview of available markets"""
        categories = self.client.get_categories()
        markets = self.client.get_markets(limit=100, status='open')

        return {
            'categories': categories,
            'total_events': sum(categories.values()),
            'sample_open_markets': len(markets),
            'top_categories': list(categories.keys())[:5]
        }

    def explore_category(self, category: str, limit: int = 20) -> Dict:
        """Deep dive into a category"""
        events = self.client.get_all_events(category=category)

        sample_markets = []
        for e in events[:10]:
            markets = self.client.get_markets(event_ticker=e.ticker, limit=5)
            sample_markets.extend(markets)

        return {
            'category': category,
            'event_count': len(events),
            'events': events[:limit],
            'sample_markets': sample_markets[:limit]
        }

    # ==================== FILTERING ====================

    def filter_markets(self, markets: List[Market] = None,
                       min_price: float = None, max_price: float = None,
                       min_volume: int = None, min_liquidity: int = None,
                       max_spread: int = None, title_contains: str = None,
                       category: str = None, event_ticker: str = None) -> List[Market]:
        """Flexible market filtering"""
        if markets is None:
            markets = self._markets_cache or self.load_all_markets()

        results = []
        for m in markets:
            # Price filter (using mid price, 0-1 scale)
            if min_price is not None or max_price is not None:
                mid = m.yes_mid
                if mid is None:
                    continue
                if min_price is not None and mid < min_price:
                    continue
                if max_price is not None and mid > max_price:
                    continue

            # Volume filter
            if min_volume is not None and (m.volume or 0) < min_volume:
                continue

            # Liquidity filter
            if min_liquidity is not None and (m.liquidity or 0) < min_liquidity:
                continue

            # Spread filter
            if max_spread is not None:
                spread = m.spread
                if spread is None or spread > max_spread:
                    continue

            # Title search
            if title_contains and title_contains.lower() not in m.title.lower():
                continue

            # Category filter (requires event lookup)
            if category and m.category and m.category.lower() != category.lower():
                continue

            # Event filter
            if event_ticker and m.event_ticker != event_ticker:
                continue

            results.append(m)

        return results

    def filter_events(self, events: List[Event] = None,
                      category: str = None, title_contains: str = None,
                      series: str = None) -> List[Event]:
        """Flexible event filtering"""
        if events is None:
            events = self._events_cache or self.load_all_events()

        results = []
        for e in events:
            if category and e.category.lower() != category.lower():
                continue
            if title_contains and title_contains.lower() not in e.title.lower():
                continue
            if series and e.series_ticker != series:
                continue
            results.append(e)

        return results

    # ==================== RESEARCH ====================

    def find_liquid_markets(self, min_volume: int = 100, min_liquidity: int = 1000,
                            limit: int = 50) -> List[Market]:
        """Find most liquid markets"""
        markets = self.filter_markets(min_volume=min_volume, min_liquidity=min_liquidity)
        return sorted(markets, key=lambda x: x.liquidity or 0, reverse=True)[:limit]

    def find_tight_spreads(self, max_spread: int = 5, limit: int = 50) -> List[Market]:
        """Find markets with tight bid-ask spreads"""
        markets = self.filter_markets(max_spread=max_spread)
        return sorted(markets, key=lambda x: x.spread or 999)[:limit]

    def find_close_calls(self, price_range: tuple = (0.40, 0.60), limit: int = 50) -> List[Market]:
        """Find markets near 50/50 (close calls)"""
        markets = self.filter_markets(min_price=price_range[0], max_price=price_range[1])
        return sorted(markets, key=lambda x: abs((x.yes_mid or 0.5) - 0.5))[:limit]

    def find_longshots(self, max_price: float = 0.15, min_volume: int = 10,
                       limit: int = 50) -> List[Market]:
        """Find low-probability markets (longshots)"""
        markets = self.filter_markets(max_price=max_price, min_volume=min_volume)
        return sorted(markets, key=lambda x: x.volume or 0, reverse=True)[:limit]

    def find_favorites(self, min_price: float = 0.85, min_volume: int = 10,
                       limit: int = 50) -> List[Market]:
        """Find high-probability markets (favorites)"""
        markets = self.filter_markets(min_price=min_price, min_volume=min_volume)
        return sorted(markets, key=lambda x: x.volume or 0, reverse=True)[:limit]

    def search(self, query: str, search_type: str = 'all') -> Dict:
        """Unified search across events and markets"""
        results = {'query': query, 'events': [], 'markets': []}

        if search_type in ('all', 'events'):
            results['events'] = self.client.search_events(query, limit=20)

        if search_type in ('all', 'markets'):
            results['markets'] = self.client.search_markets(query, limit=20)

        return results

    # ==================== ANALYSIS ====================

    def market_summary(self, market: Market) -> Dict:
        """Detailed summary of a single market"""
        orderbook = self.client.get_orderbook(market.ticker)

        return {
            'ticker': market.ticker,
            'title': market.title,
            'event': market.event_ticker,
            'status': market.status,
            'prices': {
                'yes_bid': market.yes_bid,
                'yes_ask': market.yes_ask,
                'yes_mid': market.yes_mid,
                'spread': market.spread,
                'last': market.last_price,
            },
            'activity': {
                'volume': market.volume,
                'volume_24h': market.volume_24h,
                'open_interest': market.open_interest,
                'liquidity': market.liquidity,
            },
            'orderbook': orderbook,
            'close_time': market.close_time,
        }

    def category_stats(self) -> Dict[str, Dict]:
        """Statistics by category"""
        events = self.load_all_events()
        markets = self.load_all_markets()

        # Build event ticker -> category map
        event_categories = {e.ticker: e.category for e in events}

        stats = {}
        for m in markets:
            cat = event_categories.get(m.event_ticker, 'Unknown')
            if cat not in stats:
                stats[cat] = {'markets': 0, 'total_volume': 0, 'total_liquidity': 0}
            stats[cat]['markets'] += 1
            stats[cat]['total_volume'] += m.volume or 0
            stats[cat]['total_liquidity'] += m.liquidity or 0

        return dict(sorted(stats.items(), key=lambda x: -x[1]['markets']))


if __name__ == '__main__':
    explorer = KalshiExplorer(demo=True)

    print("=" * 60)
    print("KALSHI EXPLORER - Demo")
    print("=" * 60)

    # Overview
    print("\n=== OVERVIEW ===")
    overview = explorer.overview()
    print(f"Categories: {len(overview['categories'])}")
    for cat, count in list(overview['categories'].items())[:5]:
        print(f"  {cat}: {count} events")

    # Search
    print("\n=== SEARCH: 'election' ===")
    results = explorer.search('election')
    print(f"Found {len(results['events'])} events, {len(results['markets'])} markets")
    for e in results['events'][:3]:
        print(f"  [Event] {e.title[:55]}")
    for m in results['markets'][:3]:
        print(f"  [Market] {m.title[:55]}")

    # Filter demo
    print("\n=== FILTERING DEMO ===")
    markets = explorer.client.get_markets(limit=50, status='open')
    print(f"Loaded {len(markets)} markets")

    # Show some with prices
    priced = [m for m in markets if m.yes_mid is not None and m.yes_mid > 0]
    print(f"Markets with prices: {len(priced)}")
    for m in priced[:5]:
        print(f"  {m.title[:40]} | mid: {m.yes_mid:.2f} | vol: {m.volume}")
