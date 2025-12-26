import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

key = os.getenv("CLAUDE_API_KEY")
client = Anthropic(api_key=key)

# Mock Fact Pack (similar to real one)
context = {
    "teams": {"home": "Golden State Warriors", "away": "Los Angeles Lakers"},
    "odds": {"spread": "-5.5", "total": "230.5", "home_odds": "-150", "timestamp": "2024-12-25T12:00:00"},
    "team_metrics": {
        "home": {"NetRtg": 5.5, "Pace": 99.0, "Last5": {"NetRtg": 2.0}, "Split": {"NetRtg": 6.0}},
        "away": {"NetRtg": -1.5, "Pace": 101.0, "Last5": {"NetRtg": -3.0}, "Split": {"NetRtg": -4.0}}
    },
    "rest_travel": {"home": "Standard", "away": "B2B"},
    "injuries": {"home": [], "away": []}
}

prompt = f"""
Analyze Game: {context['teams']['away']} @ {context['teams']['home']}.
Review the JSON Fact Pack below, focusing on DEFENSE (DRtg), INJURIES (Importance Score), and SCHEDULE (Rest).

FACT PACK JSON:
{json.dumps(context, indent=2)}

Return JSON excluding markdown: {{'winner': 'Team', 'confidence': 80, 'reason': 'Reason based on Defensive metrics or Injury Impact'}}."
"""

print("[Test] Sending Full Request to Claude...")
try:
    resp = client.messages.create(
        model="claude-3-haiku-20240307", 
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"[Success] Response: {resp.content[0].text[:100]}...")
except Exception as e:
    print(f"[Error] Failed: {e}")
