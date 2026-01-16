"""
API Authentication & Rate Limiting Module for SynthLab

This module provides secure authentication and rate limiting for the SynthLab API:
- JWT (JSON Web Token) based authentication
- API key validation
- Role-based access control (RBAC)
- Rate limiting to prevent abuse
- Token expiration and refresh mechanisms

Author: SynthLab Development Team
Created: 2026-01-12
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from pathlib import Path

# Security configuration
SECRET_KEY = os.getenv("SYNTHLAB_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing - using argon2 (winner of Password Hashing Competition)
# More secure and modern than bcrypt, no 72-byte limitation
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # argon2 preferred, bcrypt for backwards compatibility
    deprecated="auto"
)

# HTTP Bearer token scheme
security = HTTPBearer()


class User:
    """
    User model representing an API user with credentials and permissions.

    Attributes:
        username: Unique identifier for the user
        email: User's email address
        hashed_password: Bcrypt-hashed password
        disabled: Whether the account is active
        role: User role (admin, researcher, viewer)
        api_key: Optional API key for programmatic access
        rate_limit: Custom rate limit (requests per minute)
    """

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        disabled: bool = False,
        role: str = "researcher",
        api_key: Optional[str] = None,
        rate_limit: int = 10
    ):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.disabled = disabled
        self.role = role
        self.api_key = api_key or self._generate_api_key()
        self.rate_limit = rate_limit

    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        return f"sk_{secrets.token_urlsafe(32)}"

    def to_dict(self) -> Dict:
        """Convert user to dictionary."""
        return {
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "disabled": self.disabled,
            "role": self.role,
            "api_key": self.api_key,
            "rate_limit": self.rate_limit
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Create user from dictionary."""
        return cls(**data)


