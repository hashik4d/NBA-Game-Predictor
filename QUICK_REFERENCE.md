# 🎯 NBA Game Predictor - Quick Reference Guide

> **TL;DR:** Your codebase is functional but needs hardening. Follow this guide to make it production-ready.

---

## 📊 Current Status vs. Target

| Category | Current | Target | Priority |
|----------|---------|--------|----------|
| **Functionality** | ✅ 8/10 Working | ✅ 9/10 | - |
| **Security** | ⚠️ 4/10 Basic | ✅ 9/10 | **P1** |
| **Testing** | ❌ 2/10 Manual | ✅ 8/10 | **P1** |
| **Error Handling** | ❌ 3/10 Bare excepts | ✅ 9/10 | **P1** |
| **Logging** | ❌ 3/10 Print statements | ✅ 8/10 | **P1** |
| **Performance** | ⚠️ 5/10 Slow | ✅ 8/10 | **P2** |
| **Documentation** | ✅ 7/10 Good | ✅ 9/10 | **P3** |

**Overall: 6.5/10 → Target: 9/10**

---

## 🚦 3-Week Minimum Viable Production (MVP) Plan

### Week 1: Foundation & Security
```bash
✅ Critical fixes (DONE)
📝 Replace print() → logging
🔧 Create config.py
🛡️ Add input validation (Pydantic)
🔒 Restrict CORS
⏱️ Add rate limiting
```

### Week 2: Reliability & Error Handling
```bash
🔄 Replace bare except blocks
♻️ Add retry logic (tenacity)
⏰ Add timeouts to all API calls
🧪 Set up pytest framework
✅ Write unit tests for core logic
```

### Week 3: Testing & Optimization
```bash
🧪 Integration tests
🧪 Mock tests for external APIs
⚡ Implement caching
📊 Add database indexes
🏥 Health check endpoint
```

---

## 🎯 Priority Matrix

### P0 - Critical (COMPLETED ✅)
- ✅ Fix missing type imports
- ✅ Implement save_decision()
- ✅ Clean requirements.txt
- ✅ Add missing json import

### P1 - High Priority (Week 1-3)
**Security:**
- [ ] Input validation on all endpoints
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Request timeouts

**Reliability:**
- [ ] Replace bare exception blocks
- [ ] Add retry logic
- [ ] Proper logging (not print)
- [ ] Error tracking

**Testing:**
- [ ] Setup pytest
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] Mock external services

### P2 - Medium Priority (Week 4-5)
- [ ] Implement caching
- [ ] Database indexes
- [ ] Health checks
- [ ] Metrics collection
- [ ] Structured logging

### P3 - Low Priority (Week 6+)
- [ ] ML model improvements
- [ ] Model versioning
- [ ] CI/CD pipeline
- [ ] Advanced documentation

---

## 🔧 Quick Fixes (Copy & Paste Ready)

### 1. Replace Print with Logging
```python
# ❌ Before
print(f"[Success] API initialized")
print(f"[Error] Failed: {e}")

# ✅ After
import logging
logger = logging.getLogger(__name__)

logger.info("API initialized")
logger.error("Failed", exc_info=True, extra={"error": str(e)})
```

### 2. Add Input Validation
```python
# ❌ Before
@app.get("/predict")
async def predict(home: str, away: str, date: str):
    return await ai_service.predict_winner(home, away, date)

# ✅ After
from pydantic import BaseModel, Field, validator

class PredictRequest(BaseModel):
    home: str = Field(..., min_length=2, max_length=50)
    away: str = Field(..., min_length=2, max_length=50)
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    
    @validator('home', 'away')
    def validate_team(cls, v):
        if not v.replace(' ', '').replace('-', '').isalnum():
            raise ValueError('Invalid team name')
        return v.strip()

@app.post("/predict")
async def predict(request: PredictRequest):
    return await ai_service.predict_winner(
        request.home, request.away, request.date
    )
```

### 3. Fix Exception Handling
```python
# ❌ Before (Dangerous!)
try:
    result = api_call()
except Exception as e:
    print(f"Error: {e}")
    return None

# ✅ After (Safe!)
from requests.exceptions import RequestException, Timeout
import logging

logger = logging.getLogger(__name__)

try:
    result = api_call()
except (RequestException, Timeout, ValueError) as e:
    logger.error("API call failed", exc_info=True, extra={"error": str(e)})
    return None
except Exception as e:
    logger.critical("Unexpected error", exc_info=True)
    raise  # Don't swallow unknown errors!
```

### 4. Add Rate Limiting
```python
# Install: pip install slowapi

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, data: PredictRequest):
    return await ai_service.predict_winner(data.home, data.away, data.date)
```

### 5. Add Retry Logic
```python
# Install: pip install tenacity

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_with_retry(url: str) -> dict:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

### 6. Create Config File
```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    claude_api_key: str
    openai_api_key: str
    
    # Security
    cors_origins: list[str] = ["http://localhost:3000"]
    rate_limit_per_minute: int = 10
    
    # Database
    database_url: str = "sqlite:///nba_predictor.db"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Use everywhere:
