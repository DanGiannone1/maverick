---
name: probability-estimation
description: |
  Frameworks for calibrated probability estimation. Covers reference
  class forecasting, base rate sources, Bayesian updating, and
  calibration principles.
---

# Probability Estimation

Frameworks for producing accurate, calibrated probability estimates.

## Core Principle

> **Never estimate from scratch. Always start with: "How often does this type of thing happen?"**

---

## Reference Class Forecasting

The outside view beats the inside view. Always.

### Process

1. **Identify reference class** - What category is this?
2. **Find base rate** - Historical frequency in that class
3. **Adjust for specifics** - What makes this case different?
4. **Sanity check** - Does estimate make sense given base rate?

### Example

```
Question: Will startup X achieve outcome Y?

Reference class: Startups at this stage in this sector
Base rate: 15% achieve this outcome

Specific factors:
  + Strong team (+5%)
  + Good traction (+3%)
  - Competitive market (-2%)

Adjusted estimate: ~21%

Sanity check: Am I more than 2x away from base rate? If so, why?
```

### Rule of Thumb

- **<2x from base rate**: Usually fine
- **2-3x from base rate**: Need strong justification
- **>3x from base rate**: Almost certainly wrong

---

## Base Rate Sources by Domain

### Politics

| Event Type | Typical Base Rate | Source |
|------------|-------------------|--------|
| Incumbent reelection (president) | ~55% | Historical data |
| Bill passage (introduced → law) | ~3-5% | Congress.gov |
| Cabinet confirmation (unified gov) | ~95% | Senate records |
| Cabinet confirmation (divided gov) | ~80% | Senate records |
| Polling accuracy (final polls) | ±3 points | 538 analysis |

### Economics

| Event Type | Typical Base Rate | Source |
|------------|-------------------|--------|
| Fed surprise vs consensus | ~7% | Fed funds futures |
| CPI surprise >0.2% | ~15% | BLS data |
| Earnings beat estimates | ~65-75% | Sector varies |
| Recession within 12 months | ~15% baseline | NBER data |

### Tech/Corporate

| Event Type | Typical Base Rate | Source |
|------------|-------------------|--------|
| Product launch delay | ~30% | Industry analysis |
| M&A completion (announced) | ~85% | Deal data |
| Series A → Series B | ~40% | Crunchbase |
| IPO within 2 years (late stage) | ~25% | PitchBook |

### General Reference Points

| Scenario | Base Rate |
|----------|-----------|
| "Unprecedented" events | 1-5% (they happen) |
| "Sure things" failing | 5-10% |
| Expert consensus wrong | 10-20% |
| "This time is different" | Usually isn't |

---

## Bayesian Updating

Start with prior, update on evidence.

### Framework

```
Prior: Base rate probability
Likelihood ratio: P(evidence|true) / P(evidence|false)
Posterior: Updated probability

Strength of evidence:
  - Strong: LR > 10 (update a lot)
  - Moderate: LR 2-10 (update moderately)
  - Weak: LR 1-2 (barely update)
```

### Update Rules

| Evidence Strength | Update Amount |
|-------------------|---------------|
| Overwhelming (LR >100) | Can move 30+ points |
| Strong (LR 10-100) | Move 10-20 points |
| Moderate (LR 3-10) | Move 5-10 points |
| Weak (LR 1.5-3) | Move 1-5 points |
| Neutral (LR ~1) | Don't update |

### Warning Signs of Bad Updating

- Updating dramatically on single data points
- Not updating when you should (anchoring)
- Updating in direction you wanted (motivated reasoning)
- Updating more on vivid evidence than diagnostic evidence

---

## Calibration Principles

A calibrated forecaster: when they say 70%, it happens ~70% of the time.

### Common Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| Overconfidence | Say 90%, happens 70% | Widen confidence intervals |
| Underconfidence | Say 50%, happens 80% | Trust your analysis more |
| Binary thinking | Everything is 20% or 80% | Use the full range |
| Lazy uncertainty | Too many 50%s | Do the work |

### Calibration Check Questions

1. Am I using 50% too often? (lazy)
2. Am I avoiding 5% and 95%? (appropriate humility)
3. Am I bunched at 30% and 70%? (false precision)
4. Would I bet at these odds? (skin in game test)

### The 5-95 Rule

- If you say **5%**, you should be wrong ~5% of the time
- If you say **95%**, you should be wrong ~5% of the time
- Most people say 95% when they should say 80%

---

## Fermi Estimation

When base rates aren't available, decompose.

### Process

```
P(X) = P(A) × P(B|A) × P(C|A,B)

Example: Will company announce partnership by date?
  P(partnership exists) = 60%
  P(announce if exists | this quarter) = 40%
  P(by specific date | announce this quarter) = 50%

  P(X) = 0.6 × 0.4 × 0.5 = 12%
```

### Sanity Checks

- Multiply enough small probabilities and anything becomes unlikely
- Very long chains (>4 steps) compound uncertainty
- If chain has many 90% steps, check for overconfidence

---

## Output Format

```
## PROBABILITY ESTIMATE: [Question]

Reference Class:
  Category: [what type of event?]
  Base rate: X% (source: [where?])

Updating Factors:
  + [Factor 1]: +X% (because...)
  - [Factor 2]: -X% (because...)

Estimate:
  Point: X%
  Confidence interval: [X%, Y%] (80% CI)

Calibration check:
  - Distance from base rate: X points
  - Justified because: [reason]
  - What would make me update: [specific evidence]

FINAL: X% ± Y%
```

---

## Red Flags

- **"I'm 95% sure"** → Almost nothing is 95%
- **"It's 50/50"** → Often lazy uncertainty
- **"My gut says..."** → What's the base rate?
- **"This time is different"** → Probably not
- **"Obviously..."** → Things that are obvious are often wrong