class UserDatabase:
    """
    Simple file-based user database for storing credentials.

    In production, this should be replaced with a proper database (PostgreSQL, MongoDB, etc.).
    For development/academic use, this JSON-based approach is sufficient.

    Storage format:
    {
        "username1": {
            "email": "...",
            "hashed_password": "...",
            "role": "...",
            ...
        }
    }
    """

    def __init__(self, db_path: str = "data/users.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database with default admin user if empty."""
        if not self.db_path.exists():
            # Create default admin user
            admin = User(
                username="admin",
                email="admin@synthlab.local",
                hashed_password=pwd_context.hash("changeme123"),  # Default password
                role="admin",
                rate_limit=100  # Higher limit for admin
            )
            self._save_db({"admin": admin.to_dict()})
            print(f"[SECURITY] Created default admin user. Username: 'admin', Password: 'changeme123'")
            print(f"[SECURITY] Please change the default password immediately!")

    def _load_db(self) -> Dict:
        """Load user database from disk."""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_db(self, data: Dict):
        """Save user database to disk."""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_user(self, username: str) -> Optional[User]:
        """Retrieve user by username."""
        db = self._load_db()
        user_data = db.get(username)
        if user_data:
            return User.from_dict(user_data)
        return None

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Retrieve user by API key."""
        db = self._load_db()
        for username, user_data in db.items():
            if user_data.get("api_key") == api_key:
                return User.from_dict(user_data)
        return None

    def create_user(self, user: User) -> bool:
        """Create new user. Returns True if successful, False if user exists."""
        db = self._load_db()
        if user.username in db:
            return False
        db[user.username] = user.to_dict()
        self._save_db(db)
        return True

    def update_user(self, user: User) -> bool:
        """Update existing user."""
        db = self._load_db()
        if user.username not in db:
            return False
        db[user.username] = user.to_dict()
        self._save_db(db)
        return True

    def delete_user(self, username: str) -> bool:
        """Delete user by username."""
        db = self._load_db()
        if username in db:
            del db[username]
            self._save_db(db)
            return True
        return False


class AuthenticationManager:
    """
    Handles JWT token creation, validation, and user authentication.

    Security features:
    - Password hashing with bcrypt (12 rounds by default)
    - JWT tokens with expiration
    - Token-based authentication for stateless API
    - API key authentication for programmatic access
    """

    def __init__(self):
        self.user_db = UserDatabase()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash password using argon2."""
        return pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Returns:
            User object if authentication succeeds, None otherwise
        """
        user = self.user_db.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if user.disabled:
            return None
        return user

    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """
        Authenticate user with API key.

        Returns:
            User object if API key is valid, None otherwise
        """
        user = self.user_db.get_user_by_api_key(api_key)
        if user and not user.disabled:
            return user
        return None

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Token payload includes:
        - sub: Subject (username)
        - exp: Expiration time
        - iat: Issued at time
        - Additional custom claims (role, email, etc.)

        Args:
            data: Dictionary containing user claims
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, username: str) -> str:
        """Create long-lived refresh token."""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate JWT token.

        Raises:
            HTTPException: If token is invalid or expired

        Returns:
            Token payload as dictionary
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """
        Dependency to get current authenticated user from JWT token.

        This function is used as a FastAPI dependency in protected endpoints.

        Usage:
            @app.get("/protected")
            def protected_route(user: User = Depends(auth_manager.get_current_user)):
                return {"message": f"Hello {user.username}"}

        Raises:
            HTTPException: If token is invalid or user not found
        """
        token = credentials.credentials

        # Try JWT authentication first
        try:
            payload = self.decode_token(token)
            username = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            # If JWT fails, try API key authentication
            user = self.authenticate_api_key(token)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user

        # Get user from database
        user = self.user_db.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        return user

    def require_role(self, allowed_roles: List[str]):
        """
        Dependency factory for role-based access control.

        Usage:
            @app.delete("/admin/users/{username}")
            def delete_user(
                username: str,
                user: User = Depends(auth_manager.require_role(["admin"]))
            ):
                # Only admins can access this endpoint
                ...

        Args:
            allowed_roles: List of roles that can access the endpoint

        Returns:
            Dependency function that checks user role
        """
        def role_checker(user: User = Depends(self.get_current_user)) -> User:
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {allowed_roles}"
                )
            return user
        return role_checker


class RateLimiter:
    """
    In-memory rate limiter to prevent API abuse.

    Uses a sliding window algorithm:
    - Tracks requests per user per endpoint
    - Enforces per-user rate limits
    - Automatically cleans up old entries

    In production, use Redis-backed rate limiting for distributed systems.
    For single-instance academic use, in-memory is sufficient.
    """

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.cleanup_interval = 60  # Clean up every minute
        self.last_cleanup = datetime.utcnow()

    def _get_key(self, user: User, endpoint: str) -> str:
        """Generate unique key for user-endpoint combination."""
        return f"{user.username}:{endpoint}"

    def _cleanup_old_requests(self):
        """Remove requests older than 1 minute."""
        if (datetime.utcnow() - self.last_cleanup).seconds < self.cleanup_interval:
            return

        cutoff = datetime.utcnow() - timedelta(minutes=1)
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            if not self.requests[key]:
                del self.requests[key]

        self.last_cleanup = datetime.utcnow()

    def check_rate_limit(self, user: User, endpoint: str) -> bool:
        """
        Check if user has exceeded rate limit for endpoint.

        Args:
            user: User making the request
            endpoint: API endpoint being accessed

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        self._cleanup_old_requests()

        key = self._get_key(user, endpoint)
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Get requests in last minute
        if key not in self.requests:
            self.requests[key] = []

        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]

        # Check against limit
        if len(self.requests[key]) >= user.rate_limit:
            return False

        # Record this request
        self.requests[key].append(now)
        return True

    def get_rate_limit_headers(self, user: User, endpoint: str) -> Dict[str, str]:
        """
        Generate rate limit headers for response.

        Returns headers like:
        - X-RateLimit-Limit: 10
        - X-RateLimit-Remaining: 7
        - X-RateLimit-Reset: 1609459200
        """
        key = self._get_key(user, endpoint)
        remaining = user.rate_limit - len(self.requests.get(key, []))
        reset_time = int((datetime.utcnow() + timedelta(minutes=1)).timestamp())

        return {
            "X-RateLimit-Limit": str(user.rate_limit),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(reset_time)
        }


