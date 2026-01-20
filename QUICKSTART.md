# SynthLab Quick Start Guide

**Version:** 1.0 | **Date:** 2026-01-12

Get SynthLab up and running in 5 minutes!

---

## Prerequisites

- Python 3.12+
- Virtual environment activated
- All dependencies installed

---

## Step 1: Start the API Server (Terminal 1)

```bash
cd /Users/victoriangannguyen/Downloads/vic_coding/SynthLab

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn api:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify API is running:**
- Open browser: http://localhost:8000/docs
- You should see the FastAPI interactive documentation

---

## Step 2: Start the Streamlit UI (Terminal 2)

```bash
# In a NEW terminal window
cd /Users/victoriangannguyen/Downloads/vic_coding/SynthLab

# Activate virtual environment
source venv/bin/activate

# Start Streamlit
streamlit run app_enhanced.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

**Your browser should automatically open to:** http://localhost:8501

---

## Step 3: Login

**Default Credentials:**
```
Username: admin
Password: changeme123
```

⚠️ **IMPORTANT**: Change this password before production use!

**After login, you'll see:**
- User profile in sidebar (username, role, email)
- Synthesis settings (method, rows)
- Privacy controls (DP, k-anonymity, etc.)
- Six main tabs

---

## Step 4: Generate Your First Synthetic Dataset

### 4.1 Enable Privacy Protections

**In Sidebar:**
1. ✅ Check "Enable Differential Privacy"
2. Set ε = 1.0 (strong privacy)
3. Set k-anonymity = 3
4. ✅ Check "Enable Constraints"

### 4.2 Upload Data

**In Tab 1 (Synthetic Data):**
1. Click "Browse files" or drag-and-drop
2. Upload: `data/diabetes.csv`
3. Preview data (first 10 rows shown)

### 4.3 Generate Synthetic Data

1. Method: Select "CTGAN" (best quality)
2. Rows: Enter 1000
3. Click "🚀 Generate Synthetic Data"
4. Wait ~5 minutes (first time) or ~2 seconds (cached)

### 4.4 View Results

**Automatically displayed:**
- Synthetic data preview (first 10 rows)
- Download button (CSV)
- Statistical similarity metrics
- Privacy check (exact matches)
- Distribution comparison plots

### 4.5 Download Synthetic Data

Click **"📥 Download Synthetic Data (CSV)"**

✅ **Done!** You now have privacy-safe synthetic data!

---

## Step 5: Analyze Privacy (Optional)

### 5.1 Go to Tab 2 (Advanced Privacy)

1. Select dataset: `diabetes.csv`
2. Choose quasi-identifiers:
   - Age
   - Gender
   - BMI
3. Choose sensitive attributes:
   - Outcome (diabetes diagnosis)

### 5.2 View Privacy Analysis

**Six sub-tabs available:**
1. **Overview**: Summary + recommendations
2. **Differential Privacy**: ε,δ status
3. **k-Anonymity**: Group size analysis
4. **l-Diversity**: Sensitive value diversity
5. **t-Closeness**: Distribution similarity
6. **DCR Analysis**: Distance to closest record

**Example Output:**
```
✅ Privacy Score: 100% (no exact matches)
✅ k-anonymity satisfied (k=3)
✅ l-diversity satisfied (l=2)
✅ t-closeness satisfied (t=0.2)
✅ Mean DCR: 0.15 (good separation)
```

---

## Step 6: Create New Users (Admin Only)

### 6.1 Go to Tab 6 (User Management)

**Only visible if you're logged in as admin.**

### 6.2 Create Researcher Account

1. Username: `researcher1`
2. Email: `researcher@example.com`
3. Password: `secure_password123`
4. Role: `researcher`
5. Click "Create User"

**Result:**
```
✅ User 'researcher1' created successfully!
API Key: sk_iSSFMO8Aflz_H1_Klabcdefghijklmnopqrstuvwxyz
```

**Copy the API key** - it won't be shown again!

---

## Common Workflows

### Workflow 1: Quick Generation (No Privacy)

```
1. Login
2. Upload CSV
3. Click Generate (default settings)
4. Download synthetic data
```

**Time:** ~30 seconds (after cache)

---

### Workflow 2: HIPAA-Compliant Generation

```
1. Login
2. Enable Differential Privacy ✅
   - ε = 1.0, δ = 1e-5
3. Set k-anonymity = 5
4. Enable Constraints ✅
5. Upload patient data
6. Generate with CTGAN
7. Verify privacy in Tab 2
8. Download if all checks pass
```

**Time:** ~5 minutes first time, ~1 minute cached

---

### Workflow 3: Experiment with Parameters

