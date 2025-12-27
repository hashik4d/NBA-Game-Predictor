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

## 📚 Documentation

### 🚀 For Developers & Contributors

**New to the project?** Start here:
- **[ROADMAP.md](ROADMAP.md)** - 🗺️ Visual implementation journey with 3 paths to choose from
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - ⚡ Copy-paste ready fixes and quick wins
- **[PROJECT_GUIDE.md](PROJECT_GUIDE.md)** - 🎓 Beginner-friendly explanation of how everything works

**Ready to implement improvements?**
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 📋 Comprehensive 10-phase plan with code examples
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 💡 At-a-glance guide with commands and examples

**Want to understand the codebase?**
- **[CODE_ANALYSIS.md](CODE_ANALYSIS.md)** - 🔍 Deep analysis of strengths and areas for improvement
- **[CRITICAL_FIXES.md](CRITICAL_FIXES.md)** - ✅ What's already been fixed
- **[SUMMARY.md](SUMMARY.md)** - 📊 Quick assessment and recommendations

### 📊 Current Status

**Overall Rating:** 6.5/10 - Working MVP, needs hardening for production

**What's Working:** ✅ Multi-AI consensus, Real-time data, Full-stack app, Database persistence  
**What Needs Work:** ⚠️ Security, Testing, Error handling, Logging, Performance optimization

**Production Ready Timeline:**
- 3 weeks → Minimum Viable Production (7.5/10)
- 5 weeks → Solid Production Ready (8.5/10) ← Recommended
- 6+ weeks → Best-in-Class System (9.0/10)

**Next Steps:** Start with [ROADMAP.md](ROADMAP.md) to choose your path!

## 📄 License
MIT
