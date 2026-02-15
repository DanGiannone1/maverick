"""
Kelly Criterion - Deterministic position sizing math

Usage:
    python kelly.py --our-prob 0.05 --market-prob 0.13 --confidence high
    python kelly.py --our-prob 0.60 --market-prob 0.45 --bankroll 10000
"""

import argparse
from dataclasses import dataclass
from typing import Tuple


@dataclass
class KellyResult:
    """Result of Kelly calculation"""
    direction: str          # BUY_YES, BUY_NO, NO_TRADE
    edge: float             # Absolute edge (always positive if trade)
    full_kelly: float       # Full Kelly fraction
    recommended: float      # After confidence adjustment

    # For display
    our_prob: float
    market_prob: float
    confidence: str

    def __str__(self) -> str:
        if self.direction == "NO_TRADE":
            return "NO_TRADE: No edge detected"

        return f"""
Kelly Calculation
=====================================
Direction:    {self.direction}
Edge:         {self.edge:.1%} ({self.edge*100:.1f} points)

Our estimate: {self.our_prob:.1%}
Market price: {self.market_prob:.1%}
Confidence:   {self.confidence}

Full Kelly:   {self.full_kelly:.2%} of bankroll
Recommended:  {self.recommended:.2%} of bankroll (fractional)
=====================================
"""

    def with_bankroll(self, bankroll: float) -> str:
        """Show dollar amounts given bankroll"""
        full_amt = bankroll * self.full_kelly
        rec_amt = bankroll * self.recommended
        return f"""
Position Sizing (${bankroll:,.0f} bankroll)
=====================================
Full Kelly:   ${full_amt:,.2f}
Recommended:  ${rec_amt:,.2f}
=====================================
"""


# Confidence multipliers - how much of Kelly to actually bet
CONFIDENCE_MULTIPLIERS = {
    "low": 0.25,      # Very uncertain, bet small
    "medium": 0.40,   # Moderate confidence
    "high": 0.50,     # Strong confidence (still half Kelly)
}

# Time decay multipliers - discount for opportunity cost
TIME_MULTIPLIERS = {
    "days": 1.0,       # < 1 week
    "weeks": 0.7,      # 1-4 weeks
    "months": 0.5,     # 1-3 months
    "quarters": 0.3,   # 3-6 months
    "years": 0.2,      # 6+ months
}


def calculate_kelly(
    our_prob: float,
    market_prob: float,
    confidence: str = "medium",
    time_horizon: str = None,
) -> KellyResult:
    """
    Calculate Kelly criterion position size.

    Args:
        our_prob: Our estimated probability of YES (0-1)
        market_prob: Current market price for YES (0-1)
        confidence: "low", "medium", or "high"
        time_horizon: Optional time discount ("days", "weeks", "months", "quarters", "years")

    Returns:
        KellyResult with direction, edge, and sizing
    """
    # Validate inputs
    our_prob = max(0.001, min(0.999, our_prob))
    market_prob = max(0.001, min(0.999, market_prob))

    # Determine direction based on edge
    if abs(our_prob - market_prob) < 0.01:
        # Less than 1% edge - no trade
        return KellyResult(
            direction="NO_TRADE",
            edge=0,
            full_kelly=0,
            recommended=0,
            our_prob=our_prob,
            market_prob=market_prob,
            confidence=confidence,
        )

    if our_prob > market_prob:
        # We think YES is underpriced - buy YES
        direction = "BUY_YES"
        p = our_prob                                    # Prob of winning
        b = (1 - market_prob) / market_prob             # Odds (win/risk ratio)
    else:
        # We think YES is overpriced - buy NO
        direction = "BUY_NO"
        p = 1 - our_prob                                # Prob of NO winning
        b = market_prob / (1 - market_prob)             # Odds for NO

    # Kelly formula: f* = (p*b - q) / b where q = 1-p
    q = 1 - p
    kelly = (p * b - q) / b if b > 0 else 0

    # Clamp to [0, 1]
    kelly = max(0, min(1, kelly))

    # Apply confidence multiplier
    conf_mult = CONFIDENCE_MULTIPLIERS.get(confidence, 0.25)
    recommended = kelly * conf_mult

    # Apply time decay if specified
    if time_horizon:
        time_mult = TIME_MULTIPLIERS.get(time_horizon, 1.0)
        recommended *= time_mult

    # Safety cap: never recommend more than 10% of bankroll per trade
    # Even if Kelly says more, single-trade risk should be capped
    MAX_POSITION = 0.10
    recommended = min(recommended, MAX_POSITION)

    edge = abs(our_prob - market_prob)

    return KellyResult(
        direction=direction,
        edge=edge,
        full_kelly=kelly,
        recommended=recommended,
        our_prob=our_prob,
        market_prob=market_prob,
        confidence=confidence,
    )


def calculate_edge(our_prob: float, market_prob: float) -> Tuple[float, str]:
    """
    Simple edge calculation.

    Returns: (edge_magnitude, direction)
    """
    edge = our_prob - market_prob
    if edge > 0.01:
        return edge, "BUY_YES"
    elif edge < -0.01:
        return abs(edge), "BUY_NO"
    else:
        return 0, "NO_TRADE"


