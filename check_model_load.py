
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from model_service import StatsModel

print("Checking model...")
try:
    sm = StatsModel()
    if sm.model:
        print(f"Model loaded successfully: {type(sm.model)}")
        p_home, p_away = sm.predict({'net_rtg': 5.0, 'rest_days': 1}, {'net_rtg': -2.0, 'rest_days': 0})
        print(f"Prediction (Home +5 vs Away -2): Home={p_home:.3f}, Away={p_away:.3f}")
    else:
        print("Model object is None!")
except Exception as e:
    print(f"Error loading model: {e}")
