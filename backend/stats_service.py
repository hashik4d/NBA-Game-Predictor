from nba_api.stats.endpoints import leaguedashteamstats
from typing import Dict, Any, List
import pandas as pd
import time

class StatsService:
    def get_team_metrics(self, team_id: str, is_home: bool) -> Dict[str, Any]:
        """
        Fetches unified metrics including Splits (Home/Away) and Last 5.
        """
        # 1. Overall Advanced
        base = self._fetch_stats_segment(measure_type='Advanced')
        team_base = base.get(team_id, {})
        
        # 2. Last 5 Games
        l5 = self._fetch_stats_segment(measure_type='Advanced', last_n=5)
        team_l5 = l5.get(team_id, {})
        
        # 3. Location Split
        loc_mode = 'Home' if is_home else 'Road'
        loc = self._fetch_stats_segment(measure_type='Advanced', location=loc_mode)
        team_loc = loc.get(team_id, {})
        
        return {
            "ORtg": team_base.get('off_rtg', "N/A"),
            "DRtg": team_base.get('def_rtg', "N/A"),
            "Pace": team_base.get('pace', "N/A"),
            "NetRtg": team_base.get('net_rtg', "N/A"),
            "Last5": {
                "W_PCT": team_l5.get('w_pct', "N/A"),
                "NetRtg": team_l5.get('net_rtg', "N/A")
            },
            "Split": {
                "Location": loc_mode,
                "W_PCT": team_loc.get('w_pct', "N/A"),
                "NetRtg": team_loc.get('net_rtg', "N/A")
            }
        }

    def _fetch_stats_segment(self, measure_type='Advanced', last_n=0, location=None) -> Dict:
        """Helper to fetch specific cuts of data."""
        try:
            params = {'measure_type_detailed_defense': measure_type}
            if last_n > 0:
                params['last_n_games'] = last_n
            # if location:
            #     params['location'] = location
                
            stats = leaguedashteamstats.LeagueDashTeamStats(**params)
            df = stats.get_data_frames()[0]
            
            data = {}
            for _, row in df.iterrows():
                tid = str(row['TEAM_ID'])
                # Helper to clean NaN
                def clean(val):
                    import math
                    if val is None: return 0.0
                    try:
                        return 0.0 if math.isnan(float(val)) else float(val)
                    except:
                        return 0.0

                data[tid] = {
                    "team_name": row['TEAM_NAME'],
                    "w_pct": clean(row['W_PCT']),
                    "off_rtg": clean(row['OFF_RATING']),
                    "def_rtg": clean(row['DEF_RATING']),
                    "net_rtg": clean(row['NET_RATING']),
                    "pace": clean(row['PACE'])
                }
            return data
        except Exception as e:
            print(f"Stats Error ({last_n}, {location}): {e}")
            return {}

    @staticmethod
    def get_advanced_team_stats() -> Dict[str, Dict[str, Any]]:
        # Legacy Wrapper for compatibility if needed, else remove
        svc = StatsService()
        return svc._fetch_stats_segment()

    def get_schedule_context(self, team_id: str, date_str: str) -> Dict[str, Any]:
        """
        Calculates Rest Days, B2B, and 3-in-4 using TeamGameLog.
        """
        try:
            from nba_api.stats.endpoints import teamgamelog
            from datetime import datetime
            
            # Fetch full season log
            log = teamgamelog.TeamGameLog(team_id=team_id, season='2024-25')
            games = log.get_data_frames()[0]
            
            # Convert GAME_DATE strings to datetime objects for comparison
            # NBA API typical format: "DEC 25, 2024" or "2024-12-25"
            # We use mixed format handling to be safe, but specify 'mixed' to silence warning
            games['parsed_date'] = pd.to_datetime(games['GAME_DATE'], format='mixed')
            target = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Filter for games BEFORE target date
            past_games = games[games['parsed_date'] < target].sort_values('parsed_date', ascending=False)
            
            if past_games.empty:
                return {"rest_days": 3, "is_b2b": False, "3_in_4": False} # Default start season
            
            last_game_date = past_games.iloc[0]['parsed_date']
            delta = (target - last_game_date).days
            rest_days = max(0, delta - 1)
            
            # Check 3-in-4: Games on (Target-1, Target-2, Target-3)
            # We need to see how many games occurred in the [Target-3, Target-1] window
            # Window days: T-1, T-2, T-3
            window_start = target - pd.Timedelta(days=3)
            recent_games = past_games[past_games['parsed_date'] >= window_start]
            is_3_in_4 = len(recent_games) >= 2 # If 2 games in last 3 days + today's game = 3 in 4
            
            return {
                "rest_days": int(rest_days),
                "is_b2b": rest_days == 0,
                "3_in_4": bool(is_3_in_4)
            }
            
        except Exception as e:
            print(f"[Warning] Schedule calc failed: {e}")
            return {"rest_days": 1, "is_b2b": False, "3_in_4": False} # Fallback

if __name__ == "__main__":
    # Test
    stats = StatsService()
    # Test Warriors (1610612744) for Xmas 2025
    print("Schedule Ctx:", stats.get_schedule_context("1610612744", "2025-12-25"))
