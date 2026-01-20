# SynthLab Services - Currently Running

**Status:** ✅ Both services are running
**Date:** 2026-01-19
**UI Version:** Clinical Dark Mode (v4.0 "Clinical Precision")

---

## Active Services

### 1. FastAPI Backend
- **URL:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Status:** ✅ Running
- **Log file:** `api.log`

### 2. Streamlit Frontend (Clinical Dark Mode)
- **URL:** http://localhost:8501
- **Status:** ✅ Running
- **File:** `app_theme.py`
- **Log file:** `streamlit_theme.log`
- **Design Features:**
  - **Clinical Dark Mode** (default theme)
  - Deep Gunmetal background (#0F172A)
  - Medical Teal accent (#14B8A6)
  - Bioscience Blue secondary (#3B82F6)
  - JetBrains Mono for data/metrics (monospace)
  - Inter for UI text (sans-serif)
  - Glass morphism effects
  - Glow effects on interactive elements
  - Light/Dark theme toggle (🌙/☀️)
  - All 5 tabs: Generate, Privacy, Literature, Cache, Users/Docs
  - **Tagline:** "Synthetic Healthcare Data. Mathematically Validated."

---

## Quick Access

### Open the UI in your browser:
```bash
open http://localhost:8501
```

Or manually navigate to: **http://localhost:8501**

### Login Credentials:
```
Username: admin
Password: changeme123
```

---

## View Logs

```bash
# API logs
tail -f api.log

# Streamlit logs
tail -f streamlit.log
```

---

## Stop Services

```bash
# Stop both
pkill -f "uvicorn api:app"
pkill -f "streamlit run"

# Or stop individually
lsof -ti:8000 | xargs kill  # Stop API
lsof -ti:8501 | xargs kill  # Stop Streamlit
```

---

## Restart Services

```bash
# Kill existing
pkill -f "uvicorn api:app"
pkill -f "streamlit run"
sleep 2

# Start API
source venv/bin/activate
nohup uvicorn api:app --reload --port 8000 > api.log 2>&1 &

# Start Streamlit
nohup streamlit run app_enhanced.py --server.headless true --server.port 8501 > streamlit.log 2>&1 &
```

---

## Test the System

### 1. Test API
```bash
curl http://localhost:8000/
```

Expected output:
```json
{
    "message": "SynthLab API",
    "version": "1.0.0",
    "docs": "/docs",
    "authentication": "Required - Use /auth/login or /auth/register"
}
```

### 2. Test Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "changeme123"}'
```

### 3. Open UI
Navigate to http://localhost:8501 and you should see the login page.

---

## Troubleshooting

### Port already in use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :8501

# Kill the process
kill -9 <PID>
```

### Service not responding
```bash
# Check logs
tail -20 api.log
tail -20 streamlit.log

# Restart service (see "Restart Services" above)
```

---

**Services are ready for testing!** 🚀

Open http://localhost:8501 in your browser to start using SynthLab.
