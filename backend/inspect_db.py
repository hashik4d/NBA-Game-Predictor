
import sqlite3
import pandas as pd

DB_NAME = "nba_predictor.db"

def inspect():
    try:
        conn = sqlite3.connect(DB_NAME)
        
        print(f"\n🔎 Inspecting {DB_NAME}...\n" + "="*40)
        
        # 1. Games
        print(f"\n🏀 GAMES (Last 5):")
        df_games = pd.read_sql_query("SELECT game_id, game_time_utc, home_team, away_team FROM games ORDER BY rowid DESC LIMIT 5", conn)
        if not df_games.empty:
            print(df_games.to_string(index=False))
        else:
            print("   [Empty]")

        # 2. Predictions
        print(f"\n🤖 PREDICTIONS (Last 5):")
        df_preds = pd.read_sql_query("SELECT game_id, timestamp_utc, predicted_winner, confidence_score FROM predictions ORDER BY id DESC LIMIT 5", conn)
        if not df_preds.empty:
            print(df_preds.to_string(index=False))
        else:
            print("   [Empty]")

        # 3. Odds Snapshots
        print(f"\n📊 ODDS SNAPSHOTS (Last 5):")
        df_odds = pd.read_sql_query("SELECT game_id, timestamp_utc, book, spread, total FROM odds_snapshots ORDER BY odds_id DESC LIMIT 5", conn)
        if not df_odds.empty:
            print(df_odds.to_string(index=False))
        else:
            print("   [Empty]")
            
        conn.close()
        print("\n" + "="*40 + "\n✅ Inspection Complete.")
        
    except Exception as e:
        print(f"Error inspecting DB: {e}")

if __name__ == "__main__":
    inspect()
