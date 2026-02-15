# Data and Learning Infrastructure
## AI-Native Prediction Market Trading System

---

## Executive Summary

This document defines the data architecture and machine learning infrastructure for an AI-native prediction market trading operation. Unlike traditional quant firms that bolt ML onto legacy systems, we're designing from first principles for an agent-based trading architecture where **the system gets smarter with every trade**.

### Core Principles

1. **Data is memory** - Every prediction, reasoning trace, and outcome is a training example
2. **Compounding intelligence** - Each market teaches us about the next
3. **Minimal viable complexity** - Start simple, add complexity only when proven valuable
4. **AI-first architecture** - Designed for LLM agents, not human traders

---

## Phase 1: Foundation (MVP - Weeks 1-4)

### 1.1 Data to Store

#### **Predictions Table** (SQLite: `predictions.db`)
```sql
CREATE TABLE predictions (
    prediction_id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Market identification
    market_ticker TEXT NOT NULL,
    market_title TEXT,
    event_ticker TEXT,
    category TEXT,

    -- Our estimate
    our_probability REAL NOT NULL,  -- 0-1 scale
    confidence TEXT,  -- 'low', 'medium', 'high'

    -- Market pricing
    market_price REAL,  -- 0-1 scale at time of prediction
    yes_bid INTEGER,  -- cents
    yes_ask INTEGER,  -- cents
    spread INTEGER,  -- cents

    -- Edge calculation
    edge REAL,  -- our_prob - market_price
    edge_direction TEXT,  -- 'BUY_YES', 'BUY_NO', 'NO_TRADE'

    -- Position sizing
    kelly_full REAL,
    kelly_recommended REAL,

    -- Metadata
    agent_name TEXT,  -- which agent made this prediction
    model_version TEXT,  -- claude-opus-4-5, etc
    analysis_tokens INTEGER,

    FOREIGN KEY (market_ticker) REFERENCES markets(ticker)
);

CREATE INDEX idx_predictions_market ON predictions(market_ticker);
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX idx_predictions_agent ON predictions(agent_name);
```

#### **Reasoning Traces Table**
```sql
CREATE TABLE reasoning_traces (
    trace_id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- The reasoning
    reasoning_text TEXT,  -- Full Claude response
    key_factors TEXT,  -- JSON array of bullet points
    unknowns TEXT,  -- JSON array of uncertainties
    recommended_research TEXT,  -- JSON array

    -- Decomposition
    causal_chain TEXT,  -- First-principles breakdown
    base_rates TEXT,  -- Historical priors used

    -- Devil's advocate
    counterarguments TEXT,  -- What could make us wrong?
    scenarios_where_wrong TEXT,

    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
);

CREATE INDEX idx_traces_prediction ON reasoning_traces(prediction_id);
```

#### **Market Data Table**
```sql
CREATE TABLE markets (
    ticker TEXT PRIMARY KEY,
    title TEXT,
    event_ticker TEXT,
    category TEXT,
    status TEXT,

    -- First observed
    first_seen DATETIME,

    -- Resolution
    close_time DATETIME,
    resolution_time DATETIME,
    resolved_value REAL,  -- 0 (NO) or 1 (YES)
    resolution_method TEXT,  -- 'observed', 'official_data', etc

    -- Market structure
    volume INTEGER,
    open_interest INTEGER,
    liquidity INTEGER
);

CREATE INDEX idx_markets_category ON markets(category);
CREATE INDEX idx_markets_status ON markets(status);
```

#### **Market Snapshots Table** (Price history)
```sql
CREATE TABLE market_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Prices (cents)
    yes_bid INTEGER,
    yes_ask INTEGER,
    no_bid INTEGER,
    no_ask INTEGER,
    last_price INTEGER,

    -- Activity
    volume INTEGER,
    volume_24h INTEGER,
    open_interest INTEGER,
    liquidity INTEGER,

    FOREIGN KEY (ticker) REFERENCES markets(ticker)
);

CREATE INDEX idx_snapshots_ticker ON market_snapshots(ticker);
CREATE INDEX idx_snapshots_time ON market_snapshots(timestamp);
```