def calculate_payout(
    bet_amount: float,
    market_prob: float,
    direction: str,
    days_to_resolution: int = None,
    risk_free_rate: float = 0.05,  # Annual risk-free rate (e.g., T-bills)
) -> dict:
    """
    Calculate potential payout for a bet.

    Args:
        bet_amount: Dollar amount to bet
        market_prob: Market price for YES (0-1)
        direction: "YES" or "NO"

    Returns:
        dict with contracts, payout, profit, return_pct
    """
    if direction.upper() == "YES":
        price = market_prob
    else:
        price = 1 - market_prob

    contracts = bet_amount / price
    payout = contracts * 1.0  # Each contract pays $1 if it wins
    profit = payout - bet_amount
    return_pct = profit / bet_amount

    result = {
        "direction": direction.upper(),
        "bet_amount": bet_amount,
        "price": price,
        "contracts": contracts,
        "payout_if_win": payout,
        "profit_if_win": profit,
        "return_pct": return_pct,
        "loss_if_lose": bet_amount,
        "days": days_to_resolution,
    }

    # Calculate annualized metrics if we know the duration
    if days_to_resolution and days_to_resolution > 0:
        # Annualized return (simple, not compounded)
        annual_multiplier = 365 / days_to_resolution
        annualized_return = return_pct * annual_multiplier

        # What risk-free would give you over same period
        risk_free_for_period = risk_free_rate * (days_to_resolution / 365)
        risk_free_profit = bet_amount * risk_free_for_period

        # Risk premium: how much extra you're getting vs risk-free
        risk_premium = return_pct - risk_free_for_period

        result.update({
            "annualized_return": annualized_return,
            "risk_free_for_period": risk_free_for_period,
            "risk_free_profit": risk_free_profit,
            "risk_premium": risk_premium,
            "annual_multiplier": annual_multiplier,
        })

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Kelly Criterion position sizing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Kelly sizing
  %(prog)s --our-prob 0.05 --market-prob 0.13 --confidence high
  %(prog)s --our-prob 0.60 --market-prob 0.45 --bankroll 10000
  %(prog)s --our-prob 0.30 --market-prob 0.50 --time-horizon months

  # Payout calculation
  %(prog)s --bet 5000 --market-prob 0.13 --direction NO
  %(prog)s --bet 1000 --market-prob 0.65 --direction YES

  # With time analysis (annualized returns)
  %(prog)s --bet 5000 --market-prob 0.13 --direction NO --days 365
  %(prog)s --bet 1000 --market-prob 0.55 --direction YES --days 14
        """
    )
    parser.add_argument("--our-prob", type=float,
                        help="Your probability estimate (0-1)")
    parser.add_argument("--market-prob", type=float,
                        help="Current market price for YES (0-1)")
    parser.add_argument("--confidence", choices=["low", "medium", "high"],
                        default="medium", help="Confidence in estimate")
    parser.add_argument("--time-horizon", choices=["days", "weeks", "months", "quarters", "years"],
                        help="Time until resolution (for opportunity cost adjustment)")
    parser.add_argument("--bankroll", type=float,
                        help="Total bankroll for dollar amounts")
    parser.add_argument("--bet", type=float,
                        help="Calculate payout for a specific bet amount")
    parser.add_argument("--direction", choices=["YES", "NO", "yes", "no"],
                        help="Direction of bet (for payout calculation)")
    parser.add_argument("--days", type=int,
                        help="Days until resolution (for annualized return)")
    parser.add_argument("--risk-free", type=float, default=0.05,
                        help="Annual risk-free rate (default: 0.05)")

    args = parser.parse_args()

    # If just calculating payout (no Kelly needed)
    if args.bet and args.direction and args.market_prob:
        payout = calculate_payout(
            args.bet,
            args.market_prob,
            args.direction,
            days_to_resolution=args.days,
            risk_free_rate=args.risk_free,
        )

        output = f"""
Payout Calculator
=====================================
Bet:          ${payout['bet_amount']:,.2f} on {payout['direction']}
Price:        {payout['price']:.0%} ({payout['price']*100:.0f} cents)
Contracts:    {payout['contracts']:,.0f}

If {payout['direction']} wins:
  Payout:     ${payout['payout_if_win']:,.2f}
  Profit:     ${payout['profit_if_win']:,.2f} ({payout['return_pct']:.1%} return)

If {payout['direction']} loses:
  Loss:       ${payout['loss_if_lose']:,.2f} (100% of bet)
"""

        # Add time-adjusted analysis if days provided
        if payout.get('days'):
            output += f"""
Time Analysis ({payout['days']} days to resolution)
=====================================
Annualized:   {payout['annualized_return']:.1%} (if you could repeat this)
Risk-free:    {payout['risk_free_for_period']:.2%} for same period (${payout['risk_free_profit']:,.2f})
Risk premium: {payout['risk_premium']:.2%} extra vs risk-free

Verdict:      {"GOOD - high annualized return" if payout['annualized_return'] > 0.25 else "MEH - consider shorter bets" if payout['annualized_return'] > 0.15 else "BAD - capital locked too long"}
"""
        output += "=====================================\n"
        print(output)
        return

    # Kelly calculation requires our-prob
    if not args.our_prob or not args.market_prob:
        parser.error("Kelly calculation requires --our-prob and --market-prob")

    result = calculate_kelly(
        our_prob=args.our_prob,
        market_prob=args.market_prob,
        confidence=args.confidence,
        time_horizon=args.time_horizon,
    )

    print(result)

    if args.bankroll:
        print(result.with_bankroll(args.bankroll))


if __name__ == "__main__":
    main()
