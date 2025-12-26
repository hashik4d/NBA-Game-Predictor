# NBA Betting Agent — Hybrid Blueprint
**Stats Model + Multi-LLM Consensus + Risk Engine**

*Status Legend:*
- [✅ IMPLEMENTED]: Live in current codebase
- [⚠️ PARTIAL]: Started but needs expansion (e.g., mocks to real data)
- [❌ TODO]: Not yet started

This system combines:
- A **data-driven predictive model** (repeatable, backtestable)
- A **multi-LLM consensus layer** (context + risk audit)
- A **decision & bankroll engine** (discipline and protection)

Goal: find real edges *and* avoid fragile bets.

---

## 1. High-Level Architecture

Scheduler [✅ IMPLEMENTED] (`nba_service.py`)
→ Fetch Games / Odds / Stats / Injuries [✅ IMPLEMENTED]
→ Build Fact Pack (JSON) [✅ IMPLEMENTED]
→ Stats Model (probabilities + edge) [❌ TODO]
→ Candidate Shortlist [❌ TODO]
→ LLM Ensemble (risk & context audit) [⚠️ PARTIAL] (Voting exists, deep audit roles missing)
→ Consensus + Disagreement [⚠️ PARTIAL] (Simple voting only)
→ Decision Engine (bet / no-bet + stake) [❌ TODO]
→ Notify / Execute [❌ TODO]
→ Log Everything [❌ TODO] (No Database)


---

## 2. Inputs

### 2.1 Schedule [✅ IMPLEMENTED]
- `game_id`
- start time (UTC)
- home team / away team
- venue

### 2.2 Odds [✅ IMPLEMENTED]
- book
- timestamp
- market (moneyline initially)
- home price / away price

> Timestamp is critical for edge calculation and CLV. [✅ IMPLEMENTED]

### 2.3 Team & Player Stats [✅ IMPLEMENTED]
Minimum:
- net rating / ORtg / DRtg (or proxy)
- pace
- last 5 / last 10 net rating
- home / away splits
- rest days, B2B flags [✅ IMPLEMENTED]

### 2.4 Injuries [✅ IMPLEMENTED]
Structured only:
- player
- team
- status (`out | doubtful | questionable | probable`)
- expected minutes delta
- importance score (0–1)
- source confidence (0–1)
*Status: Live scraping from ESPN (Active).*
**Example Output:**
```json
[
  {
    "player": "LeBron James",
    "position": "SF",
    "est_return_date": "Jan 12",
    "status": "Day-To-Day",
    "expected_minutes_change": "-5",
    "importance_score": 9.5
  },
  {
    "player": "Gabe Vincent",
    "status": "Out",
    "expected_minutes_change": "-30",
    "importance_score": 5.0
  }
]
```

---

## 3. Data Storage (Minimal Tables) [✅ IMPLEMENTED]
*Schema defined in `backend/database.py`. Wiring in progress.*

### games [✅ IMPLEMENTED]
- game_id
- season
- game_time_utc
- home_team
- away_team
- venue

### odds_snapshots [✅ IMPLEMENTED]
- odds_id
- game_id
- timestamp_utc
- book
- market
- home_price
- away_price

### team_features [✅ IMPLEMENTED]
- game_id
- timestamp_utc
- feature columns

### injury_reports [✅ IMPLEMENTED]
- game_id
- timestamp_utc
- player
- team
- status
- minutes_delta
- importance
- source_confidence

### predictions [✅ IMPLEMENTED]
- game_id
- timestamp_utc
- model_version
- p_home_win
- p_away_win
- edge
- candidate (boolean)

### llm_reviews [✅ IMPLEMENTED]
- game_id
- timestamp_utc
- provider
- model_name
- prompt_version
- support_prob
- injury_uncertainty
- risk_flags (array)
- raw_json

### decisions [✅ IMPLEMENTED]
- game_id
- timestamp_utc
- action (BET / NO_BET)
- market
- side
- stake
- consensus_prob
- disagreement
- final_edge
- summary

### results [✅ IMPLEMENTED]
- game_id
- final_score
- winner
- closing_odds (optional)

---

## 4. Fact Pack (Single Source of Truth) [✅ IMPLEMENTED]
*Implemented in `nba_service.get_game_context()`*