#### **Outcomes Table**
```sql
CREATE TABLE outcomes (
    outcome_id TEXT PRIMARY KEY,
    market_ticker TEXT NOT NULL,
    prediction_id TEXT,

    -- Resolution
    resolved_at DATETIME,
    actual_outcome REAL,  -- 0 or 1
    our_probability REAL,  -- What we predicted
    market_price REAL,  -- What market said

    -- Performance
    brier_score REAL,  -- (prediction - outcome)^2
    log_score REAL,  -- log(prediction if YES, 1-prediction if NO)

    -- What we learned
    postmortem_notes TEXT,
    what_we_got_right TEXT,
    what_we_got_wrong TEXT,
    lessons_learned TEXT,

    FOREIGN KEY (market_ticker) REFERENCES markets(ticker),
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
);

CREATE INDEX idx_outcomes_market ON outcomes(market_ticker);
CREATE INDEX idx_outcomes_resolved ON outcomes(resolved_at);
```

#### **Trades Table** (if we execute)
```sql
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    prediction_id TEXT,
    market_ticker TEXT NOT NULL,

    -- Execution
    executed_at DATETIME,
    direction TEXT,  -- 'YES' or 'NO'
    contracts INTEGER,
    price_paid INTEGER,  -- cents per contract
    total_cost REAL,  -- dollars

    -- Close
    closed_at DATETIME,
    close_price INTEGER,
    payout REAL,
    pnl REAL,  -- profit/loss
    return_pct REAL,

    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id),
    FOREIGN KEY (market_ticker) REFERENCES markets(ticker)
);

CREATE INDEX idx_trades_prediction ON trades(prediction_id);
CREATE INDEX idx_trades_executed ON trades(executed_at);
```

### 1.2 Why SQLite for Phase 1?

**Advantages:**
- Single file database (easy backup, versioning)
- Zero configuration, no server to manage
- Full SQL support for analysis
- Fast for < 100k records
- Can upgrade to PostgreSQL later without schema changes

**When to migrate to PostgreSQL:**
- > 100k predictions (unlikely in first year)
- Need concurrent writes from multiple processes
- Want advanced features (time-series extensions, partitioning)

### 1.3 Minimal Viable Workflow

```python
# 1. Agent makes prediction
prediction = {
    'market_ticker': 'NVDA-2026Q1',
    'our_probability': 0.65,
    'market_price': 0.55,
    'edge': 0.10,
    'confidence': 'high',
    'agent_name': 'reasoner',
    'reasoning_text': "Full Claude analysis...",
    'key_factors': ["GPU demand", "supply constraints"],
}

# 2. Store prediction + reasoning
db.store_prediction(prediction)

# 3. When market resolves
outcome = {
    'market_ticker': 'NVDA-2026Q1',
    'actual_outcome': 1,  # YES
    'resolved_at': '2026-02-20',
}

# 4. Calculate performance
brier = (0.65 - 1)**2  # 0.1225 (good)
db.store_outcome(outcome)

# 5. Query for learning
# "Show me all NVDA predictions and how we did"
# "What categories are we most calibrated in?"
# "Which agents are most accurate?"
```

---

## Phase 2: Learning Systems (Weeks 5-12)

### 2.1 Calibration Model

**Goal:** Adjust our raw probability estimates based on historical accuracy.

#### Data Required
```sql
SELECT
    category,
    confidence,
    our_probability,
    actual_outcome,
    COUNT(*) as n_predictions
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY category, confidence, ROUND(our_probability, 1)
HAVING COUNT(*) >= 5  -- Need at least 5 samples
```

#### Model: Isotonic Regression per Category
```python
from sklearn.isotonic import IsotonicRegression

# For each category (e.g., "Tech Earnings")
model = IsotonicRegression()
X = raw_probabilities  # What Claude said
y = actual_outcomes    # What happened

calibrated_prob = model.predict(new_prediction)
```

**Why Isotonic Regression?**
- Non-parametric (no assumptions about shape)
- Monotonic (higher input → higher output)
- Works with small data
- Interpretable

