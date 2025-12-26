
import sqlite3
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_PATH = "nba_model_v1.pkl"
DB_NAME = "nba_predictor.db"

class StatsModel:
    def __init__(self):
        self.model = None
        self.load_model()
        
    def get_db_connection(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def train(self):
        """
        Fetches data from DB, trains LR model, saves to pickle.
        """
        print("Training StatsModel...")
        conn = self.get_db_connection()
        
        # 1. Fetch Dataset
        query = """
            SELECT 
                t.game_id,
                t.home_net_rtg, t.away_net_rtg,
                t.home_pace, t.away_pace,
                t.home_rest_days, t.away_rest_days,
                r.winner
            FROM team_features t
            JOIN results r ON t.game_id = r.game_id
            WHERE r.winner IS NOT NULL
        """
        try:
            df = pd.read_sql(query, conn)
        except Exception as e:
            print(f"Error reading training data: {e}")
            return
        finally:
            conn.close()

        if df.empty:
            print("No training data found.")
            return

        # 2. Feature Engineering
        # Target: Home Win = 1, Away Win = 0
        df['target'] = df['winner'].apply(lambda x: 1 if x == 'Home' else 0)
        
        # Features: Diff = Home - Away
        df['net_rating_diff'] = df['home_net_rtg'] - df['away_net_rtg']
        df['pace_diff'] = df['home_pace'] - df['away_pace'] # Maybe less predictive but relevant
        df['rest_diff'] = df['home_rest_days'] - df['away_rest_days']
        
        # Select Features
        features = ['net_rating_diff', 'rest_diff'] 
        # Keeping it simple for V1. Pace diff usually just means fast vs slow game, logic says net rating is king.
        
        X = df[features]
        y = df['target']
        
        # 3. Train
        # No complex split for this demo, just fit entries.
        # Ideally use TimeSeriesSplit, but random for now is okay for V1 MVP
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = LogisticRegression(class_weight='balanced')
        self.model.fit(X_train, y_train)
        
        train_acc = self.model.score(X_train, y_train)
        test_acc = self.model.score(X_test, y_test)
        
        print(f"Model Trained. Train Acc: {train_acc:.3f}, Test Acc: {test_acc:.3f}")
        
        # 4. Save
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
            
    def load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            return True
        return False

    def predict(self, home_stats, away_stats):
        """
        Returns (prob_home_win, prob_away_win)
        Stats dicts must strictly match DB column expectations or be pre-processed.
        
        Expected keys in input:
        - net_rtg
        - rest_days
        """
        if not self.model:
            print("Model not loaded.")
            return 0.5, 0.5
            
        # Calc Diffs
        h_net = float(home_stats.get('net_rtg', 0))
        a_net = float(away_stats.get('net_rtg', 0))
        h_rest = float(home_stats.get('rest_days', 0))
        a_rest = float(away_stats.get('rest_days', 0))
        
        net_diff = h_net - a_net
        rest_diff = h_rest - a_rest
        
        # Feature vector must match training columns: ['net_rating_diff', 'rest_diff']
        # Use DataFrame to match feature names and avoid warnings
        X_pred = pd.DataFrame(
            [[net_diff, rest_diff]], 
            columns=['net_rating_diff', 'rest_diff']
        )
        
        probs = self.model.predict_proba(X_pred)[0] # [prob_0, prob_1]
        p_away = probs[0]
        p_home = probs[1]
        
        return p_home, p_away

if __name__ == "__main__":
    # Test Run
    sm = StatsModel()
    sm.train()
