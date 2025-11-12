"""
PantryPilot - Quick Start Script

Run this script to start the PantryPilot application.
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("PantryPilot - Household Asset Management System")
    print("=" * 60)
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
