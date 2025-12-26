# 🏀 NBA Game Predictor (The Council)

**An AI-powered sports betting assistant that combines statistical rigor with LLM reasoning.**

The "Council" is an ensemble of 3 AI Agents (Claude, Gemini, OpenAI) + 1 Logistic Regression Model that debate every game to find the edge against Vegas.

## 🚀 Features

### 1. The Math Model (The Edge)
- **Engine**: Logistic Regression (Scikit-Learn).
- **Features**: Net Rating Differential, Rest Days, Pace.
- **Output**: Calculates "True Win Probability" and compares it to Implied Odds to find a **Green Edge (>3%)**.

### 2. The AI Council (Context)
- **Role**: Qualitative Analysis.
- **Inputs**: Injuries, "Vibes" (Last 5 Games), Motivation, Home/Away Splits.
- **Mechanism**: 3 separate LLM calls (Gemini 2.0, Claude 3.5, GPT-4o) vote on the winner.

### 3. The Gate System (Decision Engine)
Automated "Bet/No-Bet" logic based on 3 strict gates:
- **Gate 1 (Math)**: Is there a positive edge?
- **Gate 2 (Consensus)**: Do the AIs agree?
- **Gate 3 (Confidence)**: Is the combined confidence > 60%?
- **Result**: Displays a **"SYSTEM PICK"** ticket (BET MAX, BET SMALL, or PASS).

## 🛠️ Tech Stack
- **Frontend**: Next.js 14 (React, TypeScript), Tailwind-style CSS.
- **Backend**: Python (FastAPI), SQLite.
- **AI**: Google Gemini, Anthropic Claude, OpenAI.
- **Data**: NBA API (stats), ESPN (injuries).

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys (Gemini, Claude, or OpenAI)

### 1. Install & Run
We have a unified launcher script!

```bash
# Clone the repo
git clone https://github.com/hashik4d/NBA-Game-Predictor.git
cd NBA-Game-Predictor

# Install Backend Deps
pip install -r backend/requirements.txt

# Install Frontend Deps
cd frontend
npm install
cd ..

# Run the App (Starts both servers)
python run_app.py
```

### 2. Backfill Data (Optional)
To retrain the math model with more history:
```bash
python backend/scripts/backfill_data.py
python backend/model_service.py
```

## 📸 Screenshots
*(Add screenshots of the Game Card and Decision Ticket here)*

## 📄 License
MIT
