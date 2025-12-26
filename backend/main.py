from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from nba_service import NBAService
from ai_service import ai_service
import json

app = FastAPI(title="NBA Game Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/games")
async def get_games(date: str = Query(None)):
    games, actual_date = NBAService.get_games_for_date(date)
    return {"games": games, "date": actual_date}

@app.get("/predict")
async def predict(home: str, away: str, date: str):
    # 1. Fetch Schedule to get Time/Venue (Real Data)
    games, _ = NBAService.get_games_for_date(date)
    season_ctx = {}
    
    # Locate our game in the schedule
    for g in games:
        # Fuzzy match or exact match on names
        if (home in g['homeTeamName'] or home in g['awayTeamName']) and \
           (away in g['homeTeamName'] or away in g['awayTeamName']):
            season_ctx = {
                "time": g['gameTimeET'],
                "venue": "Home Arena" # NBA API doesn't always give venue in scoreboard, fallback safe
            }
            break

    # 2. Build "Fact Pack" (Stats + Odds + Injuries)
    print(f"🧠 Building Context for {away} @ {home}...")
    nba = NBAService() # Instantiate service (or make singleton globally)
    context = nba.get_game_context(home, away, date, season_ctx)
    
    # [PERSISTENCE] Save Game & Odds Snapshot
    import database
    try:
        database.save_game_context(
            game_id=context['game_id'],
            season="2024-25",
            time_utc=season_ctx.get("time", "TBD"),
            home=home,
            away=away,
            venue=season_ctx.get("venue", "Unknown Venue")
        )
        # Save Odds
        if context.get('odds'):
            database.save_odds_snapshot(context['game_id'], context['odds'])
            
        # Save Team Features (Stats)
        database.save_team_features(context['game_id'], context)
        
        # Save Injuries
        if context.get('injuries'):
            database.save_injury_reports(context['game_id'], context['injuries'])
            
    except Exception as e:
        print(f"[Warning] Failed to save game/odds/context to DB: {e}")

    # 3. Get AI Consensus
    result = await ai_service.predict_winner(context)
    
    # [PERSISTENCE] Save Prediction
    try:
        database.save_prediction(context['game_id'], result)
        
        # [PERSISTENCE] Save Decision (Gate Check)
        if result.get('decision'):
            database.save_decision(context['game_id'], result['decision'])
            
    except Exception as e:
        print(f"[Warning] Failed to save prediction/decision to DB: {e}")

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
