"""Data models for the maverick prediction system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID (e.g., pred_abc123)."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class Prediction:
    """A probability estimate for a market outcome."""
    id: str
    ticker: str
    agent_name: str
    probability: float  # 0.0 to 1.0
    confidence: float   # 0.0 to 1.0 (meta-confidence in the estimate)
    market_price: float # Current market YES price at time of prediction
    edge: float         # probability - market_price
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: Optional[str] = None
    subcategory: Optional[str] = None

    @property
    def has_positive_edge(self) -> bool:
        return self.edge > 0

    @classmethod
    def create(cls, ticker: str, agent_name: str, probability: float,
               confidence: float, market_price: float, **kwargs) -> "Prediction":
        """Factory method to create a new prediction with generated ID."""
        return cls(
            id=generate_id("pred"),
            ticker=ticker,
            agent_name=agent_name,
            probability=probability,
            confidence=confidence,
            market_price=market_price,
            edge=probability - market_price,
            **kwargs
        )


@dataclass
class ReasoningTrace:
    """Full reasoning behind a prediction."""
    id: str
    prediction_id: str
    reasoning_text: str  # Full AI reasoning
    key_factors: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    base_rate_used: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, prediction_id: str, reasoning_text: str, **kwargs) -> "ReasoningTrace":
        """Factory method to create a new reasoning trace with generated ID."""
        return cls(
            id=generate_id("trace"),
            prediction_id=prediction_id,
            reasoning_text=reasoning_text,
            **kwargs
        )


@dataclass
class Market:
    """Market metadata from Kalshi."""
    ticker: str
    title: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    close_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None
    status: str = "open"  # open, closed, resolved
    result: Optional[str] = None  # yes, no, null (when resolved)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketSnapshot:
    """Point-in-time market pricing data."""
    id: str
    ticker: str
    yes_price: float
    no_price: float
    volume: int
    open_interest: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, ticker: str, yes_price: float, no_price: float,
               volume: int = 0, open_interest: int = 0) -> "MarketSnapshot":
        """Factory method to create a new snapshot with generated ID."""
        return cls(
            id=generate_id("snap"),
            ticker=ticker,
            yes_price=yes_price,
            no_price=no_price,
            volume=volume,
            open_interest=open_interest
        )


@dataclass
class Outcome:
    """Resolution of a market with Brier score."""
    id: str
    ticker: str
    prediction_id: str
    actual_outcome: int  # 1 for YES, 0 for NO
    predicted_probability: float
    brier_score: float  # (prediction - outcome)^2
    resolved_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, ticker: str, prediction_id: str,
               actual_outcome: int, predicted_probability: float) -> "Outcome":
        """Factory method to create a new outcome with calculated Brier score."""
        brier_score = (predicted_probability - actual_outcome) ** 2
        return cls(
            id=generate_id("out"),
            ticker=ticker,
            prediction_id=prediction_id,
            actual_outcome=actual_outcome,
            predicted_probability=predicted_probability,
            brier_score=brier_score
        )


@dataclass
class Trade:
    """Trade execution record (future use)."""
    id: str
    prediction_id: str
    ticker: str
    side: str  # yes, no
    contracts: int
    price: float
    filled_at: Optional[datetime] = None
    status: str = "pending"  # pending, filled, cancelled
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, prediction_id: str, ticker: str, side: str,
               contracts: int, price: float) -> "Trade":
        """Factory method to create a new trade with generated ID."""
        return cls(
            id=generate_id("trade"),
            prediction_id=prediction_id,
            ticker=ticker,
            side=side,
            contracts=contracts,
            price=price
        )