#### Calibration Drift Detection
```sql
-- Are we getting less calibrated over time?
SELECT
    DATE(resolved_at, 'start of month') as month,
    AVG((our_probability - actual_outcome)^2) as brier_score,
    COUNT(*) as n_predictions
FROM outcomes
GROUP BY month
ORDER BY month;
```

If Brier scores increase → investigate:
- Is market getting more efficient?
- Are we overconfident?
- Has Claude model changed?

### 2.2 Feature Extraction for Mispricing

**Goal:** Identify which market characteristics predict whether we'll find edge.

#### Features to Track
```sql
CREATE TABLE market_features (
    ticker TEXT PRIMARY KEY,

    -- Market microstructure
    spread_pct REAL,
    volume_rank INTEGER,  -- Percentile
    liquidity_rank INTEGER,

    -- Timing
    hours_to_close REAL,
    days_to_close REAL,

    -- Complexity
    title_length INTEGER,
    has_numbers BOOLEAN,  -- "Will X exceed 5%?" vs vague
    category_complexity TEXT,  -- AI-adjacent, econ data, etc

    -- Competition
    num_trades INTEGER,
    num_unique_traders INTEGER,

    -- Outcome (for supervised learning)
    edge_found BOOLEAN,  -- Did we find > 5% edge?
    edge_magnitude REAL,
    was_correct BOOLEAN,  -- Did our edge direction match outcome?

    FOREIGN KEY (ticker) REFERENCES markets(ticker)
);
```

#### Model: Random Forest Classifier
```python
from sklearn.ensemble import RandomForestClassifier

# Predict: Will we find edge in this market?
X = market_features[['spread_pct', 'volume_rank', 'hours_to_close', ...]]
y = (edge_found == True)

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Feature importance tells us:
# "Low volume + wide spread + <48hrs to close = high edge probability"
```

**Use case:** Prioritize which markets to analyze first.

### 2.3 Market Regime Detection

**Goal:** Identify when markets are efficient vs inefficient.

#### Regimes to Detect

| Regime | Characteristics | Our Strategy |
|--------|----------------|--------------|
| **Efficient** | Tight spreads, high volume, fast price discovery | Avoid - no edge |
| **Inefficient** | Wide spreads, low volume, slow updates | Hunt for edge |
| **Uncertain** | Breaking news, high volatility | Wait for clarity |
| **Mispriced** | Structural mismatch (headlines vs fundamentals) | Best opportunities |

#### Simple Regime Classification
```python
def classify_regime(market):
    if market.spread_pct > 10 and market.volume < 100:
        return "inefficient"
    elif market.spread_pct < 3 and market.volume > 1000:
        return "efficient"
    elif market.volume_24h > 2 * market.volume_avg:
        return "uncertain"  # Sudden activity
    else:
        return "normal"
```

#### Advanced: Time-Series Clustering
- Cluster markets by price movement patterns
- Identify which patterns we're good at predicting
- Focus on those clusters

### 2.4 Agent Performance Tracking

**Goal:** Know which agents/approaches work best in which situations.

```sql
CREATE TABLE agent_performance (
    agent_name TEXT,
    category TEXT,

    -- Calibration
    n_predictions INTEGER,
    avg_brier_score REAL,
    calibration_score REAL,  -- How close predictions match outcomes

    -- Edge detection
    n_edges_found INTEGER,
    n_edges_correct INTEGER,  -- Edges that paid off
    edge_accuracy REAL,

    -- Confidence calibration
    high_conf_accuracy REAL,  -- When agent says "high", % correct
    medium_conf_accuracy REAL,
    low_conf_accuracy REAL,

    PRIMARY KEY (agent_name, category)
);
```

**Insights we can derive:**
- "Reasoner agent is well-calibrated on tech earnings"
- "Forecaster overconfident on economic data markets"
- "Devil's advocate improves accuracy by 3% when included"

---

## Phase 3: Feedback Loops (Weeks 13-24)

### 3.1 Automated Post-Mortems