```
1. Generate with ε = 0.5 (very strong privacy)
2. Generate with ε = 2.0 (more utility)
3. Compare quality metrics
4. Compare privacy scores
5. Choose best tradeoff
```

**Time:** ~2 seconds each (cached model)

---

## Troubleshooting

### Issue: "Cannot connect to API server"

**Solution:**
```bash
# Check if API is running
curl http://localhost:8000

# If not running, start it:
uvicorn api:app --reload --port 8000
```

---

### Issue: "Invalid authentication token"

**Solution:**
Token expired (60-minute timeout). Logout and login again.

---

### Issue: "No models cached yet"

**Solution:**
This is normal on first run. Generate synthetic data once to populate cache.

---

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn api:app --reload --port 8001

# Update API_BASE_URL in app_enhanced.py
API_BASE_URL = "http://localhost:8001"
```

---

## Testing the System

### Test 1: Authentication

```bash
# Terminal 3 (keep API and UI running)
source venv/bin/activate

# Run authentication tests
./test_api_auth.sh
```

**Expected:**
```
✓ Login successful
✓ Token generated
✓ Protected endpoints secured
✓ Rate limiting enforced
```

---

### Test 2: Privacy Modules

```bash
# Test differential privacy
python src/modules/privacy_engine.py

# Test re-identification analyzer
python src/modules/reidentification.py

# Test constraints
python src/modules/constraint_manager.py

# Test caching
python src/modules/model_cache.py
```

**All should show:** ✓ All tests passed

---

## API Usage (Programmatic Access)

### Using curl

```bash
# 1. Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "changeme123"}' \
     | jq -r '.access_token')

# 2. Generate synthetic data
curl -X POST "http://localhost:8000/generate" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@data/diabetes.csv" \
     -F "method=CTGAN" \
     -F "rows=1000" \
     -o synthetic_diabetes.csv

echo "Synthetic data saved to synthetic_diabetes.csv"
```

---

### Using Python

```python
import requests

# 1. Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "changeme123"}
)
token = response.json()["access_token"]

# 2. Generate synthetic data
with open("data/diabetes.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/generate",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f},
        data={"method": "CTGAN", "rows": 1000}
    )

# 3. Save synthetic data
with open("synthetic_diabetes.csv", "wb") as f:
    f.write(response.content)

print("✓ Synthetic data generated!")
```

---

### Using API Key (No Login Required)

```bash
# Get your API key from UI (Tab 6) or /auth/me endpoint
API_KEY="sk_KyvK2SOErZkafN7mdDYvhtZ_qj0LkKZ-QWtsj5Nk3u8"

# Use API key directly
curl -X POST "http://localhost:8000/generate" \
     -H "Authorization: Bearer $API_KEY" \
     -F "file=@data/diabetes.csv" \
     -F "method=CTGAN" \
     -o synthetic.csv
```

---

## What's Next?

### Learn More

1. **Privacy Concepts**: Read `DIFFERENTIAL_PRIVACY_EXPLAINED.md`
2. **Constraints**: Read `CONSTRAINTS_EXPLAINED.md`
3. **Authentication**: Read `API_AUTHENTICATION_EXPLAINED.md`
4. **UI Features**: Read `UI_INTEGRATION_GUIDE.md`
5. **Phase 1 Summary**: Read `PHASE1_COMPLETE.md`

### Customize

1. **Create Custom Constraints**: See `data/constraint_profiles/`
2. **Adjust Privacy Thresholds**: Tune ε, k, l, t for your use case
3. **Add Users**: Create accounts for your team

### Deploy to Production

See **Production Deployment Checklist** in `API_AUTHENTICATION_EXPLAINED.md`

---

## Summary

**You should now be able to:**
✅ Start API server and Streamlit UI
✅ Login with default credentials
✅ Generate privacy-safe synthetic data
✅ Analyze privacy metrics
✅ Create new user accounts
✅ Use the API programmatically

**Time to get started:** 5 minutes
**Time to generate first synthetic dataset:** 5-10 minutes
**Time to become proficient:** 1-2 hours

---

## Need Help?

**Documentation:**
- `PHASE1_COMPLETE.md` - Complete overview
- `UI_INTEGRATION_GUIDE.md` - UI feature tour
- `API_AUTHENTICATION_EXPLAINED.md` - API details

**Troubleshooting:**
- Check API is running: http://localhost:8000/docs
- Check UI is running: http://localhost:8501
- Check logs in terminal windows
- Review error messages in UI

**Common Issues:**
- Port conflicts → Use different ports
- Token expired → Logout and login
- API connection failed → Restart API server

---

**Happy Synthesizing! 🧬**

*Quick Start Guide - SynthLab v1.0*
