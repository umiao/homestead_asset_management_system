"""
PantryPilot - Staging Environment

Run this script to start PantryPilot in STAGING mode.
Uses: data/pantrypilot_staging.db

IMPORTANT: This runs on port 8001 (different from production port 8000)
to avoid conflicts and ensure proper environment isolation.
"""
import os
import sys
import io
import uvicorn

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# CRITICAL: Set environment to staging BEFORE importing app
# Environment variables set here ARE inherited by uvicorn's reload subprocess
os.environ['ENVIRONMENT'] = 'staging'

if __name__ == "__main__":
    print("=" * 60)
    print("PantryPilot - STAGING Environment")
    print("=" * 60)
    print("\n[WARNING] Running in STAGING mode")
    print("Database: data/pantrypilot_staging.db")
    print("Port: 8001 (staging)")
    print("\nStarting server...")
    print("URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # Different port for staging
        reload=True,
        log_level="info"
    )
