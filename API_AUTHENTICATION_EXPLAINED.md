# SynthLab API Authentication & Rate Limiting

## Overview

The SynthLab API now includes enterprise-grade security features to protect synthetic data generation endpoints from unauthorized access and abuse. This document explains the authentication mechanisms, rate limiting, and security best practices.

---

## Table of Contents

1. [Why Authentication Matters](#why-authentication-matters)
2. [Authentication Mechanisms](#authentication-mechanisms)
3. [How JWT Tokens Work](#how-jwt-tokens-work)
4. [Rate Limiting](#rate-limiting)
5. [Security Features](#security-features)
6. [Usage Examples](#usage-examples)
7. [Role-Based Access Control](#role-based-access-control)
8. [Deployment Considerations](#deployment-considerations)

---

## Why Authentication Matters

### Problem Statement

Without authentication, the SynthLab API would be vulnerable to:

1. **Unauthorized Access**: Anyone with the API URL could generate synthetic data
2. **Resource Exhaustion**: Malicious actors could overwhelm the server with requests
3. **Data Misuse**: No audit trail of who accessed what data
4. **Compliance Issues**: HIPAA, GDPR, and other regulations require access controls

### Solution

We implement a multi-layered security approach:

```
┌─────────────────────────────────────────┐
│  User Authentication (JWT or API Key)   │ ← Layer 1: Identity
├─────────────────────────────────────────┤
│  Rate Limiting (per-user limits)        │ ← Layer 2: Abuse Prevention
├─────────────────────────────────────────┤
│  Role-Based Access Control (RBAC)       │ ← Layer 3: Authorization
├─────────────────────────────────────────┤
│  Audit Logging (who did what)           │ ← Layer 4: Compliance
└─────────────────────────────────────────┘
```

---

## Authentication Mechanisms

### 1. JWT (JSON Web Token) Authentication

**Best for**: Interactive users, web applications, mobile apps

**How it works**:
1. User sends username + password to `/auth/login`
2. Server validates credentials against user database
3. Server generates JWT token containing user claims (username, role, email)
4. Client stores token (localStorage, sessionStorage, or secure cookie)
5. Client includes token in `Authorization: Bearer <token>` header for subsequent requests
6. Server validates token signature and expiration on each request

**Advantages**:
- ✅ Stateless - no server-side session storage required
- ✅ Short-lived (1 hour by default) - limited window for token theft
- ✅ Contains user metadata - no database lookup on each request
- ✅ Can be refreshed - long sessions without storing password

**Example Flow**:
```bash
# Login
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "changeme123"}' \
     | jq -r '.access_token')

# Use token for authenticated request
curl -X POST "http://localhost:8000/generate" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@data.csv"
```

### 2. API Key Authentication

**Best for**: Programmatic access, scripts, CI/CD pipelines, long-running services

**How it works**:
1. Admin creates user account
2. System generates unique API key (e.g., `sk_abc123...`)
3. User stores API key securely (environment variable, secrets manager)
4. User includes API key in `Authorization: Bearer <api_key>` header
5. Server validates API key against user database

**Advantages**:
- ✅ No expiration - suitable for automated systems
- ✅ No login flow - direct authentication
- ✅ Can be revoked - delete user or regenerate key
- ✅ Simple integration - just one header

**Example Flow**:
```bash
# Get your API key from /auth/me after logging in
API_KEY="sk_KyvK2SOErZkafN7mdDYvhtZ_qj0LkKZ-QWtsj5Nk3u8"

# Use API key directly (no login required)
curl -X POST "http://localhost:8000/generate" \
     -H "Authorization: Bearer $API_KEY" \
     -F "file=@data.csv"
```

---

## How JWT Tokens Work

### Token Structure

A JWT consists of three parts separated by dots: `header.payload.signature`

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9  ← Header (algorithm + type)
.
eyJzdWIiOiJhZG1pbiIsImVtYWlsIjoi...    ← Payload (user claims)
.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV...  ← Signature (tamper protection)
```

### Header (Base64-encoded JSON)
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- `alg`: Signing algorithm (HS256 = HMAC-SHA256)
- `typ`: Token type (always "JWT")

### Payload (Base64-encoded JSON)
```json
{
  "sub": "admin",           // Subject (username)
  "email": "admin@synthlab.local",
  "role": "admin",
  "exp": 1768467018,        // Expiration timestamp
  "iat": 1768463418         // Issued at timestamp
}
```
- `sub`: Subject (username) - standard claim
- `exp`: Expiration time (Unix timestamp) - standard claim
- `iat`: Issued at time (Unix timestamp) - standard claim
- Custom claims: email, role, etc.

### Signature
```python
signature = HMAC-SHA256(
    base64(header) + "." + base64(payload),
    secret_key
)
```
- Prevents tampering - any modification invalidates signature
- Only server knows `secret_key` - clients cannot forge tokens
- Signature is verified on every request

### Token Validation Process

When a request arrives with a JWT token:

```python
# 1. Extract token from Authorization header
token = request.headers.get("Authorization").replace("Bearer ", "")

# 2. Decode and verify signature
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
# If signature invalid → 401 Unauthorized
# If expired → 401 Unauthorized

# 3. Extract user information
username = payload["sub"]
role = payload["role"]

# 4. Proceed with request (user is authenticated)
```

### Why JWT is Stateless

Traditional session-based auth:
```
Client → Login → Server creates session → Store in database
Client → Request → Server queries database for session → Validate
```
❌ Requires database query on every request
❌ Session storage grows with users
❌ Difficult to scale horizontally

JWT-based auth:
```
Client → Login → Server creates JWT → Signs with secret key
Client → Request → Server validates signature → Extract claims from token
```
✅ No database query (user info in token)
✅ No session storage
✅ Easy to scale (any server can validate)

---

## Rate Limiting

### Why Rate Limiting?

**Problem**: Without limits, a single user could:
- Submit 10,000 requests in 1 minute
- Consume all CPU training CTGAN models
- Prevent legitimate users from accessing the API
- Cost money (cloud compute, bandwidth)

**Solution**: Enforce per-user request limits

### Rate Limiting Algorithm

We use a **sliding window** algorithm:

```python
# Track timestamps of recent requests
user_requests = {
    "admin:/generate": [
        datetime(2026, 1, 12, 14, 30, 10),
        datetime(2026, 1, 12, 14, 30, 15),
        datetime(2026, 1, 12, 14, 30, 20),
        # ... up to 100 requests for admin
    ]
}

# On new request at 14:30:25
now = datetime(2026, 1, 12, 14, 30, 25)
cutoff = now - timedelta(minutes=1)  # 14:29:25

# Filter requests in last minute
recent_requests = [r for r in user_requests["admin:/generate"] if r > cutoff]

# Check limit
if len(recent_requests) >= user.rate_limit:
    return 429 Too Many Requests
else:
    recent_requests.append(now)
    return proceed with request
```

**Advantages of Sliding Window**:
- ✅ Smooth rate enforcement (not bursty)
- ✅ Fair distribution across time
- ✅ Automatic cleanup of old entries

**Alternative**: Token bucket, leaky bucket (more complex, similar behavior)

### Rate Limit Headers

Every response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1768467080
```

- `X-RateLimit-Limit`: Total requests allowed per minute
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

**Client Implementation Example**:
```python
response = requests.post(url, headers=headers)

remaining = int(response.headers["X-RateLimit-Remaining"])
if remaining < 3:
    print(f"Warning: Only {remaining} requests remaining!")
    # Slow down or wait

if response.status_code == 429:
    reset_time = int(response.headers["X-RateLimit-Reset"])
    wait_seconds = reset_time - time.time()
    print(f"Rate limited! Waiting {wait_seconds} seconds...")
    time.sleep(wait_seconds)
```

### Per-User Limits

Different user roles have different limits:

| Role | Rate Limit | Use Case |
|------|-----------|----------|
| Admin | 100 req/min | System administration, bulk operations |
| Researcher | 10 req/min | Standard data generation, analysis |
| Viewer | 5 req/min | Read-only access (future) |

**Why Different Limits?**
- Admins need higher limits for system management
- Researchers have moderate needs (few datasets per session)
- Prevents abuse while allowing legitimate use

### Rate Limiting in Distributed Systems

**Current Implementation**: In-memory (single server)
```python
rate_limiter = RateLimiter()  # Stores requests in Python dict
```

**Production Implementation**: Use Redis
```python
import redis

def check_rate_limit(user, endpoint):
    key = f"rate:{user.username}:{endpoint}"
    pipe = redis.pipeline()

    # Add current request with expiration
    pipe.zadd(key, {time.time(): time.time()})
    pipe.zremrangebyscore(key, 0, time.time() - 60)  # Remove old
    pipe.zcard(key)  # Count recent
    pipe.expire(key, 60)

    _, _, count, _ = pipe.execute()
    return count <= user.rate_limit
```

**Why Redis?**
- Shared state across multiple API servers
- Atomic operations (no race conditions)
- Built-in expiration (automatic cleanup)
- High performance (microseconds latency)

---

## Security Features

### 1. Password Hashing (Argon2)

**Why Not Store Plain Passwords?**
```python
# ❌ NEVER DO THIS
users = {"admin": {"password": "changeme123"}}
```
- If database is leaked, all passwords are exposed
- Attackers can directly log in as users

**Solution: Cryptographic Hashing**
```python
# ✅ Store only hash
users = {
    "admin": {
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$..."
    }
}

# Login validation
input_password = request.json["password"]
is_valid = argon2.verify(users["admin"]["hashed_password"], input_password)
```

**Properties of Cryptographic Hash Functions**:
1. **One-way**: Cannot reverse hash to get password
2. **Deterministic**: Same input → same hash
3. **Collision-resistant**: Hard to find two inputs with same hash
4. **Avalanche effect**: Small input change → completely different hash

**Why Argon2?**

Argon2 won the [Password Hashing Competition](https://password-hashing.net/) in 2015.

| Algorithm | Security | Speed | Notes |
|-----------|----------|-------|-------|
| MD5 | ❌ Broken | Very fast | NEVER use |
| SHA-256 | ❌ Too fast | Very fast | Not for passwords |
| bcrypt | ✅ Good | Fast | 72-byte limit |
| **Argon2** | ✅ **Best** | Configurable | **Recommended** |

**Argon2 Features**:
- **Memory-hard**: Requires large RAM → prevents GPU cracking
- **Time-hard**: Takes ~300ms to hash → prevents brute force
- **Parallelism**: Uses multiple CPU cores
- **No length limit**: Unlike bcrypt (72 bytes)

**Argon2 Configuration**:
```python
# Default settings
memory_cost = 65536  # 64 MB RAM
time_cost = 3        # 3 iterations
parallelism = 4      # 4 threads
```

**Attack Resistance**:
```
Attacker with RTX 4090 GPU ($1600):
- MD5: 100 billion passwords/sec → crack in minutes
- bcrypt: 100,000 passwords/sec → crack in years
- Argon2: 10 passwords/sec → crack in centuries
```

### 2. JWT Secret Key

The JWT secret key is the most critical security component:

```python
SECRET_KEY = os.getenv("SYNTHLAB_SECRET_KEY", secrets.token_urlsafe(32))
```

**Security Requirements**:
- ✅ At least 256 bits (32 bytes) of entropy
- ✅ Cryptographically random (not predictable)
- ✅ Stored securely (environment variable, secrets manager)
- ❌ NEVER commit to Git
- ❌ NEVER expose in logs or error messages

**Generating Secure Keys**:
```bash
# Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# /dev/urandom
head -c 32 /dev/urandom | base64
```

**What If Secret Key is Leaked?**
1. Attacker can forge valid JWT tokens
2. Attacker can impersonate any user (including admin)
3. Must immediately:
   - Rotate secret key (invalidates all existing tokens)
   - Force all users to re-login
   - Investigate how key was leaked

**Key Rotation Strategy** (production):
```python
# Support multiple keys for graceful rotation
ACTIVE_KEY = os.getenv("JWT_KEY_ACTIVE")
OLD_KEYS = [os.getenv("JWT_KEY_1"), os.getenv("JWT_KEY_2")]

# Sign with active key
token = jwt.encode(payload, ACTIVE_KEY, algorithm="HS256")

# Verify with any key
for key in [ACTIVE_KEY] + OLD_KEYS:
    try:
        return jwt.decode(token, key, algorithms=["HS256"])
    except JWTError:
        continue
```

### 3. Token Expiration

**Why Tokens Expire**:
- Limits damage if token is stolen
- Forces re-authentication periodically
- Allows revoking access (wait for expiration)

**Current Expiration Times**:
- Access Token: **60 minutes** (short-lived)
- Refresh Token: **30 days** (long-lived, not yet implemented)

**Token Refresh Flow** (future enhancement):
```
1. User logs in → receives access token (1h) + refresh token (30d)
2. User makes requests with access token
3. After 1 hour, access token expires
4. Instead of re-entering password, user sends refresh token
5. Server validates refresh token → issues new access token
6. Repeat steps 2-5 for up to 30 days
7. After 30 days, refresh token expires → must re-login
```

**Benefits**:
- Short access token expiration (limits theft window)
- Long session duration (better UX)
- Can revoke refresh tokens (immediate logout)

### 4. Audit Logging

Every authenticated request is logged:

```python
print(f"[AUDIT] User: {user.username}, Method: {method}, Rows: {rows}, File: {file.filename}")
```

**Current Output** (console):
```
[AUDIT] User: admin, Method: CTGAN, Rows: 1000, File: patient_data.csv
[AUDIT] User: researcher1, Action: analyze, Method: TVAE, File: lab_results.csv
```

**Production Implementation** (structured logging):
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "synthetic_data_generated",
    user=user.username,
    role=user.role,
    method=method,
    rows=rows,
    filename=file.filename,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    timestamp=datetime.utcnow().isoformat()
)
```

**Audit Log Use Cases**:
1. **Security**: Detect unusual activity (100 requests from one user in 1 minute)
2. **Compliance**: HIPAA requires access logs for PHI
3. **Analytics**: Which synthesis methods are most popular?
4. **Debugging**: Reproduce user issues
5. **Billing**: Track usage for resource accounting

**Log Storage** (production):
- Local files (logrotate for management)
- Elasticsearch (searchable logs)
- CloudWatch/Stackdriver (cloud services)
- SIEM systems (security monitoring)

---

## Usage Examples

### Example 1: Web Application (React)

```javascript
// Login component
async function login(username, password) {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // Store token in localStorage
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
}

// Protected API call
async function generateSyntheticData(file) {
  const token = localStorage.getItem('token');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('method', 'CTGAN');
  formData.append('rows', '1000');

  const response = await fetch('http://localhost:8000/generate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (response.status === 401) {
    // Token expired, redirect to login
    window.location.href = '/login';
    return;
  }

  const blob = await response.blob();
  return blob;
}
```

### Example 2: Python Script

```python
import requests
import os

# Store API key in environment variable
API_KEY = os.getenv("SYNTHLAB_API_KEY")

# Generate synthetic data
with open("patient_data.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/generate",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": f},
        data={"method": "CTGAN", "rows": "1000"}
    )

# Check rate limit
remaining = int(response.headers["X-RateLimit-Remaining"])
print(f"Requests remaining: {remaining}")

# Save synthetic data
with open("synthetic_output.csv", "wb") as f:
    f.write(response.content)
```

### Example 3: CI/CD Pipeline (GitHub Actions)

```yaml
name: Generate Test Data

on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate synthetic test data
        env:
          SYNTHLAB_API_KEY: ${{ secrets.SYNTHLAB_API_KEY }}
        run: |
          curl -X POST "https://synthlab.example.com/generate" \
               -H "Authorization: Bearer $SYNTHLAB_API_KEY" \
               -F "file=@tests/fixtures/sample_data.csv" \
               -F "method=GaussianCopula" \
               -F "rows=500" \
               -o tests/data/synthetic.csv

      - name: Run tests with synthetic data
        run: pytest tests/
```

---

## Role-Based Access Control (RBAC)

### User Roles

| Role | Permissions | Rate Limit | Use Case |
|------|------------|-----------|----------|
| **admin** | Full access, can create users | 100 req/min | System administrators |
| **researcher** | Generate & analyze data | 10 req/min | Data scientists, researchers |
| **viewer** | Read-only (future) | 5 req/min | Stakeholders, reviewers |

### Enforcing Roles

```python
# Require specific role(s)
@app.delete("/admin/users/{username}")
def delete_user(
    username: str,
    user: User = Depends(auth_manager.require_role(["admin"]))
):
    """Only admins can delete users."""
    # Delete user logic
```

**How It Works**:
1. `require_role(["admin"])` creates a dependency
2. Dependency first authenticates user (JWT validation)
3. Then checks if `user.role in ["admin"]`
4. If not → 403 Forbidden
5. If yes → proceed with endpoint logic

### Role Hierarchy (future)

```
admin
  └─ researcher
       └─ viewer
```

- Admin inherits all researcher permissions
- Researcher inherits all viewer permissions
- Implement with permission checks: `user.role_level >= REQUIRED_LEVEL`

---

## Deployment Considerations

### Environment Variables

**Required Settings** (`.env` file):
```bash
# CRITICAL: Change this before deploying
SYNTHLAB_SECRET_KEY="your-256-bit-secret-key-here"

# Optional: Database path (default: data/users.json)
SYNTHLAB_USER_DB_PATH="/secure/path/users.json"

# Optional: Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Optional: Log level
LOG_LEVEL=INFO
```

**Never commit `.env` to Git**:
```bash
# .gitignore
.env
*.env
```

### Production Checklist

- [ ] **Change default admin password** immediately
- [ ] **Set strong SECRET_KEY** (256+ bits, cryptographically random)
- [ ] **Enable HTTPS** (TLS 1.3, valid certificate)
- [ ] **Restrict CORS origins** (not `*` in production)
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://synthlab.example.com"],  # Specific domain
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["Authorization", "Content-Type"],
  )
  ```
- [ ] **Use Redis for rate limiting** (distributed systems)
- [ ] **Implement refresh tokens** (better UX for long sessions)
- [ ] **Set up log aggregation** (Elasticsearch, CloudWatch, etc.)
- [ ] **Enable request logging** (access logs, error logs)
- [ ] **Add request timeouts** (prevent long-running requests)
- [ ] **Implement database-backed user storage** (PostgreSQL, MongoDB)
- [ ] **Set up backup for user database** (automated, encrypted)
- [ ] **Add monitoring** (Prometheus, Grafana, or similar)
- [ ] **Configure firewall** (only allow necessary ports)
- [ ] **Enable rate limiting at nginx/load balancer** (defense in depth)

### HTTPS Configuration (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name synthlab.example.com;

    ssl_certificate /etc/ssl/certs/synthlab.crt;
    ssl_certificate_key /etc/ssl/private/synthlab.key;
    ssl_protocols TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Rate limiting at nginx level
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 1000 synthlab && chown -R synthlab:synthlab /app
USER synthlab

# Expose port
EXPOSE 8000

# Run with environment variables from docker-compose
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SYNTHLAB_SECRET_KEY=${SYNTHLAB_SECRET_KEY}
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### Scaling Considerations

**Current Limitations** (single server):
- In-memory rate limiting (not shared across servers)
- File-based user database (not suitable for high concurrency)
- No horizontal scaling

**Production Architecture**:
```
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
      ┌────▼───┐      ┌────▼───┐     ┌────▼───┐
      │ API #1 │      │ API #2 │     │ API #3 │
      └────┬───┘      └────┬───┘     └────┬───┘
           │               │               │
           └───────────────┼───────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌────▼────┐ ┌────▼────┐
         │  Redis  │  │ PostgreS│ │ S3/Blob │
         │ (rates) │  │QL(users)│ │(models) │
         └─────────┘  └─────────┘ └─────────┘
```

---

## Troubleshooting

### Common Issues

**1. "Invalid authentication token"**
```
Cause: Token expired or invalid signature
Solution: Re-login to get new token
```

**2. "Rate limit exceeded"**
```
Cause: Too many requests in 1 minute
Solution: Wait until X-RateLimit-Reset time, then retry
```

**3. "Insufficient permissions"**
```
Cause: User role doesn't have access to endpoint
Solution: Contact admin for role upgrade
```

**4. "User not found"**
```
Cause: User was deleted or never existed
Solution: Contact admin to recreate account
```

### Debug Mode

Enable detailed logging:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("api_auth")

logger.debug(f"Token: {token[:20]}...")
logger.debug(f"User: {user.username}, Role: {user.role}")
```

---

## Summary

**Authentication Mechanisms**:
- JWT tokens for interactive users (1-hour expiration)
- API keys for programmatic access (no expiration)

**Security Features**:
- Argon2 password hashing (memory-hard, GPU-resistant)
- 256-bit JWT secret key (HMAC-SHA256 signatures)
- Per-user rate limiting (10-100 req/min)
- Role-based access control (admin, researcher, viewer)
- Audit logging (who did what, when)

**Rate Limiting**:
- Sliding window algorithm (smooth enforcement)
- Per-user, per-endpoint tracking
- Rate limit headers in responses
- Automatic cleanup of old requests

**Deployment**:
- Change default admin password immediately
- Set strong SECRET_KEY from environment variable
- Enable HTTPS with valid TLS certificate
- Use Redis for distributed rate limiting (production)
- Use PostgreSQL for user storage (production)
- Set up log aggregation and monitoring
- Configure firewall and load balancer

**Next Steps**:
1. Test authentication with `test_api_auth.sh`
2. Change default admin password
3. Create researcher accounts
4. Integrate with frontend (Streamlit, React, etc.)
5. Plan production deployment (Docker, Kubernetes, etc.)

---

*Generated by SynthLab Development Team - 2026-01-12*
