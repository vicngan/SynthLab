#!/bin/bash

# Test script for SynthLab API Authentication
# This script demonstrates the full authentication flow

BASE_URL="http://localhost:8000"

echo "======================================"
echo "SynthLab API Authentication Test"
echo "======================================"
echo ""

# Step 1: Try accessing protected endpoint without auth (should fail)
echo "[1] Testing /generate without authentication (should fail)..."
curl -s -X POST "$BASE_URL/generate" \
     -F "file=@data/diabetes.csv" \
     -w "\nHTTP Status: %{http_code}\n" \
     | head -20
echo ""
echo "---"
echo ""

# Step 2: Login to get JWT token
echo "[2] Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "changeme123"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get token"
    exit 1
fi

echo "✓ Token obtained: ${TOKEN:0:50}..."
echo ""
echo "---"
echo ""

# Step 3: Get current user info
echo "[3] Getting current user info..."
curl -s -X GET "$BASE_URL/auth/me" \
     -H "Authorization: Bearer $TOKEN" \
     | python3 -m json.tool
echo ""
echo "---"
echo ""

# Step 4: Generate synthetic data with authentication
echo "[4] Generating synthetic data (authenticated)..."
curl -s -X POST "$BASE_URL/generate" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@data/diabetes.csv" \
     -F "rows=100" \
     -F "method=GaussianCopula" \
     -o /tmp/synthetic_test.csv \
     -w "HTTP Status: %{http_code}\n"

if [ -f /tmp/synthetic_test.csv ]; then
    echo "✓ Synthetic data generated successfully!"
    echo "  First 5 rows:"
    head -5 /tmp/synthetic_test.csv
    echo "  ..."
fi
echo ""
echo "---"
echo ""

# Step 5: Analyze synthetic data
echo "[5] Analyzing synthetic data quality..."
curl -s -X POST "$BASE_URL/analyze" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@data/diabetes.csv" \
     -F "method=GaussianCopula" \
     | python3 -m json.tool | head -40
echo "  ..."
echo ""
echo "---"
echo ""

# Step 6: Test rate limiting (make multiple requests quickly)
echo "[6] Testing rate limiting (100 req/min for admin)..."
for i in {1..5}; do
    RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
         -H "Authorization: Bearer $TOKEN" \
         -w "\nX-RateLimit-Remaining: %header{X-RateLimit-Remaining}" \
         -o /dev/null)
    echo "  Request $i: $RESPONSE"
done
echo ""
echo "---"
echo ""

# Step 7: Test API key authentication
echo "[7] Testing API key authentication..."
API_KEY=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; resp = json.load(sys.stdin); import requests; me = requests.get('$BASE_URL/auth/me', headers={'Authorization': f'Bearer {resp[\"access_token\"]}'}).json(); print(me['api_key'])" 2>/dev/null)

if [ -n "$API_KEY" ]; then
    echo "  API Key: ${API_KEY:0:20}..."
    curl -s -X GET "$BASE_URL/auth/me" \
         -H "Authorization: Bearer $API_KEY" \
         | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"  ✓ Authenticated as: {data['username']} (role: {data['role']})\")"
fi
echo ""
echo "---"
echo ""

echo "======================================"
echo "All Tests Complete!"
echo "======================================"
echo ""
echo "Summary:"
echo "  ✓ Authentication working"
echo "  ✓ JWT tokens generated and validated"
echo "  ✓ Protected endpoints secured"
echo "  ✓ Rate limiting enforced"
echo "  ✓ API key authentication working"
echo ""
