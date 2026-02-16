---
name: operating-model
description: |
  How Maverick operates: Find → Research → Challenge → Synthesize.
  Uses task-list pattern with parallel subagents and verifier signoff.
invocation: operate
---

# Maverick Operating Model

**Find → Research → Challenge → Synthesize**

Task-list driven workflow with parallel subagents and verifier signoff.

---

## Core Protocol: No Self-Signoff

Implementers (finders, researchers, challengers) do NOT mark tasks complete.

Only **verifiers** can approve work and mark tasks complete.

---

## Task List Structure

Create 3 tasks at the start:

```
TaskCreate: "Find bets"
TaskCreate: "Research bets" [blocked by Find]
TaskCreate: "Challenge & vet bets" [blocked by Research]
```

---

## Step A: Find Bets

**3 finder subagents in parallel**, each searching different categories.

| Finder | Categories |
|--------|------------|
| Finder 1 | Economics: Fed, CPI, unemployment, rates |
| Finder 2 | Politics: cabinet, nominations, tariffs, legislation |
| Finder 3 | Tech: AI, crypto, SpaceX, product launches |

**Finder prompt:**

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    ROLE: Finder for {category} markets.

    CONSTRAINTS:
    - Use kalshi_client.py to search PROD markets
    - Do NOT write new scripts
    - Return in under 60 seconds

    SEARCH TERMS: {search_terms}

    CRITERIA:
    - Resolution < 30 days
    - Volume > 1000 (or interesting structural setup)
    - Reasoning-amenable (not pure sports/weather randomness)

    Return top 2-3 candidates with:
    - Ticker
    - Current price (YES %)
    - Resolution date
    - Why it's interesting
    """
)
```

**After all 3 return:** Orchestrator aggregates and picks **top 3 candidates** total.

**Orchestrator marks "Find bets" complete** (no verifier needed - orchestrator curates).

---

## Step B: Research Bets

**3 researcher subagents in parallel**, one per candidate.

**Researcher prompt:**

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    ROLE: Researcher for {ticker}.

    CONSTRAINTS:
    - Use WebSearch for current data
    - Do NOT write scripts or spawn background tasks
    - Return in under 90 seconds

    MARKET: {ticker} - {title}
    Current price: {price}% YES
    Resolution: {resolution_date}

    RESEARCH AND RETURN:

    ## Current Data
    [Latest numbers/status from WebSearch - be specific with dates]

    ## Resolution Criteria
    [Exact rules - how does this market resolve?]

    ## Base Rate
    [Historical frequency of similar outcomes]

    ## Key Players
    [Who are the decision-makers? What are their incentives?]

    ## Catalysts
    [What events before resolution could move this?]

    ## Key Uncertainty
    [What could go either way?]
    """
)
```

**After all 3 return:** Dispatch **1 verifier subagent** to review all research.

**Verifier prompt:**

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    ROLE: Research Verifier. Review all 3 research packets.

    RESEARCH PACKETS:

    --- CANDIDATE 1: {ticker_1} ---
    {research_1}

    --- CANDIDATE 2: {ticker_2} ---
    {research_2}

    --- CANDIDATE 3: {ticker_3} ---
    {research_3}

    FOR EACH CANDIDATE, CHECK:
    1. Is the current data specific and dated? (not vague)
    2. Are resolution criteria clearly stated?
    3. Is the base rate sourced or just guessed?
    4. Are there obvious gaps in the research?

    DECISION:
    - If ALL research is solid → return "APPROVED" with any notes
    - If ANY research has critical gaps → return "REJECTED" with specific issues

    Be concise. Return pass/fail for each candidate with 1-2 sentence rationale.
    """
)
```

**If approved:** Orchestrator marks "Research bets" complete.

**If rejected:** Orchestrator dispatches new researcher(s) for failed candidates with feedback, then re-verifies.

---

## Step C: Challenge & Vet Bets

**3 challenger subagents in parallel**, one per candidate.

