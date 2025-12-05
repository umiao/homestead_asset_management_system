"""PantryPilot - Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

from .database import create_db_and_tables
from .routers import inventory, import_data, receipt_ocr, autocomplete

# Create FastAPI app
app = FastAPI(
    title="PantryPilot",
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
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    """Inventory management page."""
    return templates.TemplateResponse("inventory.html", {"request": request})


@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Import data page."""
    return templates.TemplateResponse("import.html", {"request": request})


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alerts and expiration page."""
    return templates.TemplateResponse("alerts.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PantryPilot"}
