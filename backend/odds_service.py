import os
import requests
import random
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class OddsService:
    def __init__(self):
        self.api_key = os.getenv("ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

    def get_odds(self, home_team: str, away_team: str, date: str) -> Dict[str, str]:
        """
        Fetches odds for a specific game.
        Returns: {
            "home_odds": "-110",
            "away_odds": "-110",
            "spread": "-1.5",
            "total": "225.5",
            "source": "DraftKings"
        }
        """
        if self.api_key:
            return self._fetch_live_odds(home_team, away_team)
        else:
            print("[Error] No Odds API Key found. Returning empty odds.")
            return {}

    def _fetch_live_odds(self, home_team: str, away_team: str) -> Dict[str, str]:
        print(f"[Odds] Fetching LIVE odds for {away_team} @ {home_team}...")
        try:
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american"
            }
            resp = requests.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            # Simple fuzzy match (production would need strict mapping)
            for game in data:
                if home_team in game['home_team'] or away_team in game['away_team']:
                    # Extract first bookmaker (us)
                    book = game['bookmakers'][0]
                    
                    # Initialize default values
                    home_ml = "N/A"
                    spread = "N/A"
                    total = "N/A"
                    
                    for market in book['markets']:
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == game['home_team']:
                                    home_ml = str(outcome['price'])
                        elif market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                if outcome['name'] == game['home_team']:
                                    # Format: -2.5 (Home)
                                    spread = f"{outcome['point']} (Home)"
                        elif market['key'] == 'totals':
                             if market['outcomes']:
                                 total = str(market['outcomes'][0]['point'])

                    return {
                        "home_odds": home_ml,
                        "away_odds": "N/A", # Simplified for MVP
                        "spread": spread,
                        "total": total,
                        "source": book['title'],
                        "timestamp": book.get('last_update', None)
                    }
            
            print(f"[Warning] Game not found in live odds.")
            return {} 
        except Exception as e:
            print(f"[Error] Odds API Error: {e}")
            return {}


if __name__ == "__main__":
    odds = OddsService()
    # Test
    print(odds.get_odds("Los Angeles Lakers", "Golden State Warriors", "2025-12-25"))
