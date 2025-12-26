# 🏀 NBA Game Predictor: The Developer's Handbook

Welcome to your first deep dive into software engineering! This guide assumes you know **nothing** about coding and explains how a real-world "Full Stack" application works.

This project has two main parts:
1.  **The Backend** (Python): The brain that thinks and gets data.
2.  **The Frontend** (React/Next.js): The face that you touch and click.

---

## 1. The Backend (Where the logic lives)
*Location: [`backend/`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend)*

The backend is a server. It sits waiting for orders (requests) and sends back answers (responses).

### 🧠 The Head Chef: [`main.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/main.py)
This is the entry point. When you start the Python server, this file runs first.

**What it does:**
-   **Lines 1-5**: Imports tools. `FastAPI` is the framework that makes building API servers easy.
-   **Line 7**: `app = FastAPI(...)` creates the app.
-   **Lines 22-24**: This is an "endpoint". It's like a door. When someone knocks on the `/predict` door, this function runs:
    ```python
    @app.get("/predict")
    async def predict(home: str, away: str, date: str):
        # It asks the AI service to predict the winner
        return await ai_service.predict_winner(home, away, date)
    ```

### 🤖 The Brains: [`ai_service.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/ai_service.py)
This is where the Intelligence lives. It handles the "Multi-AI" logic.

**How it works (Simplified):**
1.  **`__init__`**: When the service starts, it logs in to Google (Gemini), Anthropic (Claude), OpenAI, and Perplexity using your keys.
2.  **`predict_winner`**: The main function.
    -   First, it asks **Perplexity** to find today's news (Injuries, etc.).
    -   Then, it sends that news to **Gemini**, **Claude**, and **OpenAI** simultaneously (in parallel).
    -   It counts the votes (e.g., 3 votes for Lakers, 1 for Warriors).
    -   It returns the winner and the explanation.

### 🏀 The Supplier: [`nba_service.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/nba_service.py)
This file talks to the official NBA database.

**Key Logic:**
-   **`get_games_for_date`**: It looks for games today. If there are no games (like on holidays), it automatically checks tomorrow and the day after until it finds real basketball games to show you.

---

## 2. The Frontend (What the user sees)
*Location: [`frontend/`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/frontend)*

The frontend is built with **Next.js** (a framework for React). It builds the HTML you see in Chrome.

### 🏠 The Homepage: [`app/page.tsx`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/frontend/app/page.tsx)
This is the first page you see.

**What it does:**
-   **`useEffect` (Line 11)**: This is a "Hook". It runs automatically when the page loads.
-   **`fetch('http://localhost:8000/games')`**: It calls your Backend to get the list of games.
-   **`games.map(...)` (Line 44)**: This is a loop. For every game in the list, it creates a `<GameCard />`.

### 🃏 The Game Card: [`components/GameCard.tsx`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/frontend/components/GameCard.tsx)
This represents *one* single game box (e.g., just the Lakers vs Warriors box).

**Key Logic:**
-   **`onClick={getPrediction}` (Line 50)**: When you click the button, it runs the `getPrediction` function.
-   **`fetch(...)` (Line 12)**: It calls the Backend's `/predict` endpoint:
    `http://localhost:8000/predict?home=Lakers&away=Warriors...`
-   **Line 58 (`{prediction && ...}`)**: This is conditional rendering. It means *"If we have a prediction, show the result. If not, show the button."*

---

## 🎓 Summary of the Flow

1.  **Browser** loads [`page.tsx`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/frontend/app/page.tsx).
2.  **Page** asks [`nba_service.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/nba_service.py) for the schedule.
3.  **User** clicks a [`GameCard.tsx`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/frontend/components/GameCard.tsx).
4.  **Card** knocks on [`main.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/main.py)'s door (`/predict`).
5.  **Main** wakes up [`ai_service.py`](file:///c:/Users/hashi/OneDrive/Desktop/Antigravity/nba-predictor/backend/ai_service.py).
6.  **AI Service** gathers votes from 4 robots and sends the answer back!

## 🚀 How to Run It (The Easy Way)
I made a **Magic Button** script for you. It opens everything at once.

1.  Open any terminal in the `nba-predictor` folder.
2.  Run this single command:
    ```bash
    python run_app.py
    ```

**What will happen?**
1.  It starts the Backend (Kitchen).
2.  It starts the Frontend (Dining Room).
3.  It waits 10 seconds.
4.  **It automatically opens Chrome** to your website! 🎉

---

## 🧪 Micro-Experiments: Can I run just ONE file?

**YES!** This is a great way to learn. You don't always need the whole restaurant open to taste the soup.

### Experiment 1: Talk to the NBA Database
Want to see the raw data coming from the NBA? Run the Supplier file directly.
1.  Open your backend terminal.
2.  Run: `python nba_service.py`
    -   *You will see a big JSON list of games printed right in your terminal.*

### Experiment 2: Talk to the AI Brain
Want to test the consensus engine without the website? I added a special "Test Mode" to the AI service.
1.  Open your backend terminal.
2.  Run: `python ai_service.py`
    -   *You will see the "4-AI Council" predict a Lakers vs. Warriors game right there in the black box!*

---

**Happy Coding!** 🚀