**Challenger prompt:**

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    ROLE: Challenger for {ticker}. Your job is to ATTACK the thesis.

    MARKET: {ticker} at {price}% YES

    VALIDATED RESEARCH:
    {research_packet}

    CHALLENGE THIS:

    ## Who's on the other side?
    [Who is betting the opposite? What do they know?]

    ## What could make this wrong?
    [Scenarios where our thesis fails]

    ## Information asymmetry
    [What might the market know that we don't?]

    ## Structural issues
    [Liquidity traps, resolution ambiguity, timing risks]

    ## Devil's advocate probability
    [If you HAD to argue the opposite, what probability would you assign?]

    Be adversarial. Find the holes.
    """
)
```

**After all 3 return:** Dispatch **1 verifier subagent** to review all challenges.

**Verifier prompt:**

```python
Task(
    subagent_type="general-purpose",
    prompt="""
    ROLE: Challenge Verifier. Review all 3 challenge packets.

    CHALLENGE PACKETS:

    --- CANDIDATE 1: {ticker_1} ---
    {challenge_1}

    --- CANDIDATE 2: {ticker_2} ---
    {challenge_2}

    --- CANDIDATE 3: {ticker_3} ---
    {challenge_3}

    FOR EACH CANDIDATE:
    1. Did the challenger actually attack the thesis? (not just summarize)
    2. Is the "other side" analysis substantive?
    3. Are the risk scenarios plausible?

    DECISION:
    - If challenges are rigorous → return "APPROVED"
    - If any challenge is weak/superficial → return "REJECTED" with specifics

    Be concise. Pass/fail for each with 1-2 sentence rationale.
    """
)
```

**If approved:** Orchestrator marks "Challenge & vet bets" complete.

**If rejected:** Re-dispatch challengers with feedback, then re-verify.

---

## Final: Orchestrator Synthesizes

With all tasks complete, the orchestrator generates the **Final Report**.

**For each candidate:**

1. **Estimate probability** - First-principles reasoning on validated facts
2. **Calculate edge** - Our estimate vs market price
3. **Size position** - Kelly criterion via `kelly.py`
4. **Decide** - Trade or pass

```bash
# If edge > 10 points and confidence is medium+
python kelly.py --our-prob 0.35 --market-prob 0.50 --confidence medium
```

**Final Report Format:**

```markdown
# Maverick Analysis Report - {date}

## Candidates Analyzed

### 1. {ticker_1}: {title}
**Market:** {price}% YES
**Our estimate:** {our_prob}%
**Edge:** {edge} points
**Recommendation:** {TRADE / PASS}
**Rationale:** {1-2 sentences}

### 2. {ticker_2}: {title}
...

### 3. {ticker_3}: {title}
...

## Summary
- Candidates analyzed: 3
- Trades recommended: {n}
- Total edge captured: {sum of edges}

## Key Risks
{Top risks across all candidates}
```

---

## Task Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TaskCreate("Find bets")                    ──────┐          │
│  TaskCreate("Research bets", blockedBy:[1])       │          │
│  TaskCreate("Challenge & vet", blockedBy:[2])     │          │
│                                                   │          │
│  ┌────────────────────────────────────────────────▼────────┐ │
│  │ STEP A: FIND (parallel)                                 │ │
│  │  ├── Finder 1 (economics) ─┐                            │ │
│  │  ├── Finder 2 (politics) ──┼──► Orchestrator picks 3    │ │
│  │  └── Finder 3 (tech) ──────┘    marks task complete     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ STEP B: RESEARCH (parallel + verify)                    │ │
│  │  ├── Researcher 1 ─┐                                    │ │
│  │  ├── Researcher 2 ──┼──► Verifier reviews all 3         │ │
│  │  └── Researcher 3 ─┘    approves → task complete        │ │
│  │                         rejects → re-research           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ STEP C: CHALLENGE (parallel + verify)                   │ │
│  │  ├── Challenger 1 ─┐                                    │ │
│  │  ├── Challenger 2 ──┼──► Verifier reviews all 3         │ │
│  │  └── Challenger 3 ─┘    approves → task complete        │ │
│  │                         rejects → re-challenge          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ FINAL: SYNTHESIZE                                       │ │
│  │  Orchestrator generates Final Report                    │ │
│  │  - Probability estimates                                │ │
│  │  - Edge calculations                                    │ │
│  │  - Position sizing (Kelly)                              │ │
│  │  - Trade/Pass recommendations                           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Time Budget

| Step | Subagents | Target | Max |
|------|-----------|--------|-----|
| Find | 3 parallel | 30 sec | 60 sec |
| Research | 3 parallel + verifier | 90 sec | 120 sec |
| Challenge | 3 parallel + verifier | 90 sec | 120 sec |
| Synthesize | orchestrator | 60 sec | 90 sec |
| **Total** | | **5 min** | **7 min** |

---

## Anti-Patterns

**Subagent anti-patterns:**
- Writing new Python scripts
- Spawning background bash tasks
- Taking more than 90 seconds
- Marking tasks as completed (only verifiers do this)
- Producing lengthy reports (be concise)

**Orchestrator anti-patterns:**
- Skipping verification steps
- Trading without edge > 10 points
- Averaging conflicting estimates (synthesize, don't average)
- Running steps sequentially when they can be parallel

---

## Tool Usage Summary

| Step | Tool | Count | Who |
|------|------|-------|-----|
| Setup | TaskCreate | 3 | Orchestrator |
| Find | Task | 3 parallel | Finders |
| Research | Task | 3 parallel | Researchers |
| Research verify | Task | 1 | Verifier |
| Challenge | Task | 3 parallel | Challengers |
| Challenge verify | Task | 1 | Verifier |
| Synthesize | kelly.py + reasoning | - | Orchestrator |

**Total subagent calls:** 11 (3 + 3 + 1 + 3 + 1)

---

## After the Report

**If trading:**
1. Record prediction in database for calibration
2. Execute via Kalshi API (or dry run)
3. Set reminder to check resolution

**If passing on all:**
1. Document why (no edge found)
2. Run the loop again later
