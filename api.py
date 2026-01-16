from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import pandas as pd
from io import BytesIO, StringIO
from typing import Optional
from datetime import timedelta

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport
from src.modules.api_auth import (
    auth_manager,
    rate_limiter,
    rate_limit_dependency,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(
    title="SynthLab API",
    description="Generate synthetic data and evaluate its quality with enterprise-grade security.",
    version="1.0.0"
)

# Enable CORS for web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "researcher"


class UserResponse(BaseModel):
    username: str
    email: str
    role: str
    api_key: str
    rate_limit: int

@app.get("/")
def root():
    """Public endpoint with API information."""
    return {
        "message": "SynthLab API",
        "version": "1.0.0",
        "docs": "/docs",
        "authentication": "Required - Use /auth/login or /auth/register"
    }


@app.post("/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """
    Authenticate user and receive JWT access token.

    **Authentication Flow:**
    1. Client sends username and password
    2. Server validates credentials against user database
    3. If valid, server generates JWT token with expiration
    4. Client stores token and includes it in Authorization header for subsequent requests

    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/auth/login" \\
         -H "Content-Type: application/json" \\
         -d '{"username": "admin", "password": "changeme123"}'
    ```

    **Example Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "username": "admin",
            "email": "admin@synthlab.local",
            "role": "admin"
        }
    }
    ```

    **Using the Token:**
    ```bash
    curl -X POST "http://localhost:8000/generate" \\
         -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
         -F "file=@data.csv"
    ```
    """
    # Authenticate user
    user = auth_manager.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    token_data = {
        "sub": user.username,
        "email": user.email,
        "role": user.role
    }
    access_token = auth_manager.create_access_token(
        token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )


@app.post("/auth/register", response_model=UserResponse)
def register(
    user_data: UserCreateRequest,
    admin_user: User = Depends(auth_manager.require_role(["admin"]))
):
    """
    Register a new user (admin only).

    Only administrators can create new user accounts. This prevents unauthorized
    access to the synthetic data generation system.

    **Roles:**
    - **admin**: Full access, can create users, unlimited rate limit
    - **researcher**: Standard access, can generate and analyze data
    - **viewer**: Read-only access (future feature)

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/auth/register" \\
         -H "Authorization: Bearer ADMIN_TOKEN" \\
         -H "Content-Type: application/json" \\
         -d '{
           "username": "researcher1",
           "email": "researcher@university.edu",
           "password": "secure_password",
           "role": "researcher"
         }'
    ```
    """
    # Check if user already exists
    existing_user = auth_manager.user_db.get_user(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=auth_manager.hash_password(user_data.password),
        role=user_data.role,
        rate_limit=100 if user_data.role == "admin" else 10
    )

    success = auth_manager.user_db.create_user(new_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return UserResponse(
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        api_key=new_user.api_key,
        rate_limit=new_user.rate_limit
    )


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(auth_manager.get_current_user)):
    """
    Get information about the currently authenticated user.

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/auth/me" \\
         -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    return UserResponse(
        username=user.username,
        email=user.email,
        role=user.role,
        api_key=user.api_key,
        rate_limit=user.rate_limit
    )

@app.post("/generate")
async def generate_synthetic_data(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    rows: int = 1000,
    method: str = "GaussianCopula",
    user: User = Depends(rate_limit_dependency)
):
    """
    Generate synthetic data from a CSV file using the specified method.

    **This endpoint is PROTECTED and requires authentication.**

    **Rate Limiting:**
    - Standard users: 10 requests/minute
    - Admin users: 100 requests/minute
    - Rate limit headers included in response

    **Security Features:**
    - JWT token authentication required
    - Per-user rate limiting to prevent abuse
    - Audit logging (user, timestamp, file)

    **Supported Methods:**
    - **GaussianCopula**: Fast, good for continuous data with correlations
    - **TVAE**: Variational autoencoder, good for mixed data types
    - **CTGAN**: GAN-based, best quality for complex distributions (slower)

    **Example:**
    ```bash
    # 1. Login to get token
    TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \\
         -H "Content-Type: application/json" \\
         -d '{"username": "admin", "password": "changeme123"}' \\
         | jq -r '.access_token')

    # 2. Generate synthetic data
    curl -X POST "http://localhost:8000/generate" \\
         -H "Authorization: Bearer $TOKEN" \\
         -F "file=@patient_data.csv" \\
         -F "rows=1000" \\
         -F "method=CTGAN" \\
         -o synthetic_output.csv
    ```

    **Using API Key (alternative to JWT):**
    ```bash
    curl -X POST "http://localhost:8000/generate" \\
         -H "Authorization: Bearer YOUR_API_KEY" \\
         -F "file=@data.csv"
    ```

    Args:
        file: CSV file containing training data
        rows: Number of synthetic rows to generate (default: 1000)
        method: Synthesis method (GaussianCopula, TVAE, or CTGAN)
        user: Authenticated user (injected by dependency)

    Returns:
        CSV file containing synthetic data
    """
    # Add rate limit headers to response
    endpoint = request.url.path
    rate_headers = rate_limiter.get_rate_limit_headers(user, endpoint)
    for key, value in rate_headers.items():
        response.headers[key] = value

    # Validate file format
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    # Validate method
    if method not in ["GaussianCopula", "TVAE", "CTGAN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid method. Supported: GaussianCopula, TVAE, CTGAN"
        )

    # Read uploaded file
    content = await file.read()
    data = pd.read_csv(StringIO(content.decode('utf-8')))

    # Clean the data
    loader = DataLoader()
    cleaned_data, cols = loader.clean_data(data)

    # Generate synthetic data
    generator = SyntheticGenerator(method=method)
    generator.train(cleaned_data)
    synthetic_data = generator.generate(rows)

    # Audit log (in production, log to file or database)
    print(f"[AUDIT] User: {user.username}, Method: {method}, Rows: {rows}, File: {file.filename}")

    # Return synthetic data as CSV
    output = BytesIO()
    synthetic_data.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=synthetic_{file.filename}",
            **rate_headers
        }
    )

@app.post("/analyze")
async def analyze_synthetic_data(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    rows: int = 1000,
    method: str = "GaussianCopula",
    user: User = Depends(rate_limit_dependency)
):
    """
    Analyze the quality and privacy of synthetic data.

    **This endpoint is PROTECTED and requires authentication.**

    **What This Endpoint Does:**
    1. Generates synthetic data from your uploaded CSV
    2. Compares statistical properties (means, stds, correlations)
    3. Calculates privacy metrics (DCR - Distance to Closest Record)
    4. Returns comprehensive quality report

    **Quality Metrics:**
    - **Statistical Similarity**: How well synthetic data matches original distributions
    - **Privacy Score (DCR)**: Measures risk of re-identification
    - **Correlation Preservation**: How well relationships between variables are maintained

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/analyze" \\
         -H "Authorization: Bearer $TOKEN" \\
         -F "file=@patient_data.csv" \\
         -F "method=CTGAN"
    ```

    **Example Response:**
    ```json
    {
        "filename": "patient_data.csv",
        "original_rows": 500,
        "synthetic_rows": 500,
        "method": "CTGAN",
        "user": "researcher1",
        "stats": {
            "mean_difference": 0.02,
            "correlation_difference": 0.05
        },
        "privacy": {
            "mean_dcr": 0.87,
            "min_dcr": 0.45,
            "privacy_level": "High"
        }
    }
    ```

    Args:
        file: CSV file containing training data
        rows: Number of synthetic rows to generate (default: 1000)
        method: Synthesis method (GaussianCopula, TVAE, or CTGAN)
        user: Authenticated user (injected by dependency)

    Returns:
        JSON quality report with statistics and privacy metrics
    """
    # Add rate limit headers to response
    endpoint = request.url.path
    rate_headers = rate_limiter.get_rate_limit_headers(user, endpoint)
    for key, value in rate_headers.items():
        response.headers[key] = value

    # Validate file format
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    # Validate method
    if method not in ["GaussianCopula", "TVAE", "CTGAN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid method. Supported: GaussianCopula, TVAE, CTGAN"
        )

    # Read uploaded file
    content = await file.read()
    data = pd.read_csv(StringIO(content.decode('utf-8')))

    # Clean the data
    loader = DataLoader()
    cleaned_data = loader.clean_data(data)

    # Generate synthetic data
    generator = SyntheticGenerator(method=method)
    generator.train(cleaned_data)
    synthetic_data = generator.generate(rows=len(cleaned_data))

    # Analyze quality
    analyzer = QualityReport()
    report = analyzer.analyze(cleaned_data, synthetic_data)

    # Audit log
    print(f"[AUDIT] User: {user.username}, Action: analyze, Method: {method}, File: {file.filename}")

    return {
        "filename": file.filename,
        "original_rows": len(cleaned_data),
        "synthetic_rows": len(synthetic_data),
        "method": method,
        "user": user.username,
        "stats": report.compare_stats(),
        "privacy": report.check_privacy(),
        "rate_limit": rate_headers
    }
