# Test Environment Setup Guide

## Overview

PantryPilot uses **environment-based database separation** to prevent test data from polluting production. There are three distinct environments, each with its own database.

## Environment Overview

| Environment | Database File | Purpose | Start Command |
|-------------|--------------|---------|---------------|
| **Production** | `data/pantrypilot.db` | Real data, live usage | `python run.py` or `start_production.bat` |
| **Staging** | `data/pantrypilot_staging.db` | Testing, experiments | `python run_staging.py` or `start_staging.bat` |
| **Test** | `data/pantrypilot_test.db` | Unit tests, CI/CD | Set `ENVIRONMENT=test` |

## Quick Start

### Running in Different Environments

**Production (default):**
```bash
python run.py
# or double-click: start_production.bat
```

**Staging (for testing):**
```bash
python run_staging.py
# or double-click: start_staging.bat
```

**Test (for unit tests):**
```bash
set ENVIRONMENT=test
python your_test_script.py
```

## How It Works

The `app/database.py` module automatically selects the database based on the `ENVIRONMENT` variable:

```python
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod')  # Default: prod

DB_FILES = {
    'prod': 'pantrypilot.db',
    'staging': 'pantrypilot_staging.db',
    'test': 'pantrypilot_test.db'
}
```

## Testing Workflow

### ⚠️ IMPORTANT: Always Test in Staging

**Before testing new features:**
1. Start staging environment: `python run_staging.py`
2. Test your features
3. Verify everything works
4. Only then use production

### Cleanup Staging Database

To reset staging database:

```bash
# Windows
del data\pantrypilot_staging.db

# Linux/Mac
rm data/pantrypilot_staging.db
```

Then restart staging to get a fresh database.

## Best Practices

1. **Never run tests against production database**
2. **Use descriptive test data** that's clearly identifiable as test data
3. **Clean up after tests** - either delete test DB or use transactions with rollback
4. **Document test scenarios** in your test files
5. **Use fixtures** for consistent test data setup

## Example: Testing in Staging

**Most common testing scenario:**

1. Start staging server:
   ```bash
   python run_staging.py
   ```

2. Test your features in the browser:
   - Open: http://localhost:8000/inventory
   - Test adding/editing/deleting items
   - All changes go to `data/pantrypilot_staging.db`

3. If needed, reset staging:
   ```bash
   # Stop server (Ctrl+C)
   del data\pantrypilot_staging.db
   # Restart staging
   python run_staging.py
   ```

## Example: Automated Test Script

For automated tests (e.g., API testing):

```python
"""
Test script using staging environment.
"""
import os

# Set to staging BEFORE importing app
os.environ['ENVIRONMENT'] = 'staging'

import requests

BASE_URL = "http://localhost:8000/api"

def test_multi_item_creation():
    """Test creating multiple items."""
    response = requests.post(
        f"{BASE_URL}/inventory/items",
        json={
            "name": "Test Item 1, Test Item 2",
            "category": "Test",
            "quantity": 1,
            "unit": "count",
            "location_path": "Test Location"
        }
    )
    assert response.status_code == 200
    result = response.json()
    print(f"Created {result['count']} items")

if __name__ == "__main__":
    print("⚠️  Running tests in STAGING environment")
    test_multi_item_creation()
```

## Testing with Running Server

If you need to test against a running server:

1. **Start server with test database:**
   ```bash
   set DATABASE_URL=sqlite:///data/pantrypilot_test.db
   python run.py
   ```

2. **Run your API tests:**
   ```bash
   python test_api_features.py
   ```

3. **Stop server and cleanup:**
   ```bash
   # Ctrl+C to stop server
   del data\pantrypilot_test.db
   ```

## Database Migration for Tests

If you need to migrate test database schema:

```bash
set DATABASE_URL=sqlite:///data/pantrypilot_test.db
alembic upgrade head
```

## Continuous Integration

For CI/CD pipelines, always set `DATABASE_URL` to test database in your CI configuration:

```yaml
# Example .github/workflows/test.yml
env:
  DATABASE_URL: sqlite:///data/pantrypilot_test.db

steps:
  - name: Run tests
    run: |
      python -m pytest tests/
```

## Summary

✅ **Always** use `data/pantrypilot_test.db` for testing
✅ **Set** `DATABASE_URL` environment variable before importing app modules
✅ **Clean up** test database after testing
❌ **Never** write test data to production database (`data/pantrypilot.db`)
