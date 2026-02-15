---
name: kelly-sizing
description: |
  Kelly criterion position sizing framework. Covers the formula,
  confidence adjustments, time decay, and portfolio limits.
---

# Kelly Sizing

Position sizing using the Kelly criterion with practical adjustments.

## Core Philosophy

> **Kelly maximizes long-term growth, but full Kelly is too aggressive.**
> Use fractional Kelly to trade growth for reduced volatility.

---

## The Kelly Formula

### For BUY_YES (market underpriced)

```
p = your probability of YES
b = (1 - market_price) / market_price  (the odds)
Kelly = (p * b - (1-p)) / b
```

### For BUY_NO (market overpriced)

```
p = your probability of NO (= 1 - your YES probability)
b = market_price / (1 - market_price)
Kelly = (p * b - (1-p)) / b
```

### Interpretation

- Kelly > 0: Positive edge, bet this fraction
- Kelly = 0: No edge, don't bet
- Kelly < 0: Negative edge, bet the other side

---

## CLI Tool: `kelly.py`

Always use the tool for position sizing calculations.

### Basic Usage

```bash
# Calculate Kelly for a trade
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence medium

# With bankroll for dollar amounts
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence medium --bankroll 10000

# With time horizon adjustment
python kelly.py --our-prob 0.30 --market-prob 0.45 --confidence high --time-horizon months

# Payout analysis for existing position
python kelly.py --bet 1000 --market-prob 0.45 --direction NO --days 14
```

### Output Example

```
Kelly Calculation
=====================================
Direction:    BUY_NO
Edge:         15.0% (15 points)

Our estimate: 30.0%
Market price: 45.0%
Confidence:   medium

Full Kelly:   33.3% of bankroll
Recommended:  13.3% of bankroll (fractional)
=====================================
```

---

## Confidence Adjustments

Never use full Kelly. Adjust based on confidence in your estimate.

| Confidence | Kelly Fraction | Rationale |
|------------|----------------|-----------|
| Low | 25% | High uncertainty in probability estimate |
| Medium | 40% | Moderate confidence |
| High | 50% | Strong confidence (never go higher) |

### Why Not Full Kelly?

- Assumes perfect probability estimates (we don't have them)
- Single estimation error can cause massive drawdown
- Fractional Kelly sacrifices ~10-15% growth for ~50% less volatility

---

## Time Adjustments

Capital has opportunity cost. Discount for duration.

| Resolution | Multiplier | Minimum Edge Required |
|------------|------------|----------------------|
| 1-7 days | 1.0x | 5% |
| 7-14 days | 0.9x | 7% |
| 14-30 days | 0.7x | 10% |
| 30-60 days | 0.5x | 15% |
| 60-90 days | 0.3x | 20% |
| 90+ days | 0.1x or skip | 25%+ |

### Calculation

```
Final size = Kelly × Confidence fraction × Time multiplier
```

---

## Hard Limits (Non-Negotiable)

| Rule | Limit | Rationale |
|------|-------|-----------|
| Single position max | 10% of bankroll | No single bet can kill us |
| Correlated positions | 25% total | Related bets compound risk |
| Daily drawdown limit | 15% | Stop trading if hit |
| Weekly drawdown limit | 25% | Reassess strategy if hit |

### Correlation Definition

Positions are correlated if:
- Same underlying event (different markets on same outcome)
- Causally linked (if A happens, B becomes more likely)
- Same category risk (all political, all tech earnings)

**Rule:** Sum of correlated position sizes ≤ 25% of bankroll

---

## Position Sizing Workflow

```
## POSITION SIZING: [Market]

Input:
  Our probability: X%
  Market price: X%
  Confidence: low/medium/high
  Days to resolution: X
  Current bankroll: $X

Calculations:
  Edge: X points
  Direction: BUY_YES / BUY_NO
  Full Kelly: X%
  Confidence adjustment: X%
  Time adjustment: X%
  Final recommended: X%

Dollar amount: $X
Contracts: X @ Xc

Risk check:
  [ ] Under single position cap (10%)
  [ ] No correlation breach
  [ ] Edge meets minimum for duration
  [ ] Annualized return: X%

VERDICT: APPROVED / REDUCE SIZE / REJECT
```

---

## When to Reject

**Automatic rejection:**
- Position would exceed 10% cap
- Would breach correlation limits
- Current drawdown exceeds limits
- Edge < minimum for time horizon

**Recommend reduction:**
- Near limits but not breaching
- Moderate confidence on large edge
- Uncertainty in probability estimate

---

## Red Flags

| Signal | Problem | Action |
|--------|---------|--------|
| "This is a sure thing" | Overconfidence | Reduce size |
| "Let's size up to make back losses" | Tilt | Never do this |
| Kelly says >50% | Bad inputs | Recheck calculation |
| "It's small so limits don't matter" | Slippery slope | Limits always apply |
| "Gut says more" | Emotion | Trust the math |

---

## Quick Reference

### Minimum Edge by Timeframe

| Days Out | Min Edge |
|----------|----------|
| 1-7 | 5% |
| 7-14 | 7% |
| 14-30 | 10% |
| 30-60 | 15% |
| 60-90 | 20% |
| 90+ | 25%+ |

### Confidence Multipliers

| Confidence | Multiply Kelly by |
|------------|-------------------|
| Low | 0.25 |
| Medium | 0.40 |
| High | 0.50 |

### Time Multipliers

| Horizon | Multiply by |
|---------|-------------|
| Days | 1.0 |
| Weeks | 0.7-0.9 |
| Months | 0.5 |
| Quarters | 0.3 |
| Years | 0.2 |

---

## Remember

1. **Survival first** - Can't compound if you're broke
2. **Kelly is a ceiling** - Never go above, often go below
3. **Correlation kills** - Diversification is free risk reduction
4. **Time is money** - Long lockup needs massive edge
5. **Limits are rules** - Not guidelines, rules
