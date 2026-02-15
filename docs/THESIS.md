# Maverick Trading Thesis

## Core Philosophy

**The market has the same information you do. The edge is processing it better.**

We don't compete on:
- Speed (HFT bots win)
- Data access (institutions win)
- Capital (whales win)

We compete on:
- **Reasoning depth** (thinking through causal chains others skip)
- **Domain expertise** (understanding AI implications before market does)
- **Capital velocity** (short-term bets compound faster)
- **Discipline** (Kelly sizing, time-adjusted returns)

---

## The Reasoning Edge

Most market participants:
- Anchor on headlines and recent events
- Price based on sentiment and vibes
- Confuse "feels scary" with "is probable"
- Don't think through full causal chains

We:
- Decompose into first principles
- Map complete causal chains (A → B → C → outcome)
- Identify what the market is assuming
- Steel-man both sides before betting
- Only bet when we can articulate what would change our mind

### Example: Taiwan Invasion Market

**Market says:** 13% chance of invasion

**Headlines-based thinking:** "Tensions are high, military exercises, could happen"

**First-principles reasoning:**
```
TSMC fabs in Taiwan
  → 90% of advanced chips (existential US interest)
  → US would defend militarily
  → China knows this
  → MAD scenario
  → Rational actor won't trigger MAD
  → Probability ≈ 1-2%, not 13%
```

**Edge:** 11 points by thinking through the causal chain.

---

## Capital Velocity > Large Edges

A 15% return locked up for 1 year is worse than 4 × 5% returns over 1 quarter.

### The Math

| Strategy | Return | Duration | Annualized |
|----------|--------|----------|------------|
| One 15% bet | 15% | 12 months | 15% |
| Four 5% bets | ~22% | 3 months each | ~22% |
| Twelve 2% bets | ~27% | 1 month each | ~27% |

### Time-Adjusted Decision Rule

Before any bet, calculate:
```bash
python kelly.py --bet 1000 --market-prob 0.XX --direction YES --days 14
```

| Annualized Return | Verdict |
|-------------------|---------|
| > 25% | Good - proceed |
| 15-25% | Meh - only if edge is very confident |
| < 15% | Bad - find shorter-term opportunities |

### Opportunity Cost

Money locked in a 1-year bet at 15% return:
- Could earn 5% risk-free (T-bills)
- Could compound through multiple shorter bets
- Is exposed to tail risk for modest premium

**Rule:** Long-dated bets (90+ days) require massive edge (20+ points) or small position size.

---

## Domain Expertise: AI

Our structural edge is understanding AI before the market does.

### Where Market Gets AI Wrong

| Market Misconception | Reality |
|---------------------|---------|
| Overhypes near-term capabilities | Knows what's technically hard |
| Underhypes long-term implications | Sees second-order effects |
| Prices headlines, not fundamentals | Understands actual capability curves |
| Misses economic implications | Sees productivity/labor effects coming |

### AI-Adjacent Opportunities

**Tier 1: Direct AI Markets**
- Model releases, capability benchmarks
- Moderate edge (everyone watches these)

**Tier 2: AI → Tech Earnings**
- NVDA, cloud providers, infrastructure plays
- Better edge (understand real demand vs hype)

**Tier 3: AI → Economic Effects**
- Productivity stats, labor markets, inflation components
- Best edge (nobody connecting these dots yet)

**Tier 4: AI → Regulatory**
- Policy deadlines, technical compliance
- Good edge (understand what's technically feasible to regulate)

---

## Bet Selection Criteria

### Must Have
- [ ] Resolution in < 30 days (capital velocity)
- [ ] Structurally constrained outcome (not coin flip)
- [ ] Clear causal chain we can articulate
- [ ] Know what would change our mind
- [ ] Annualized return > 25%

### Should Have
- [ ] Domain expertise applies (AI-adjacent)
- [ ] Market pricing on sentiment, not structure
- [ ] Observable inputs before resolution
- [ ] Historical base rates available

### Avoid
- [ ] Resolution > 90 days (capital locked)
- [ ] Pure speculation (no structural constraints)
- [ ] Sports/entertainment (not our edge)
- [ ] Can't articulate the causal chain
- [ ] Don't know what would change our mind

---

## Position Sizing

### Kelly Formula
```
Edge = |Our probability - Market probability|
Kelly% = (edge-adjusted formula in kelly.py)
```

### Confidence Adjustment
| Confidence | Kelly Multiplier |
|------------|-----------------|
| Low | 25% |
| Medium | 40% |
| High | 50% |

### Time Adjustment
| Resolution | Multiplier |
|------------|------------|
| Days | 1.0x |
| Weeks | 0.7x |
| Months | 0.5x |
| Quarters | 0.3x |
| Years | 0.2x |

### Hard Caps
- Never > 10% of bankroll on single bet
- Never > 25% total exposure in correlated positions

---

## Workflow

```
1. FINDER scans for candidates
   - Short duration (< 30 days)
   - Reasoning-amenable category
   - Structural constraints present

2. REASONER analyzes each candidate
   - First principles decomposition
   - Causal chain mapping
   - Steel-man both sides
   - Probability estimate

3. DEVIL'S ADVOCATE attacks the analysis
   - Find logical flaws
   - Challenge assumptions
   - Identify what would make us wrong

4. KELLY SIZING calculates position
   - Edge + confidence + time adjustment
   - Respects hard caps

5. EXECUTE (or pass)
   - Only if criteria met
   - Document reasoning for later review
```

---

## What We Don't Do

- Chase speed (bots win)
- Trade outside our domain expertise
- Bet on pure speculation
- Lock up capital for modest returns
- Skip the devil's advocate
- Size based on feelings
- Ignore time value of money