**When market resolves:**
```python
def automated_postmortem(outcome):
    prediction = db.get_prediction(outcome.prediction_id)

    # Generate post-mortem prompt
    prompt = f"""
    MARKET: {outcome.market_title}

    OUR PREDICTION: {prediction.our_probability:.0%}
    ACTUAL OUTCOME: {"YES" if outcome.actual_outcome == 1 else "NO"}

    OUR REASONING:
    {prediction.reasoning_text}

    RESULT: We were {"CORRECT" if was_correct else "WRONG"}

    Analyze:
    1. What did we get RIGHT in our reasoning?
    2. What did we MISS or get WRONG?
    3. What should we update in our mental models?
    4. What questions should we ask next time?

    Be brutally honest. This is how we learn.
    """

    # Store lessons learned
    lessons = claude.analyze(prompt)
    db.store_postmortem(outcome.outcome_id, lessons)
```

### 3.2 Pattern Library

As we learn, build a knowledge base of patterns:

```sql
CREATE TABLE patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_name TEXT,

    -- The pattern
    description TEXT,
    when_it_applies TEXT,
    typical_edge REAL,

    -- Evidence
    n_instances INTEGER,
    success_rate REAL,

    -- Examples
    example_markets TEXT,  -- JSON array of tickers

    -- Status
    confidence TEXT,  -- 'hypothesis', 'validated', 'deprecated'
    last_updated DATETIME
);
```

**Example patterns:**
- "NVDA earnings: Market underprices supply constraints by ~5%"
- "Productivity data: Market lags AI impact by 1-2 quarters"
- "Regulatory deadlines: Slip 60% of the time when technical compliance undefined"

### 3.3 Prior Updates (Bayesian Learning)

```sql
CREATE TABLE priors (
    prior_id TEXT PRIMARY KEY,
    category TEXT,
    subcategory TEXT,

    -- Base rate
    base_rate REAL,  -- Historical frequency
    n_observations INTEGER,

    -- Confidence interval
    lower_bound REAL,
    upper_bound REAL,

    -- Metadata
    last_updated DATETIME,
    source TEXT  -- 'historical_data', 'expert_estimate', 'market_implied'
);

-- Example: What's the base rate for tech earnings beats?
INSERT INTO priors VALUES (
    'tech_earnings_beat',
    'earnings',
    'tech',
    0.62,  -- 62% of tech companies beat earnings
    150,   -- Based on 150 observations
    0.55, 0.69,  -- 95% CI
    '2026-02-14',
    'historical_data'
);
```

**Usage in reasoning:**
```python
# When predicting NVDA earnings
prior = db.get_prior('tech_earnings_beat')
# Start from 62% base rate
# Adjust based on NVDA-specific factors
# = Bayesian update
```

### 3.4 Edge Decay Detection

**Critical question:** Is our edge degrading over time?

```sql
-- Monthly edge analysis
SELECT
    DATE(p.timestamp, 'start of month') as month,
    AVG(ABS(p.edge)) as avg_edge_magnitude,
    AVG(CASE WHEN o.was_correct THEN 1 ELSE 0 END) as edge_accuracy,
    COUNT(*) as n_predictions
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY month
ORDER BY month;
```

**Signals of edge decay:**
- Edge magnitude declining
- Edge accuracy declining
- Markets we previously found edge in becoming efficient

**Response:**
- Shift to new market categories
- Refine reasoning approaches
- Update models

---

## Phase 4: Compounding Intelligence (Long-term)

### 4.1 The Flywheel

```
More predictions
    → More outcomes
        → Better calibration
            → More accurate estimates
                → Better edge detection
                    → More profitable trades
                        → More capital
                            → Can analyze more markets
                                → More predictions (loop)
```

### 4.2 Architectural Advantages

**Traditional quant firm:**
- Hire analysts (slow, expensive)
- Build models (rigid, hard to update)
- Scale by adding headcount

**AI-native firm (us):**
- Spawn agents (instant, free)
- Models improve automatically (as Claude/GPT improve)
- Scale by analyzing more markets in parallel

### 4.3 Knowledge Accumulation

Every prediction adds to our institutional knowledge:

```sql
-- After 1000 predictions, we can answer:
-- "What's our edge in NVDA earnings markets?"
SELECT AVG(edge) FROM predictions
WHERE market_title LIKE '%NVDA%' AND category = 'earnings';

-- "Which reasoning patterns lead to best outcomes?"
SELECT key_factors, AVG(brier_score)
FROM reasoning_traces r
JOIN outcomes o ON r.prediction_id = o.prediction_id
GROUP BY key_factors;

-- "What markets should we avoid?"
SELECT category, AVG(brier_score), COUNT(*)
FROM predictions p JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY category
HAVING AVG(brier_score) > 0.2;  -- Poorly calibrated
```

### 4.4 Meta-Learning

Learn about our learning:
- Which types of reasoning traces predict good outcomes?
- Do longer analyses lead to better predictions?
- Does including devil's advocate improve calibration?
- What confidence levels are actually well-calibrated?

```sql
CREATE TABLE meta_insights (
    insight_id TEXT PRIMARY KEY,
    insight_text TEXT,
    supporting_data TEXT,  -- SQL query or stats
    confidence REAL,
    discovered_at DATETIME
);

-- Example meta-insight:
-- "Predictions with >3 causal chain steps are 15% better calibrated"
-- "High confidence predictions in tech earnings are well-calibrated (92%)"
-- "Markets closing in <48hrs have 2x larger edges"
```

---

## Implementation Roadmap

### Week 1-2: Schema + Basic Storage
- [ ] Create SQLite database with core tables
- [ ] Build Python ORM/helper functions
- [ ] Test with manual data entry

### Week 3-4: Agent Integration
- [ ] Modify agents to log predictions
- [ ] Store reasoning traces
- [ ] Capture market snapshots

### Week 5-8: Outcomes Tracking
- [ ] Build market resolution monitor
- [ ] Automated outcome recording
- [ ] Basic performance metrics (Brier scores)

### Week 9-12: Calibration Model
- [ ] Collect enough data (50+ predictions)
- [ ] Build isotonic regression calibrator
- [ ] A/B test calibrated vs raw predictions

### Week 13-16: Feature Extraction
- [ ] Build market feature extraction pipeline
- [ ] Train edge detection model
- [ ] Deploy as market prioritization tool

### Week 17-20: Automated Post-Mortems
- [ ] Prompt engineering for lessons learned
- [ ] Build pattern library
- [ ] Track prior updates

### Week 21-24: Meta-Analysis
- [ ] Agent performance dashboards
- [ ] Edge decay monitoring
- [ ] Strategy refinement based on data

---

## Avoiding Overfitting

### The Danger

With small sample sizes, we can easily overfit:
- "We're 3-0 on NVDA earnings!" (3 is not statistically significant)
- "This pattern works!" (cherry-picked examples)
- "Our model predicts..." (trained on 20 samples)

### Guardrails

1. **Minimum sample sizes**
   - Don't trust patterns with < 20 instances
   - Don't build models on < 50 samples
   - Report confidence intervals, not just point estimates

2. **Out-of-sample testing**
   - Train on months 1-6, test on months 7-12
   - Don't backtest on the same data you'll trade

3. **Simplicity bias**
   - Start with simple models (isotonic regression)
   - Add complexity only when justified by data
   - "More data beats better algorithms" (for small n)

4. **Human judgment override**
   - Models inform, don't dictate
   - Agents can override model predictions
   - Track when overrides were correct

5. **Regime awareness**
   - Markets change, models become stale
   - Regular re-validation
   - Kill strategies that stop working

---

## Success Metrics

### Phase 1 (MVP)
- [ ] 50+ predictions logged with reasoning traces
- [ ] All outcomes tracked within 24hrs of resolution
- [ ] Can query: "Show me all tech earnings predictions"

### Phase 2 (Learning)
- [ ] Calibration model deployed and improving Brier scores by 10%+
- [ ] Agent performance metrics updated daily
- [ ] Can answer: "Which categories are we good at?"

### Phase 3 (Feedback)
- [ ] Automated post-mortems for 100% of resolved markets
- [ ] Pattern library with 10+ validated patterns
- [ ] Can answer: "What have we learned about X markets?"

