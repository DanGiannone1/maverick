# Maverick Playbook

Quick reference for daily operation.

---

## Tools

### Kelly Calculator
```bash
# Full Kelly analysis
python kelly.py --our-prob 0.05 --market-prob 0.13 --confidence high --bankroll 5000

# Payout calculator
python kelly.py --bet 1000 --market-prob 0.55 --direction NO

# Time-adjusted analysis (critical!)
python kelly.py --bet 1000 --market-prob 0.55 --direction NO --days 14
```

### Market Scanner
```bash
python niche_finder.py
```

---

## Quick Decision Tree

```
1. Is resolution < 30 days?
   NO  → Skip unless edge is 20+ points
   YES → Continue

2. Can I reason about this from first principles?
   NO  → Skip (not our game)
   YES → Continue

3. Do I have domain expertise here?
   NO  → Lower confidence, smaller size
   YES → Continue

4. Run Kelly with time adjustment:
   python kelly.py --bet X --market-prob X --direction X --days X

5. Is annualized return > 25%?
   NO  → Skip
   YES → Continue

6. Can I articulate what would change my mind?
   NO  → Skip (not reasoning, just guessing)
   YES → Execute
```

---

## Position Sizing Cheat Sheet

| Confidence | Kelly Multiplier | Max Position |
|------------|-----------------|--------------|
| Low | 25% of Kelly | 2.5% of bankroll |
| Medium | 40% of Kelly | 4% of bankroll |
| High | 50% of Kelly | 5% of bankroll |

**Hard cap: 10% per position regardless of Kelly**

---

## Time Value Cheat Sheet

| Days to Resolution | Time Multiplier | Min Edge Required |
|-------------------|-----------------|-------------------|
| 1-7 days | 1.0x | 5% |
| 7-14 days | 0.9x | 7% |
| 14-30 days | 0.7x | 10% |
| 30-60 days | 0.5x | 15% |
| 60-90 days | 0.3x | 20% |
| 90+ days | Skip | Skip |

---

## Reasoning Checklist

Before any bet:

- [ ] First principles identified (3-5 fundamental truths)
- [ ] Causal chain mapped (A → B → C → outcome)
- [ ] Market assumptions identified (what are they thinking?)
- [ ] Steel-manned both sides (best argument for YES and NO)
- [ ] Probability estimated with confidence interval
- [ ] Time-adjusted Kelly calculated
- [ ] "What would change my mind" articulated

If any box unchecked → Don't bet

---

## Best Categories for Us

### Tier 1 (Best Edge)
- Economic data releases influenced by AI
- Tech earnings (NVDA, cloud providers)
- Productivity/labor statistics

### Tier 2 (Good Edge)
- AI capability milestones
- Tech regulatory decisions
- Fed/macro with structural constraints

### Tier 3 (Moderate Edge)
- Political procedural events
- Weather (base rates + current data)
- Corporate events with deadlines

### Avoid
- Sports
- Crypto price movements
- Celebrity/entertainment
- Pure speculation
- Anything > 90 days out

---

## Daily Routine

**Morning (5 min):**
1. Check economic calendar - any releases this week?
2. Check earnings calendar - any AI-adjacent reports?
3. Quick scan of Kalshi/Polymarket for new short-term markets

**When Opportunity Found (20 min):**
1. Run through reasoning checklist
2. Calculate time-adjusted Kelly
3. Devil's advocate yourself (or use agent)
4. Execute or pass

**Weekly (15 min):**
1. Review bets placed - any resolving soon?
2. Update probability estimates if new info
3. Log outcomes and learnings

---

## Red Flags - Don't Bet If:

- "This feels like easy money" (probably missing something)
- Can't explain the causal chain clearly
- Edge comes from "gut feeling" not structure
- Would be embarrassed to explain this bet to someone smart
- Sizing feels emotional not calculated
- Resolution date is fuzzy or disputed
- Only upside, can't see how you're wrong

---

## Recovery Protocol

If a bet loses:

1. Was the reasoning sound? (Bad luck vs bad analysis)
2. What did I miss in the causal chain?
3. Were my assumptions wrong?
4. Update priors for similar markets
5. Document in learning log
6. Don't chase - next bet is independent

---

## Agent Workflow

```
/triage-markets
```

Spawns:
1. **Finder** (haiku) - scans for candidates
2. **Reasoner** (opus) - deep analysis
3. **Devil's Advocate** (opus) - attacks the analysis
4. **Lead** - synthesizes and recommends

Or manually:
1. Find market yourself
2. Use reasoner.md framework
3. Run kelly.py for sizing
4. Execute
