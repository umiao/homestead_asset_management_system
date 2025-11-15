"""
PantryPilot - Staging Environment

Run this script to start PantryPilot in STAGING mode.
Uses: data/pantrypilot_staging.db
"""
import os
import sys
import io
import uvicorn

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set environment to staging BEFORE importing app
os.environ['ENVIRONMENT'] = 'staging'

if __name__ == "__main__":
    print("=" * 60)
    print("PantryPilot - STAGING Environment")
    print("=" * 60)
    print("\n⚠️  Running in STAGING mode")
    print("Database: data/pantrypilot_staging.db")
    print("\nStarting server...")
    print("URL: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
