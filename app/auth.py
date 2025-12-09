"""
Authentication and Authorization Module

Security features:
- Salted SHA-256 password hashing (salt = SHA-256(username))
  * Client: SHA-256(password + SHA-256(username))
  * Server: SHA-256(stored_password + SHA-256(username))
  * Prevents rainbow table attacks and ensures unique hashes per user
- Signed session cookies (itsdangerous)
- HTTPS-only cookies (secure flag)
- HTTP-only cookies (XSS protection)
- Constant-time hash comparison (timing attack protection)
- Role-based access control (admin/viewer)
- Long-term sessions (365 days, logout required to end session)
"""
import os
import hashlib
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Cookie, HTTPException, status, Response, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()

# HTTP Basic Auth security (legacy, not used with current implementation)
security = HTTPBasic()

# Session serializer for signed cookies
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-THIS-TO-RANDOM-SECRET-KEY")
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
serializer = Serializer(SECRET_KEY, expires_in=SESSION_EXPIRY_HOURS * 3600)

# User configuration
# Passwords are stored in plain text in .env
# Salted hashing process:
#   1. salt = SHA-256(username)
#   2. Client sends: SHA-256(password + salt)
#   3. Server computes: SHA-256(stored_password + salt)
#   4. Compare using constant-time algorithm
# This ensures different users with same password get different hashes
USERS = {
    os.getenv("ADMIN_USERNAME", "admin"): {
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin",
        "permissions": ["read", "write", "delete", "import"],
        "display_name": "Administrator"
    },
    os.getenv("VIEWER_USERNAME", "viewer"): {
        "password": os.getenv("VIEWER_PASSWORD", "viewer123"),
        "role": "viewer",
        "permissions": ["read"],
        "display_name": "Viewer"
    }
}


def sha256_hash(text: str) -> str:
    """
    Compute SHA-256 hash of text.

    Args:
        text: Plain text to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_salted_password_hash(username: str, password: str) -> str:
    """
    Compute salted password hash using username as salt.

    Process:
    1. salt = SHA-256(username)
    2. salted_password = password + salt
    3. final_hash = SHA-256(salted_password)

    This ensures:
    - Same password for different users produces different hashes
    - Username acts as a deterministic salt
    - No need to store salt separately

    Args:
        username: Username (used as salt base)
        password: Plain text password

    Returns:
        Final salted hash (hexadecimal)
    """
    # Step 1: Create salt from username
    salt = sha256_hash(username)

    # Step 2: Combine password with salt
    salted_password = password + salt

    # Step 3: Hash the salted password
    final_hash = sha256_hash(salted_password)

    return final_hash


def create_session_token(username: str) -> str:
    """
    Create a signed session token.

    Args:
        username: Username to encode in token

    Returns:
        Signed token string
    """
    payload = {
        "username": username,
        "created_at": datetime.utcnow().isoformat()
    }
    return serializer.dumps(payload).decode('utf-8')


def verify_session_token(token: str) -> Optional[dict]:
    """
    Verify and decode session token.

    Args:
        token: Signed token string

    Returns:
        Decoded payload dict if valid, None otherwise
    """
    try:
        payload = serializer.loads(token)
        return payload
    except (SignatureExpired, BadSignature):
        return None


def authenticate_user(username: str, password_hash: str) -> Optional[dict]:
    """
    Authenticate user with username and salted password hash.

    The client sends SHA-256(password + SHA-256(username)), and we
    compute the same for the stored password and compare.

    Process:
    - Client: SHA-256(password + SHA-256(username))
    - Server: SHA-256(stored_password + SHA-256(username))
    - Compare with constant-time algorithm

    Args:
        username: Username (also used as salt base)
        password_hash: Salted password hash from client

    Returns:
        User dict if authenticated, None otherwise
    """
    user = USERS.get(username)
    if not user:
        return None

    # Compute expected salted hash from stored password
    expected_hash = compute_salted_password_hash(username, user["password"])

    # Compare hashes using constant-time comparison (timing attack protection)
    import secrets
    if not secrets.compare_digest(password_hash, expected_hash):
        return None

    return {"username": username, **user}


async def get_current_user(session: Optional[str] = Cookie(None, alias="session_token")) -> dict:
    """
    Get current authenticated user from session cookie.

    Args:
        session: Session token from cookie

    Returns:
        User dict

    Raises:
        HTTPException: If not authenticated
    """
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Verify session token
    payload = verify_session_token(session)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Get user from payload
    username = payload.get("username")
    user = USERS.get(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please log in again.",
        )

    return {"username": username, **user}


def require_permission(permission: str):
    """
    Dependency to require specific permission.

    Args:
        permission: Required permission (e.g., "write", "delete", "import")

    Returns:
        Dependency function
    """
    async def permission_checker(user: dict = Depends(get_current_user)) -> dict:
        if permission not in user["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required. Your role: {user['role']}"
            )
        return user
    return permission_checker


async def get_optional_user(session: Optional[str] = Cookie(None, alias="session_token")) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    Useful for pages that work differently for logged-in vs anonymous users.

    Args:
        session: Session token from cookie

    Returns:
        User dict if authenticated, None otherwise
    """
    if not session:
        return None

    payload = verify_session_token(session)
    if not payload:
        return None

    username = payload.get("username")
    user = USERS.get(username)

    if not user:
        return None

    return {"username": username, **user}


class RedirectToLogin(Exception):
    """Exception to trigger redirect to login page."""
    def __init__(self, return_url: str):
        self.return_url = return_url


async def get_current_user_or_redirect(
    request: Request,
    session: Optional[str] = Cookie(None, alias="session_token")
) -> dict:
    """
    Get current authenticated user or redirect to login page.
    Used for HTML page routes that should redirect to login.

    Args:
        request: FastAPI request object (to get current path)
        session: Session token from cookie

    Returns:
        User dict if authenticated

    Raises:
        HTTPException with 303 redirect
    """
    return_url = str(request.url.path)

    if not session:
        # Redirect to login with return URL
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={quote(return_url)}"}
        )

    # Verify session token
    payload = verify_session_token(session)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={quote(return_url)}"}
        )

    # Get user from payload
    username = payload.get("username")
    user = USERS.get(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={quote(return_url)}"}
        )

    return {"username": username, **user}


def create_session_cookie(username: str) -> dict:
    """
    Create session cookie configuration.

    Args:
        username: Username to create session for

    Returns:
        Dict with cookie key and value
    """
    token = create_session_token(username)

    # Cookie settings
    # httponly=True: Prevents JavaScript access (XSS protection)
    # secure=True: Only sent over HTTPS (ngrok HTTPS)
    # samesite="lax": CSRF protection
    # max_age: Cookie expiry in seconds
    # path="/": Cookie available for all paths
    return {
        "key": "session_token",
        "value": token,
        "path": "/",
        "httponly": True,
        "secure": True,  # ngrok HTTPS
        "samesite": "lax",
        "max_age": SESSION_EXPIRY_HOURS * 3600
    }


# Export commonly used dependencies
__all__ = [
    "get_current_user",
    "get_current_user_or_redirect",
    "require_permission",
    "get_optional_user",
    "authenticate_user",
    "create_session_cookie",
    "USERS"
]
