"""Database connection and session management."""
import os
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database file location
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

# Environment-based database selection
# ENVIRONMENT can be: prod, staging, or test
# Default to production if not specified
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod').lower()

# Database mapping
DB_FILES = {
    'prod': 'pantrypilot.db',           # Production database
    'staging': 'pantrypilot_staging.db', # Staging/testing database
    'test': 'pantrypilot_test.db'        # Unit test database
}

# Get database file based on environment
db_file = DB_FILES.get(ENVIRONMENT, DB_FILES['prod'])

# Allow override with DATABASE_URL env var (for advanced usage)
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    f"sqlite:///{DB_DIR}/{db_file}"
)

# Log which database is being used (for clarity)
print(f"[Database] Environment: {ENVIRONMENT.upper()} | Database: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False}  # Needed for SQLite
)


def create_db_and_tables():
    """Create database tables."""
    # Import models to ensure they're registered with SQLModel
    from app.models import Household, Location, Item, Event
    from app.services.autocomplete_cache import AutocompleteCache

    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