from backend.config import settings
print(settings.gemini_api_key)
```

---

## 📝 File-by-File Changes

### Backend Files to Modify

| File | Changes Needed | Priority |
|------|----------------|----------|
| `main.py` | Add validation, rate limiting, health check | P1 |
| `ai_service.py` | Fix exceptions, add logging, timeouts | P1 |
| `nba_service.py` | Fix exceptions, add caching, logging | P1 |
| `stats_service.py` | Fix exceptions, add caching, logging | P1 |
| `odds_service.py` | Add retry logic, timeouts, logging | P1 |
| `injury_service.py` | Add retry logic, timeouts | P1 |
| `database.py` | Add indexes, batch operations | P2 |
| `model_service.py` | Add evaluation, versioning | P3 |

### New Files to Create

| File | Purpose | Priority |
|------|---------|----------|
| `backend/config.py` | Centralized configuration | P1 |
| `backend/tests/test_*.py` | Unit & integration tests | P1 |
| `backend/pytest.ini` | Test configuration | P1 |
| `.github/workflows/ci.yml` | CI/CD pipeline | P2 |
| `backend/requirements-dev.txt` | Dev dependencies | P1 |

---

## 🧪 Testing Checklist

### Setup Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

# Create pytest.ini
echo "[pytest]
testpaths = tests
python_files = test_*.py
addopts = --cov=backend --cov-report=html -v" > pytest.ini

# Create tests directory
mkdir -p backend/tests
touch backend/tests/__init__.py
```

### Must-Have Tests
```python
# tests/test_ai_service.py
def test_consensus_unanimous_vote()
def test_consensus_split_vote()
def test_invalid_json_handling()

# tests/test_database.py
def test_save_and_retrieve_game()
def test_save_decision()

# tests/test_api.py
def test_health_endpoint()
def test_predict_validation()
def test_rate_limiting()
```

### Run Tests
```bash
# Run all tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## 📦 Dependencies to Add

### P1 (Essential)
```txt
# requirements.txt additions
slowapi==0.1.9          # Rate limiting
tenacity==8.2.3         # Retry logic
pydantic-settings==2.0.3  # Configuration

# requirements-dev.txt (new file)
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0
black==24.1.0
ruff==0.2.0
```

### P2 (Performance)
```txt
cachetools==5.3.2       # Caching
redis==5.0.1            # Distributed cache
```

### P3 (Monitoring)
```txt
prometheus-client==0.19.0
python-json-logger==2.0.7
sentry-sdk==1.39.0
```

---

## 🎯 Success Criteria

### Week 1
- [ ] All print() replaced with logging
- [ ] Config.py created and used
- [ ] Input validation on all endpoints
- [ ] CORS restricted
- [ ] Rate limiting active

### Week 2
- [ ] No bare except blocks
- [ ] Retry logic on external APIs
- [ ] Timeouts on all requests
- [ ] Pytest configured
- [ ] 10+ unit tests written

### Week 3
- [ ] Test coverage > 60%
- [ ] Integration tests passing
- [ ] Caching implemented
- [ ] Database indexes added
- [ ] Health check endpoint

---

## 🚀 Quick Commands

### Development
```bash
# Start backend with logging
cd backend
uvicorn main:app --reload --log-level debug

# Run tests
pytest -v

# Check coverage
pytest --cov=. --cov-report=html

# Format code
black .
ruff check .

# Type checking
mypy .
```

### Testing Specific Features
```bash
# Test single file
pytest tests/test_api.py -v

# Test with print output
pytest -s

# Test with coverage for one module
pytest tests/test_ai_service.py --cov=backend.ai_service
```

---

## 🔍 Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'typing'"
**Fix:** Remove `from typing import ...` if using Python 3.9+, or use `typing_extensions`

### Issue: "Database is locked"
**Fix:** 
```python
conn = sqlite3.connect(DB_NAME, timeout=10.0, check_same_thread=False)
```

### Issue: "CORS policy blocked"
**Fix:** 
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Rate limit exceeded on AI APIs"
**Fix:** Implement caching and reduce concurrent calls

---

## 📚 Resources

- **Full Implementation Plan:** See `IMPLEMENTATION_PLAN.md`
- **Code Analysis:** See `CODE_ANALYSIS.md`
- **Completed Fixes:** See `CRITICAL_FIXES.md`
- **Original Roadmap:** See `Total_Thingstoimplement.md`

---

## 🎉 Quick Win: Deploy These Today

These changes take < 2 hours and provide immediate value:

1. **Add Health Check** (5 min)
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

2. **Add Timeouts** (15 min)
```python
# Add to all requests.get()
response = requests.get(url, timeout=10)
```

3. **Setup Logging** (30 min)
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Replace all print() with logger.info()
```

4. **Pin Dependencies** (10 min)
```bash
pip freeze > requirements-lock.txt
```

5. **Add .env.example** (5 min)
```bash
cp .env .env.example
# Remove actual keys from .env.example
```

---

## 💡 Pro Tips

1. **Use Git Branches:** Create feature branches for each phase
2. **Test Locally First:** Don't push untested changes
3. **One Thing at a Time:** Complete P1 before moving to P2
4. **Keep Documentation Updated:** Update README as you go
5. **Measure Progress:** Use the success criteria checklist

---

## 📞 Need Help?

- Review detailed examples in `IMPLEMENTATION_PLAN.md`
- Check FastAPI docs: https://fastapi.tiangolo.com/
- Check Pytest docs: https://docs.pytest.org/
- Check Pydantic docs: https://docs.pydantic.dev/

---

**Remember:** Production-readiness is a journey, not a destination. Focus on P1 items first, then iterate!

**Good luck! 🏀🚀**
