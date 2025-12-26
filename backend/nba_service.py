from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import json
from stats_service import StatsService
from odds_service import OddsService
from injury_service import InjuryService
from model_service import StatsModel

class NBAService:
    def __init__(self):
        self.stats_svc = StatsService()
        self.odds_svc = OddsService()
        self.inj_svc = InjuryService()
        self.stats_model = StatsModel()
        self.team_stats_cache = {}

    def get_game_context(self, home_team: str, away_team: str, date_str: str, season_ctx: dict = None) -> dict:
        """
        Builds the strict 'Fact Pack' JSON payload.
        """
        # 1. Fetch Stats if empty
        if not self.team_stats_cache:
             # Basic cache warmup
             self.team_stats_cache = self.stats_svc.get_advanced_team_stats()
             
        # Find team IDs
        h_base = self._find_stats(home_team)
        a_base = self._find_stats(away_team)
        h_id = self._get_team_id(home_team)
        a_id = self._get_team_id(away_team)
        
        # 2. Get Detailed Metrics (Splits/L5)
        # Note: In prod, catch exceptions if IDs not found
        h_metrics = self.stats_svc.get_team_metrics(h_id, is_home=True)
        a_metrics = self.stats_svc.get_team_metrics(a_id, is_home=False)
        
        # 3. Get Odds (Timestamp included)
        odds = self.odds_svc.get_odds(home_team, away_team, date_str)
        
        # 5. Get Schedule Context (Real Data)
        h_schedule = self.stats_svc.get_schedule_context(h_id, date_str)
        a_schedule = self.stats_svc.get_schedule_context(a_id, date_str)

        # 6. Get Injuries (Detailed) - Restored
        h_injuries = self.inj_svc.get_injury_report(home_team)
        a_injuries = self.inj_svc.get_injury_report(away_team)

        # 7. Math Model Prediction
        h_model_input = {**h_metrics, "rest_days": h_schedule.get("rest_days", 0)}
        a_model_input = {**a_metrics, "rest_days": a_schedule.get("rest_days", 0)}
        
        p_home, p_away = self.stats_model.predict(h_model_input, a_model_input)
        
        # Calculate Edge
        ml_home = odds.get('home_odds', "N/A")
        def get_implied(american):
            try:
                if str(american) == "N/A": return 0.5
                v = float(american)
                if v < 0: return (-v) / (-v + 100)
                return 100 / (v + 100)
            except: return 0.5
            
        implied_home = get_implied(ml_home)
        edge = p_home - implied_home
        
        math_block = {
            "p_home": round(p_home, 3),
            "p_away": round(p_away, 3),
            "implied_home": round(implied_home, 3),
            "edge_home": round(edge, 3)
        }
            
        return {
            "game_id": f"{date_str}-{away_team}-{home_team}", # Generated ID
            "time": season_ctx.get("time", "TBD") if season_ctx else "TBD",
            "teams": {"home": home_team, "away": away_team},
            "venue": season_ctx.get("venue", f"Home of {home_team}") if season_ctx else f"Home of {home_team}",
            
            "odds": odds,
            
            "team_metrics": {
                "home": h_metrics,
                "away": a_metrics
            },
            
            "rest_travel": {
                "home": h_schedule,
                "away": a_schedule
            },
            
            "injuries": {
                "home": h_injuries,
                "away": a_injuries
            },
            
            "math_model": math_block
        }

    def _get_team_id(self, team_name):
        for tid, data in self.team_stats_cache.items():
            if team_name in data.get('team_name', ''):
                return tid
        return "0" # Not found

    def _find_stats(self, team_name):
        # Naive fuzzy match for MVP
        for tid, data in self.team_stats_cache.items():
            if team_name in data['team_name'] or data['team_name'] in team_name:
                return data
        return {"net_rtg": "N/A", "pace": "N/A", "w_pct": "N/A"}

    @staticmethod
    def get_games_for_date(date_str=None):
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Add basic headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.nba.com/'
        }
        
        try:
            # If no games for today, try tomorrow (NBA usually has no games on Dec 24)
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            for _ in range(3): # Try up to 3 days ahead
                formatted_date = current_date.strftime('%Y-%m-%d')
                sb = scoreboardv2.ScoreboardV2(game_date=formatted_date)
                games_data = sb.get_dict()
                
                rows = games_data['resultSets'][0]['rowSet']
                if rows:
                    # Found games!
                    main_headers = games_data['resultSets'][0]['headers']
                    
                    # More robust team names from static list
                    from nba_api.stats.static import teams
                    nba_teams = teams.get_teams()
                    team_map = {str(t['id']): t['full_name'] for t in nba_teams}
                    
                    games = []
                    for row in rows:
                        game_header = dict(zip(main_headers, row))
                        h_id = str(game_header.get('HOME_TEAM_ID'))
                        v_id = str(game_header.get('VISITOR_TEAM_ID'))
                        
                        games.append({
                            "gameId": game_header["GAME_ID"],
                            "homeTeamName": team_map.get(h_id, f"Home ({h_id})"),
                            "awayTeamName": team_map.get(v_id, f"Away ({v_id})"),
                            "homeTeamId": h_id,
                            "awayTeamId": v_id,
                            "gameTimeET": game_header["GAME_STATUS_TEXT"]
                        })
                    return games, formatted_date
                
                current_date += timedelta(days=1)
                
            return [], date_str
        except Exception as e:
            print(f"Error fetching games: {e}")
            return [], date_str

if __name__ == "__main__":
    # Test
    games = NBAService.get_games_for_date()
    print(json.dumps(games, indent=2))
