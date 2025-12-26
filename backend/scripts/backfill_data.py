
import sys
import os
import time
from datetime import datetime, timedelta
import sqlite3
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, init_db
from nba_api.stats.endpoints import scoreboardv2, leaguedashteamstats
from nba_api.stats.static import teams

SEASONS = [
    # Season ID, Start Date, End Date (approx, or fetch until today)
    ("2024-25", "2024-10-22"),
    ("2023-24", "2023-10-24"),
    ("2022-23", "2022-10-18"),
    ("2021-22", "2021-10-19"),
    ("2020-21", "2020-12-22"),
    ("2019-20", "2019-10-22"),
    ("2018-19", "2018-10-16"),
    ("2017-18", "2017-10-17"),
    ("2016-17", "2016-10-25"),
    ("2015-16", "2015-10-27")
]

def backfill_season_data():
    """
    Fetches completed games for the defined 10 seasons.
    Populates: games, results, team_features
    """
    print(f"Starting 10-Season Backfill...")
    init_db()
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Get all teams
    nba_teams = teams.get_teams()
    team_map = {t['id']: t['full_name'] for t in nba_teams}

    for season_id, start_date_str in SEASONS:
        print(f"=== Processing Season {season_id} ===")
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        # End date is either today (for current season) or roughly June 30th of the next year
        # Actually logic: Fetch until "Next Season Start" or Today.
        # Simple Logic: Iterate 200 days (Regular season is ~170 days)
        # We stop if no games for > 15 days in a row maybe? 
        # Or just hardcode end dates?
        # Let's run for 180 days from start date.
        
        end_date = start_date + timedelta(days=180)
        cutoff = datetime.now() - timedelta(days=1)
        if end_date > cutoff:
            end_date = cutoff

        current_date = start_date
        
        consecutive_empty_days = 0
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Check if we already have games/features for this day to skip?
            # It's faster to check DB than API.
            # However, partial days might be an issue.
            # Let's perform a CHECK FIRST.
            c.execute("SELECT COUNT(*) FROM games WHERE game_time_utc = ?", (date_str,))
            count = c.fetchone()[0]
            
            # Heuristic: If we have > 2 games for this date, assume it's done. 
            # (Sometimes days have 1-2 games, but rarely 0 in season unless break)
            # Re-running is safer but slower. 
            # Given user wants 10 years, optimized skipping is vital.
            if count > 2:
                 # Check if features exist
                 c.execute("SELECT COUNT(*) FROM team_features WHERE timestamp_utc = ?", (date_str,))
                 f_count = c.fetchone()[0]
                 if f_count >= count:
                     print(f"Skipping {date_str} (Already in DB)")
                     current_date += timedelta(days=1)
                     continue

            print(f"Processing {date_str}...")
            
            try:
                # Fetch Scoreboard
                sb = scoreboardv2.ScoreboardV2(game_date=date_str)
                games_dict = sb.get_dict()
                result_sets = games_dict['resultSets'][0]
                rows = result_sets['rowSet']
                
                if not rows:
                    consecutive_empty_days += 1
                    if consecutive_empty_days > 10:
                        print("10 empty days, skipping rest of season.")
                        break
                else:
                    consecutive_empty_days = 0
                
                # ... [Logic from previous script with tweaks] ...
                
                # Fetch Advanced Stats for "Yesterday" (Entering Stats)
                prev_day = (current_date - timedelta(days=1)).strftime("%m/%d/%Y")
                
                # Only make this expensive call if we have games
                daily_stats = {}
                if rows:
                    stats = leaguedashteamstats.LeagueDashTeamStats(
                        season=season_id,
                        last_n_games=0, 
                        measure_type_detailed_defense="Advanced",
                        date_from_nullable="",
                        date_to_nullable=prev_day
                    )
                    stats_dict = stats.get_dict()['resultSets'][0]
                    s_headers = stats_dict['headers']
                    for r in stats_dict['rowSet']:
                        d = dict(zip(s_headers, r))
                        daily_stats[d['TEAM_ID']] = d

                # Process Games
                main_headers = result_sets['headers']
                
                # Get Line Scores for Points
                line_score_set = games_dict['resultSets'][1]
                ls_headers = line_score_set['headers']
                ls_rows = line_score_set['rowSet']
                
                def get_pts(tid):
                    for ls_row in ls_rows:
                        # Indexing by name is safer, zip every time is slow but safe
                        d = dict(zip(ls_headers, ls_row))
                        if d['TEAM_ID'] == tid:
                            return d['PTS']
                    return 0

                for row in rows:
                    game_data = dict(zip(main_headers, row))
                    if "Final" not in game_data['GAME_STATUS_TEXT']:
                        continue

                    g_id = game_data['GAME_ID']
                    h_id = game_data['HOME_TEAM_ID']
                    a_id = game_data['VISITOR_TEAM_ID']
                    
                    # 1. Games Table
                    c.execute('''
                        INSERT OR IGNORE INTO games (game_id, season, game_time_utc, home_team, away_team, venue)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        g_id, season_id, date_str, 
                        team_map.get(h_id, "Unknown"), 
                        team_map.get(a_id, "Unknown"), 
                        "NBA Arena"
                    ))
                    
                    # 2. Results Table
                    h_pts = get_pts(h_id)
                    a_pts = get_pts(a_id)
                    winner = "Home" if h_pts > a_pts else "Away"
                    
                    c.execute('''
                        INSERT OR REPLACE INTO results (game_id, final_home_score, final_away_score, winner)
                        VALUES (?, ?, ?, ?)
                    ''', (g_id, h_pts, a_pts, winner))
                    
                    # 3. Features
                    # Check if exists to avoid dupes
                    c.execute("SELECT 1 FROM team_features WHERE game_id=?", (g_id,))
                    if c.fetchone():
                        continue
                        
                    if h_id in daily_stats and a_id in daily_stats:
                        h_s = daily_stats[h_id]
                        a_s = daily_stats[a_id]
                        
                        c.execute('''
                            INSERT INTO team_features (
                                game_id, timestamp_utc,
                                home_ortg, home_drtg, home_pace, home_net_rtg,
                                away_ortg, away_drtg, away_pace, away_net_rtg,
                                home_rest_days, away_rest_days
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            g_id, date_str,
                            h_s.get('OFF_RATING'), h_s.get('DEF_RATING'), h_s.get('PACE'), h_s.get('NET_RATING'),
                            a_s.get('OFF_RATING'), a_s.get('DEF_RATING'), a_s.get('PACE'), a_s.get('NET_RATING'),
                            0, 0
                        ))

                conn.commit()
                # print(f" > Processed.")

            except Exception as e:
                print(f"Error on {date_str}: {e}")
                # Don't break, just continue
            
            current_date += timedelta(days=1)
            # Sleep to prevent rate limit ban (600 req/10min is generous but persistent scraping is flagged)
            # We are doing 2 calls per day.
            # 0.6s sleep = ~1.2s per day.
            time.sleep(0.5)

    conn.close()
    print("10-Season Backfill Complete.")

if __name__ == "__main__":
    backfill_season_data()
