"""家庭资产盘存系统 - Main FastAPI application."""
from fastapi import FastAPI, Request, Form, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pathlib import Path
import json

from .database import create_db_and_tables
from .routers import inventory, import_data, receipt_ocr, autocomplete
from .auth import authenticate_user, create_session_cookie, get_current_user, get_current_user_or_redirect, get_optional_user

# Create FastAPI app
app = FastAPI(
    title="家庭资产盘存系统",
    description="Household Asset Management System",
    version="1.0.0"
)

# Add middleware to ensure UTF-8 encoding
@app.middleware("http")
async def add_utf8_header(request: Request, call_next):
    response = await call_next(request)
    # Ensure UTF-8 encoding for all responses
    if "content-type" in response.headers:
        content_type = response.headers["content-type"]
        if "charset" not in content_type:
            if "application/json" in content_type:
                response.headers["content-type"] = "application/json; charset=utf-8"
            elif "text/html" in content_type:
                response.headers["content-type"] = "text/html; charset=utf-8"
    return response

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Include routers
app.include_router(inventory.router)
app.include_router(import_data.router)
app.include_router(receipt_ocr.router)
app.include_router(autocomplete.router)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(get_current_user_or_redirect)):
    """Home page - requires authentication."""
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request, user: dict = Depends(get_current_user_or_redirect)):
    """Inventory management page - requires authentication."""
    return templates.TemplateResponse("inventory.html", {"request": request, "user": user})


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request, user: dict = Depends(get_current_user_or_redirect)):
    """Import data page - requires authentication."""
    return templates.TemplateResponse("import.html", {"request": request, "user": user})


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request, user: dict = Depends(get_current_user_or_redirect)):
    """Alerts and expiration page - requires authentication."""
    return templates.TemplateResponse("alerts.html", {"request": request, "user": user})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "家庭资产盘存系统"}


# HTTP Basic security for login
security = HTTPBasic()


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    """
    Display login page.

    Args:
        next: URL to redirect to after successful login
    """
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next
    })


@app.post("/login")
async def login_submit(
    response: Response,
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/")
):
    """
    Process login form submission.

    On success, sets a signed session cookie and redirects to the intended page.
    On failure, shows login page with error message.
    """
    # Authenticate user
    user = authenticate_user(username, password)

    if not user:
        # Return login page with error
        return templates.TemplateResponse("login.html", {
            "request": request,
            "next": next,
            "error": "Invalid username or password"
        }, status_code=401)

    # Create session cookie
    cookie_config = create_session_cookie(username)

    # Create redirect response
    redirect_response = RedirectResponse(url=next, status_code=303)
    redirect_response.set_cookie(**cookie_config)

    return redirect_response


@app.get("/logout")
async def logout():
    """
    Logout endpoint.
    Clears session cookie and redirects to login page.
    """
    # Create redirect response
    response = RedirectResponse(url="/login", status_code=303)

    # Delete session cookie with all the same parameters as when it was set
    response.delete_cookie(
        key="session_token",
        path="/",
        domain=None,
        secure=True,
        httponly=True,
        samesite="lax"
    )

    return response


@app.get("/auth/status")
async def auth_status(user: dict = Depends(get_optional_user)):
    """
    Check authentication status.
    Returns user info if logged in, null otherwise.
    """
    if not user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
            "permissions": user["permissions"]
        }
    }