# Global instances
auth_manager = AuthenticationManager()
rate_limiter = RateLimiter()


def rate_limit_dependency(request: Request, user: User = Depends(auth_manager.get_current_user)) -> User:
    """
    FastAPI dependency for rate limiting.

    Usage:
        @app.post("/generate")
        def generate(user: User = Depends(rate_limit_dependency)):
            # User is already authenticated and rate-limited
            ...

    Raises:
        HTTPException: If rate limit is exceeded
    """
    endpoint = request.url.path

    if not rate_limiter.check_rate_limit(user, endpoint):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {user.rate_limit} requests/minute",
            headers=rate_limiter.get_rate_limit_headers(user, endpoint)
        )

    return user


if __name__ == "__main__":
    """
    Test authentication system.

    This creates a test user, generates tokens, and validates them.
    """
    print("=== SynthLab API Authentication System Test ===\n")

    # Initialize auth manager
    auth = AuthenticationManager()
    print("✓ Authentication manager initialized")
    print(f"✓ User database: {auth.user_db.db_path}")

    # Test default admin user
    admin = auth.user_db.get_user("admin")
    if admin:
        print(f"✓ Default admin user exists: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  API Key: {admin.api_key[:20]}...")
        print(f"  Rate Limit: {admin.rate_limit} req/min")

    # Test password authentication
    print("\n--- Testing Password Authentication ---")
    authenticated_user = auth.authenticate_user("admin", "changeme123")
    if authenticated_user:
        print(f"✓ Password authentication successful for: {authenticated_user.username}")
    else:
        print("✗ Password authentication failed")

    # Test wrong password
    wrong_auth = auth.authenticate_user("admin", "wrongpassword")
    if not wrong_auth:
        print("✓ Correctly rejected wrong password")

    # Test JWT token creation
    print("\n--- Testing JWT Token Generation ---")
    token_data = {
        "sub": admin.username,
        "email": admin.email,
        "role": admin.role
    }
    access_token = auth.create_access_token(token_data)
    print(f"✓ Access token generated ({len(access_token)} chars)")
    print(f"  Token preview: {access_token[:50]}...")

    # Test token decoding
    print("\n--- Testing Token Validation ---")
    try:
        payload = auth.decode_token(access_token)
        print("✓ Token decoded successfully")
        print(f"  Subject: {payload['sub']}")
        print(f"  Role: {payload['role']}")
        print(f"  Expires: {datetime.fromtimestamp(payload['exp'])}")
    except Exception as e:
        print(f"✗ Token decoding failed: {e}")

    # Test API key authentication
    print("\n--- Testing API Key Authentication ---")
    api_user = auth.authenticate_api_key(admin.api_key)
    if api_user:
        print(f"✓ API key authentication successful for: {api_user.username}")
    else:
        print("✗ API key authentication failed")

    # Test creating new user
    print("\n--- Testing User Creation ---")
    new_user = User(
        username="researcher1",
        email="researcher@university.edu",
        hashed_password=auth.hash_password("secure_password123"),
        role="researcher",
        rate_limit=10
    )
    created = auth.user_db.create_user(new_user)
    if created:
        print(f"✓ Created new user: {new_user.username}")
        print(f"  API Key: {new_user.api_key[:20]}...")

    # Test rate limiting
    print("\n--- Testing Rate Limiter ---")
    limiter = RateLimiter()
    test_endpoint = "/generate"

    # Make requests up to limit
    allowed_count = 0
    for i in range(admin.rate_limit + 5):
        if limiter.check_rate_limit(admin, test_endpoint):
            allowed_count += 1
        else:
            print(f"✓ Rate limit enforced after {allowed_count} requests")
            break

    # Check headers
    headers = limiter.get_rate_limit_headers(admin, test_endpoint)
    print(f"✓ Rate limit headers: {headers}")

    print("\n=== All Tests Complete ===")
    print(f"\n[IMPORTANT] Default credentials:")
    print(f"  Username: admin")
    print(f"  Password: changeme123")
    print(f"  API Key: {admin.api_key}")
    print(f"\n  Please change these credentials before deploying to production!")
