
import sqlite3
import json
from datetime import datetime

DB_NAME = "nba_predictor.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database with the schema defined in 'Total_Thingstoimplement.md'.
    """
    conn = get_db_connection()
    c = conn.cursor()

    # 1. GAMES
    c.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            season TEXT,
            game_time_utc TEXT,
            home_team TEXT,
            away_team TEXT,
            venue TEXT
        )
    ''')
    
    # 2. ODDS_SNAPSHOTS
    c.execute('''
        CREATE TABLE IF NOT EXISTS odds_snapshots (
            odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            book TEXT,
            market TEXT,
            home_price TEXT,
            away_price TEXT,
            spread TEXT,
            total TEXT,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    # 3. TEAM_FEATURES
    c.execute('''
        CREATE TABLE IF NOT EXISTS team_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            home_ortg REAL,
            home_drtg REAL,
            home_pace REAL,
            home_net_rtg REAL,
            away_ortg REAL,
            away_drtg REAL,
            away_pace REAL,
            away_net_rtg REAL,
            home_rest_days INTEGER,
            away_rest_days INTEGER,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    # 4. INJURY_REPORTS
    c.execute('''
        CREATE TABLE IF NOT EXISTS injury_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            team TEXT,
            player TEXT,
            status TEXT,
            est_return_date TEXT,
            minutes_delta TEXT,
            importance_score REAL,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    # 5. PREDICTIONS
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            model_version TEXT,
            predicted_winner TEXT,
            confidence_score INTEGER,
            analysis_summary TEXT,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    # 6. LLM_REVIEWS (Granular AI logs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS llm_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            provider TEXT,  -- e.g. "Claude", "GPT-5"
            model_name TEXT,
            prompt_version TEXT,
            raw_response TEXT,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    # 7. DECISIONS (The Agent's final call)
    c.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT,
            timestamp_utc TEXT,
            action TEXT,   -- "BET" or "NO_BET"
            market TEXT,   -- "Moneyline", "Spread"
            side TEXT,     -- "Home", "Away", "Over", "Under"
            stake_units REAL,
            rationale TEXT,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')
    
    # 8. RESULTS (Ground Truth)
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            game_id TEXT PRIMARY KEY,
            final_home_score INTEGER,
            final_away_score INTEGER,
            winner TEXT,
            FOREIGN KEY(game_id) REFERENCES games(game_id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database {DB_NAME} initialized successfully.")

def save_game_context(game_id: str, season: str, time_utc: str, home: str, away: str, venue: str):
    """
    Saves the static game metadata. Idempotent (INSERT OR IGNORE).
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO games (game_id, season, game_time_utc, home_team, away_team, venue)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (game_id, season, time_utc, home, away, venue))
    conn.commit()
    conn.close()

def save_odds_snapshot(game_id: str, odds: dict):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO odds_snapshots (game_id, timestamp_utc, book, market, home_price, away_price, spread, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        game_id, 
        datetime.utcnow().isoformat(), 
        odds.get('source', 'Unknown'), 
        'Composite', 
        odds.get('home_odds', 'N/A'), 
        odds.get('away_odds', 'N/A'),
        odds.get('spread', 'N/A'),
        odds.get('total', 'N/A')
    ))
    conn.commit()
    conn.close()

def save_team_features(game_id: str, features: dict):
    """
    Saves team metrics (net ratings, pace, etc.)
    Expected structure from context['team_metrics']:
    {
        "home": { "net_rtg": 5.5, ... },
        "away": { "net_rtg": -2.1, ... }
    }
    PLUS context['rest_travel'] for rest days.
    """
    # Defensive check
    if not features or 'team_metrics' not in features:
        return

    metrics = features.get('team_metrics', {})
    home_m = metrics.get('home', {})
    away_m = metrics.get('away', {})
    
    rest = features.get('rest_travel', {})
    home_r = rest.get('home', {})
    away_r = rest.get('away', {})

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO team_features (
            game_id, timestamp_utc,
            home_ortg, home_drtg, home_pace, home_net_rtg,
            away_ortg, away_drtg, away_pace, away_net_rtg,
            home_rest_days, away_rest_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        game_id,
        datetime.utcnow().isoformat(),
        home_m.get('off_rtg', 0),
        home_m.get('def_rtg', 0),
        home_m.get('pace', 0),
        home_m.get('net_rtg', 0),
        away_m.get('off_rtg', 0),
        away_m.get('def_rtg', 0),
        away_m.get('pace', 0),
        away_m.get('net_rtg', 0),
        home_r.get('rest_days', 0),
        away_r.get('rest_days', 0)
    ))
    conn.commit()
    conn.close()

def save_injury_reports(game_id: str, injuries: dict):
    """
    Saves a list of injuries.
    Expected structure from context['injuries']:
    {
        "home": [ { "player": "X", "status": "Day-To-Day", ... } ],
        "away": [ ... ]
    }
    """
    if not injuries:
        return

    conn = get_db_connection()
    c = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    
    # Helper to insert a list of players for a specific team side
    def insert_list(team_name, player_list):
        for p in player_list:
            c.execute('''
                INSERT INTO injury_reports (
                    game_id, timestamp_utc, team, player, status,
                    est_return_date, minutes_delta, importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_id,
                timestamp,
                team_name,
                p.get('player', 'Unknown'),
                p.get('status', 'Unknown'),
                p.get('return_date', 'N/A'),
                str(p.get('minutes_delta', 0)), # Store as text if flexible, or tweak schema
                p.get('importance', 0.0)
            ))

    # Home
    insert_list('Home', injuries.get('home', []))
    # Away
    insert_list('Away', injuries.get('away', []))

    conn.commit()
    conn.close()

def save_prediction(game_id: str, result: dict):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Save top-level consensus
    c.execute('''
        INSERT INTO predictions (game_id, timestamp_utc, model_version, predicted_winner, confidence_score, analysis_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        game_id,
        datetime.utcnow().isoformat(),
        "Flagship-2025-Ensemble",
        result.get('predictedWinner'),
        result.get('confidence'),
        result.get('analysis')
    ))
    
    conn.commit()
    conn.close()

def save_decision(game_id: str, decision: dict):
    """
    Saves the final betting decision to the database.
    
    Args:
        game_id: Unique identifier for the game (format: YYYYMMDD-AWAY@HOME)
        decision: Decision dictionary containing:
            - action: str ("BET MAX", "BET SMALL", or "PASS")
            - gates: dict with edge, consensus, confidence status
    
    Raises:
        sqlite3.Error: If database write fails
        ValueError: If decision data cannot be serialized
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Safely serialize gates data
    try:
        gates_json = json.dumps(decision.get('gates', {}))
    except (TypeError, ValueError) as e:
        print(f"[Warning] Failed to serialize decision gates: {e}")
        gates_json = json.dumps({"error": "Serialization failed"})
    
    c.execute('''
        INSERT INTO decisions (
            game_id, timestamp_utc, action, 
            market, side, stake_units, rationale
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        game_id,
        datetime.utcnow().isoformat(),
        decision.get('action', 'PASS'),
        'Moneyline',  # Default market
        'TBD',  # Would need to determine from winner
        0.0,  # Stake sizing not implemented yet
        gates_json
    ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