```json
{
  "game": {
    "game_id": "YYYYMMDD-AWAY@HOME",
    "start_time_utc": "...",
    "home_team": "HOME",
    "away_team": "AWAY"
  },
  "odds": {
    "timestamp_utc": "...",
    "book": "BookX",
    "moneyline": { "home": -150, "away": +130 }
  },
  "team_form": {
    "home": { "net_rating": 4.8, "pace": 98.2, "last5_net": 3.1 },
    "away": { "net_rating": 1.2, "pace": 100.1, "last5_net": -0.4 }
  },
  "schedule_context": {
    "home_rest_days": 2,
    "away_rest_days": 1,
    "home_b2b": false,
    "away_b2b": false
  },
  "injuries": [
    {
      "player": "Player A",
      "team": "AWAY",
      "status": "questionable",
      "minutes_delta": -10,
      "importance": 0.9,
      "source_confidence": 0.6
    }
  ],
  "constraints": {
    "market": "moneyline",
    "use_only_this_data": true
  }
}
```

LLMs must reason only from this pack. [✅ IMPLEMENTED] (Prompts enforced)

## 5. Stats Model (Edge Finder) [❌ TODO]
*Currently relying purely on LLM reasoning.*

Output
- P(home_win)
- P(away_win)
- edge = P_model − P_implied

Recommended models
- Logistic Regression
- XGBoost / LightGBM
- Elo + adjustments

Core features
- net_rating_diff
- pace_diff
- home_advantage
- rest_diff
- injury_impact_diff
- last5_net_diff

Candidate threshold
- Conservative: edge ≥ 0.04
- Standard: edge ≥ 0.03
- Aggressive: edge ≥ 0.02 (requires stricter risk gating)

## 6. LLM Ensemble (Risk & Context Audit) [⚠️ PARTIAL]
*Basic voting implemented. Advanced audit roles described below are pending.*

Role specialization
- Injury/rotation auditor [❌ TODO]
- Schedule & fatigue auditor [❌ TODO]
- Matchup & pace auditor [❌ TODO]
- Devil’s advocate (try to kill the bet) [❌ TODO]

Required JSON output [✅ IMPLEMENTED] (Using simpler schema "winner/confidence/reason")
```json
{
  "support_prob": 0.61,
  "injury_uncertainty": 0.28,
  "risk_flags": ["STAR_Q", "ROTATION_VOLATILE"],
  "reason_codes": ["injury", "rest", "net_rating"],
  "rationale": "..."
}
```

Invalid JSON = discard response. [✅ IMPLEMENTED]

## 7. Consensus & Disagreement [⚠️ PARTIAL]
Consensus probability
consensus_prob = Σ(w_i * p_i) / Σ(w_i) [✅ IMPLEMENTED] (Simple Average)

Disagreement
disagreement = standard_deviation(p_i) [❌ TODO]

Interpretation
- Low disagreement → stable bet
- High disagreement → fragile / missing info

## 8. Decision Engine (Three Gates) [❌ TODO]
*Currently logic is: Majority vote wins.*

Gate 1 — Stats Edge
- edge ≥ threshold

Gate 2 — LLM Trust
- disagreement ≤ 0.08
- avg_injury_uncertainty ≤ 0.25

Gate 3 — Hard Blocks
- STAR_Q + low confidence → NO BET
- stale odds (> 60 min) → refresh
- disagreement > 0.12 → NO BET

## 9. Stake Sizing [❌ TODO]
Safe mode
- 1% bankroll per bet
- max 5% exposure per day
- cap per bet: 3%

Fractional Kelly
- kelly = (b*p − q) / b
- stake = bankroll * 0.25 * kelly

Cap at 3%.

## 10. Execution Modes [❌ TODO]
- Advisory [✅ IMPLEMENTED] (UI Display)
- Manual bet
- Semi-Auto
- Auto bet below $X
- Manual approval above
- Full Auto
- Only after strong logs + controls

## 11. Observability [❌ TODO]
Track:
- ROI
- edge vs outcome
- disagreement distribution
- veto effectiveness
- CLV
- API latency & failure rates

Alerts:
- stale odds
- injury feed down
- abnormal bet volume
- sudden disagreement spikes

## 12. Evaluation Loop (Weekly) [❌ TODO]
- Retrain or recalibrate stats model
- Reweight LLMs based on calibration
- Tune thresholds
- Review blocked bets that would’ve lost
