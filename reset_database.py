"""
Reset Database Script

This script will delete the database and recreate it fresh.
Useful when you want to start over or fix duplicate imports.
"""
import os
from pathlib import Path

# Database file location
DB_PATH = Path(__file__).parent / "data" / "pantrypilot.db"

def reset_database():
    """Delete the database file to start fresh."""
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"✓ Database deleted: {DB_PATH}")
        print("✓ A new database will be created when you start the server.")
        print("\nNext steps:")
        print("1. Run: python run.py")
        print("2. Navigate to http://localhost:8000/import")
        print("3. Click 'Import Sample Data Now' to load fresh data")
    else:
        print(f"✗ Database not found at: {DB_PATH}")
        print("No action needed - database doesn't exist yet.")

if __name__ == "__main__":
    confirm = input("This will DELETE all inventory data. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")
