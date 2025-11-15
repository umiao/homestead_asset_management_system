# PantryPilot - Environment Guide

## Quick Reference

| What you want to do | Command | Database |
|---------------------|---------|----------|
| **Use the app normally** | `python run.py` | `data/pantrypilot.db` |
| **Test new features** | `python run_staging.py` | `data/pantrypilot_staging.db` |
| **Run unit tests** | Set `ENVIRONMENT=test` | `data/pantrypilot_test.db` |

## Windows Quick Start

### Production (Real Data)
```cmd
start_production.bat
```
or
```cmd
python run.py
```

### Staging (Testing)
```cmd
start_staging.bat
```
or
```cmd
python run_staging.py
```

## Environment Separation

PantryPilot uses **three separate databases** to prevent test data from mixing with real data:

### 1. Production Environment 🏭
- **Database:** `data/pantrypilot.db`
- **Purpose:** Your real household inventory data
- **Start:** `python run.py`
- **When to use:** Normal daily usage

### 2. Staging Environment 🧪
- **Database:** `data/pantrypilot_staging.db`
- **Purpose:** Testing new features, experiments
- **Start:** `python run_staging.py`
- **When to use:**
  - Before trying new functionality
  - Testing comma-separated item creation
  - Experimenting with UI changes
  - Any testing that creates/modifies data

### 3. Test Environment 🔬
- **Database:** `data/pantrypilot_test.db`
- **Purpose:** Automated tests, CI/CD
- **Start:** Set `ENVIRONMENT=test` before running tests
- **When to use:** Running automated test suites

## How to Tell Which Environment You're In

When you start the server, you'll see:

**Production:**
```
============================================================
PantryPilot - PRODUCTION Environment
============================================================
✓ Running in PRODUCTION mode
Database: data/pantrypilot.db
```

**Staging:**
```
============================================================
PantryPilot - STAGING Environment
============================================================
⚠️  Running in STAGING mode
Database: data/pantrypilot_staging.db
```

## Important Rules

✅ **DO:**
- Use staging for all testing and experiments
- Reset staging database when needed
- Keep production clean and organized

❌ **DON'T:**
- Create test data in production
- Mix real data with test data
- Delete production database unless backing up

## Resetting Databases

### Reset Staging (Safe)
```cmd
REM Stop the server first (Ctrl+C)
del data\pantrypilot_staging.db
python run_staging.py
```

### Reset Test (Safe)
```cmd
del data\pantrypilot_test.db
```

### Reset Production (⚠️ DANGER)
```cmd
REM Only do this if you're sure!
REM Consider backing up first:
copy data\pantrypilot.db data\pantrypilot_backup.db
del data\pantrypilot.db
python run.py
```

## Technical Details

The environment is controlled by the `ENVIRONMENT` variable in `app/database.py`:

```python
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod')

DB_FILES = {
    'prod': 'pantrypilot.db',
    'staging': 'pantrypilot_staging.db',
    'test': 'pantrypilot_test.db'
}
```

Both `run.py` and `run_staging.py` automatically set this variable before starting the server.

## More Information

For detailed testing guidelines, see [TEST_SETUP.md](TEST_SETUP.md)
