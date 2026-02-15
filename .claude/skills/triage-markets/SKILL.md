---
name: triage-markets
description: |
  Multi-agent orchestration workflow for analyzing prediction markets.
  Coordinates a reasoning-first approach across specialized agents.
invocation: triage markets
---

# Triage Niche Markets

Use agent teams to analyze niche prediction markets and find mispricing opportunities through **deep logical reasoning**.

## Philosophy: Reasoning Before Research

Most AI trading tools focus on information gathering (news, sentiment, data).
Our edge is **reasoning** - thinking deeper than other market participants.

**The market has the same facts you do. The edge is processing them better.**

Example (Taiwan invasion market at 13%):
- Most traders: "China-Taiwan tensions high, maybe 10-15%?"
- Our reasoning: TSMC fabs → strategic US interest → guaranteed US defense → MAD scenario → rational actor won't trigger → ~1-2%

## When to Use

- User says "triage markets", "analyze markets", "find opportunities"
- User wants to scan Kalshi for mispriced bets
- User wants multi-perspective analysis on prediction markets

## Team Structure

Spawn a 7-agent team with specialized roles. Each agent has a detailed persona in `.claude/agents/`.

| Agent | Model | Role |
|-------|-------|------|
| Finder | sonnet | Scan for short-term, reasoning-amenable markets |
| Reasoner | opus | Deep first-principles analysis |
| Forecaster | opus | Base rates and calibration |
| Researcher | opus | Targeted fact-finding (on demand) |
| Devil's Advocate | opus | Adversarial review |
| Philosopher | opus | Meta-reasoning and assumptions |
| Quant | opus | Kelly sizing and risk limits |
| Market Maker | opus | Execution analysis |

## Task Flow (Reasoning-First)

```
PHASE 1: Discovery
├── Finder: Scan for short-term, reasoning-amenable markets
└── Output: 5-10 candidates with context

PHASE 2: Pure Reasoning (NO RESEARCH YET)
├── Reasoner: First principles + causal chains for each candidate
└── Output: Initial probability estimates

PHASE 3: Calibration
├── Forecaster: Base rates + calibration check
└── Output: Adjusted probabilities with confidence intervals

PHASE 4: Targeted Research
├── Researcher: Answer specific questions only
└── Output: Facts that resolve uncertainty

PHASE 5: Adversarial Review
├── Devil's Advocate: Attack each thesis
├── Reasoner: Respond to challenges
└── Output: Approved / Conditional / Rejected

PHASE 6: Philosophical Review
├── Philosopher: Question the question itself
├── Check: Definitional clarity, framing, buried assumptions
└── Output: Confidence ceiling, reframe recommendations, unknown unknowns

PHASE 7: Risk Sizing
├── Quant: Kelly + time adjustment + correlation check
└── Output: Position sizes for approved trades

PHASE 8: Execution Check
├── Market Maker: Liquidity + spread + true edge
└── Output: Execute / Reduce / Skip

PHASE 9: Final Report
└── Lead: Compile recommendations with full audit trail
```

## Output Format

The team should produce a final report:

```markdown
# Niche Market Triage Report
Generated: [timestamp]

## Executive Summary
- Markets scanned: X
- Candidates analyzed: Y
- Actionable opportunities: Z

## Opportunities

### [STRONG BUY] Market Title
- **Ticker**: XXX
- **Market Price**: X%
- **Our Estimate**: Y% (confidence: high)
- **Edge**: +Z%
- **Kelly Sizing**:
  - Full Kelly: X% of bankroll
  - Recommended (fractional): Y% of bankroll
  - Max position: $Z at current price
- **Reasoning Chain**:
  A → B → C → Therefore probability is ~Y%
- **First Principles Applied**:
  - Principle 1
  - Principle 2
- **Key Assumptions We're Making**:
  - Assumption 1
  - Assumption 2
- **What Would Change Our Mind**:
  - If X happens, reassess
  - If Y becomes true, exit
- **Devil's Advocate Verdict**: Approved / Concerns noted

### [WEAK BUY] Market Title
...

### [PASS] Market Title
- **Why**: Insufficient edge / Devil's Advocate found fatal flaw
```

## Reasoning Framework

Each market goes through this reasoning framework:

### Step 1: First Principles
What fundamental truths apply regardless of current narrative?
- Physical constraints
- Institutional structures
- Incentive alignment
- Historical base rates

### Step 2: Causal Chains
Map out: Premise → Step 1 → Step 2 → Outcome
- What chain must complete for YES?
- What chain must complete for NO?
- Where could each chain break?

### Step 3: Assumption Autopsy
What must the market be assuming for current price to be correct?
- Are these assumptions reasonable?
- What evidence contradicts them?

### Step 4: Steel-Man Both Sides
- Best argument for YES (even if we disagree)
- Best argument for NO (even if we disagree)

### Step 5: Probability Estimate
- Point estimate
- Confidence interval
- Calibration check (am I overconfident?)

### Step 6: Edge Assessment
- Compare to market
- Account for transaction costs
- Apply Kelly sizing

## Trade Criteria

Only trade when:
- Edge > 5% (after reasoning and research)
- Confidence is medium or high
- Devil's Advocate approved OR concerns are addressable
- Spread + fees < Edge
- Kelly sizing suggests position > minimum
- We can articulate what would change our mind

## Best Practices

1. **Reasoning BEFORE Research** - Don't let headlines pollute your thinking
2. **Use Opus for Everything** - Maximum reasoning power (Sonnet only for Finder)
3. **Limit to 5-10 markets** - Deep analysis > broad scanning
4. **Require Devil's Advocate** - Every trade gets challenged
5. **Document the chain** - Full reasoning trail for learning
6. **Track outcomes** - Log predictions vs actuals over time
7. **Update on new info** - Re-run reasoning if cruxes resolve

## Anti-Patterns to Avoid

- Generic research dumps (noise, not signal)
- Anchoring on first price you see
- Skipping Devil's Advocate because "we're confident"
- Over-sizing (Kelly assumes perfect probability estimates)
- Trading outside your reasoning domain
- Letting emotion override causal chains