### Phase 4 (Compounding)
- [ ] Month-over-month improvement in calibration
- [ ] Edge detection accuracy > 65%
- [ ] System recommends which markets to analyze
- [ ] Can answer: "What's our edge and where is it strongest?"

---

## Technology Stack

### Phase 1-2
- **Database:** SQLite (single file, easy to start)
- **ORM:** Raw SQL or lightweight wrapper (sqlalchemy)
- **Analysis:** Pandas, Jupyter notebooks
- **Agents:** Current Claude Code agent system

### Phase 3-4 (if needed)
- **Database:** PostgreSQL with TimescaleDB extension
- **ML:** scikit-learn, lightweight models
- **Dashboarding:** Streamlit or simple web UI
- **Orchestration:** Simple cron jobs or task queue

### What We DON'T Need (Yet)
- ❌ Kafka, microservices, Kubernetes (overkill)
- ❌ Deep learning (not enough data)
- ❌ Real-time streaming (markets update slowly)
- ❌ Data warehouses (simple SQL is fine)

---

## Appendix A: Schema Diagram

```
markets
    ├─ ticker (PK)
    ├─ title
    ├─ category
    └─ resolved_value
        ↓
    market_snapshots (price history)
        ├─ ticker (FK)
        ├─ timestamp
        └─ prices
        ↓
    predictions
        ├─ prediction_id (PK)
        ├─ market_ticker (FK)
        ├─ our_probability
        ├─ confidence
        └─ agent_name
            ↓
        reasoning_traces
            ├─ prediction_id (FK)
            ├─ reasoning_text
            ├─ key_factors
            └─ causal_chain
            ↓
        outcomes
            ├─ prediction_id (FK)
            ├─ actual_outcome
            ├─ brier_score
            └─ lessons_learned
            ↓
        trades (optional)
            ├─ prediction_id (FK)
            ├─ executed_at
            └─ pnl
```

---

## Appendix B: Example Queries

```sql
-- How calibrated are we overall?
SELECT
    confidence,
    COUNT(*) as n,
    AVG(ABS(our_probability - actual_outcome)) as mean_abs_error,
    AVG((our_probability - actual_outcome)^2) as brier_score
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY confidence;

-- Which categories have the most edge?
SELECT
    category,
    AVG(ABS(edge)) as avg_edge,
    COUNT(*) as n_predictions,
    AVG(CASE WHEN was_correct THEN 1 ELSE 0 END) as accuracy
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY category
ORDER BY avg_edge DESC;

-- Agent leaderboard
SELECT
    agent_name,
    COUNT(*) as predictions,
    AVG(brier_score) as brier,
    AVG(CASE WHEN was_correct THEN 1 ELSE 0 END) as accuracy
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY agent_name
ORDER BY brier ASC;

-- Markets we should have bet on but didn't
SELECT
    market_ticker,
    title,
    ABS(edge) as edge_magnitude,
    kelly_recommended,
    actual_outcome,
    CASE
        WHEN (edge > 0 AND actual_outcome = 1) THEN 'missed_YES'
        WHEN (edge < 0 AND actual_outcome = 0) THEN 'missed_NO'
        ELSE 'avoided_correctly'
    END as verdict
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
WHERE kelly_recommended > 0.05  -- We should have bet
AND prediction_id NOT IN (SELECT prediction_id FROM trades)  -- But didn't
ORDER BY ABS(edge) DESC;

-- Time series: Are we improving?
SELECT
    DATE(p.timestamp, 'start of month') as month,
    COUNT(*) as predictions,
    AVG((our_probability - actual_outcome)^2) as brier,
    AVG(ABS(edge)) as avg_edge
FROM predictions p
JOIN outcomes o ON p.prediction_id = o.prediction_id
GROUP BY month
ORDER BY month;
```

---

## Conclusion

This infrastructure enables **compounding intelligence** - every market we analyze makes us smarter for the next one. We start simple (SQLite + basic logging) and add complexity only as justified by data.

The key insight: **traditional quant firms treat data as input to models. We treat data as memory for agents.** Our agents learn from experience, just like human traders - but they can process thousands of markets and remember every lesson perfectly.

This is the structural advantage of AI-native trading.
