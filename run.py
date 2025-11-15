"""
PantryPilot - Production Start Script

Run this script to start PantryPilot in PRODUCTION mode.
Uses: data/pantrypilot.db
"""
import os
import uvicorn

# Set environment to production explicitly
os.environ['ENVIRONMENT'] = 'prod'

if __name__ == "__main__":
    print("=" * 60)
    print("PantryPilot - PRODUCTION Environment")
    print("=" * 60)
    print("\n✓ Running in PRODUCTION mode")
    print("Database: data/pantrypilot.db")
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
