# PantryPilot Environment Quick Reference

## 🚀 Quick Start

### Production Server
```bash
python run.py
```
- 🌐 URL: **http://localhost:8000**
- 💾 Database: `data/pantrypilot.db`
- 📊 Items: ~165
- ⚠️ **Use for**: Real user operations ONLY

### Staging Server
```bash
python run_staging.py
```
- 🌐 URL: **http://localhost:8001**
- 💾 Database: `data/pantrypilot_staging.db`
- 📊 Items: ~146
- ✅ **Use for**: Testing, development, experimentation

---

## 🔍 How to Verify Environment

### Check Console Output
**Production**:
```
[Database] Environment: PROD | Database: sqlite:///.../data/pantrypilot.db
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Staging**:
```
============================================================
PantryPilot - STAGING Environment
============================================================

[WARNING] Running in STAGING mode
Database: data/pantrypilot_staging.db
Port: 8001 (staging)

[Database] Environment: STAGING | Database: sqlite:///.../data/pantrypilot_staging.db
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### Check Browser URL
- **http://localhost:8000** → Production ⚠️
- **http://localhost:8001** → Staging ✅

### Check Item Count
```bash
# Production (should be ~165)
curl -s "http://localhost:8000/api/inventory/items?limit=1000" | python -c "import sys, json; print(len(json.load(sys.stdin)))"

# Staging (should be ~146)
curl -s "http://localhost:8001/api/inventory/items?limit=1000" | python -c "import sys, json; print(len(json.load(sys.stdin)))"
```

---

## 📋 Environment Comparison

| Aspect | Production | Staging |
|--------|-----------|---------|
| **Command** | `python run.py` | `python run_staging.py` |
| **Port** | 8000 | 8001 |
| **URL** | http://localhost:8000 | http://localhost:8001 |
| **Database** | `data/pantrypilot.db` | `data/pantrypilot_staging.db` |
| **Deletion Log** | `logs/item_deletions.log` | `logs/item_deletions_staging.log` |
| **Items** | ~165 | ~146 |
| **Purpose** | Real user data | Testing/development |
| **Data Safety** | CRITICAL - Real data | Safe to modify |
| **Console Banner** | None | "STAGING Environment" |
| **Log Format** | `[PROD] - ...` | `[STAGING] - ...` |

---

## ✅ When to Use Each Environment

### Use Production (Port 8000)
- ✅ Viewing real user data (read-only)
- ✅ Final verification before deployment
- ✅ User-facing operations
- ❌ **NEVER** for testing new features
- ❌ **NEVER** for importing test data
- ❌ **NEVER** for experimentation

### Use Staging (Port 8001)
- ✅ Feature development
- ✅ Testing new imports (CSV, receipts, OCR)
- ✅ Experimenting with inventory changes
- ✅ Testing responsive design
- ✅ Testing autocomplete cache
- ✅ Any risky operations
- ✅ Breaking things without consequences

---

## 🔧 Running Both Simultaneously

You can run both servers at the same time for comparison:

```bash
# Terminal 1 - Production
python run.py
# → http://localhost:8000

# Terminal 2 - Staging
python run_staging.py
# → http://localhost:8001
```

**Use case**: Compare production vs staging side-by-side

---

## 🛡️ Safety Rules

### 🚨 NEVER
1. ❌ Write test data to production database
2. ❌ Test risky features on port 8000
3. ❌ Import experimental data to production
4. ❌ Delete items from production for testing

### ✅ ALWAYS
1. ✅ Use staging (port 8001) for all development
2. ✅ Verify port number before operations
3. ✅ Check console for environment banner
4. ✅ Test thoroughly in staging before production

---

## 🐛 Common Issues

### Issue: "I see 165 items in staging"
**Problem**: You're accessing the wrong port
**Solution**: Make sure you're visiting **http://localhost:8001**, not 8000

### Issue: "Both servers show same data"
**Problem**: Both servers running on same port (port conflict)
**Solution**: Kill old server, start fresh. Production = 8000, Staging = 8001

### Issue: "Can't connect to staging"
**Problem**: Staging server not running or wrong port
**Solution**:
1. Run `python run_staging.py`
2. Look for "Uvicorn running on http://0.0.0.0:8001"
3. Access http://localhost:8001

---

## 📊 File Locations

```
homestead_asset_management_system/
├── data/
│   ├── pantrypilot.db          ← Production database (165 items) ⚠️
│   └── pantrypilot_staging.db  ← Staging database (146 items) ✅
├── logs/
│   ├── item_deletions.log           ← Production deletion log ⚠️
│   └── item_deletions_staging.log   ← Staging deletion log ✅
├── run.py                      ← Production server
└── run_staging.py              ← Staging server
```

### View Deletion Logs

```bash
# Production deletions (real user operations)
tail -f logs/item_deletions.log

# Staging deletions (test operations)
tail -f logs/item_deletions_staging.log

# Count deletions
grep -c "删除物品" logs/item_deletions.log          # Production count
grep -c "删除物品" logs/item_deletions_staging.log  # Staging count
```

---

## 🔄 Sync Staging from Production

If you want to refresh staging with production data:

```bash
# Backup current staging
cp data/pantrypilot_staging.db data/pantrypilot_staging.db.backup

# Copy production to staging
cp data/pantrypilot.db data/pantrypilot_staging.db

# Verify
python -c "import os; os.environ['ENVIRONMENT'] = 'staging'; from app.database import engine; from sqlmodel import Session, select; from app.models import Item; session = Session(engine); print(f'Staging now has {len(session.exec(select(Item)).all())} items')"
```

---

## 📞 Quick Help

### Check which database a running server is using
```bash
# Production
curl -s http://localhost:8000/api/inventory/items?limit=1 | python -m json.tool

# Staging
curl -s http://localhost:8001/api/inventory/items?limit=1 | python -m json.tool
```

### Stop all servers
```bash
# Ctrl+C in each terminal running the servers
# Or kill the processes:
# Windows: taskkill /F /IM python.exe
# Linux/Mac: pkill -f "python run"
```

---

## 📚 Related Documentation

- `docs/BUGFIX_STAGING_PORT.md` - Detailed explanation of port separation fix
- `docs/STAGING_VERIFICATION.md` - Environment verification report
- `CLAUDE.md` - Complete development guidelines
- `README.md` - Project overview

---

**Last Updated**: 2025-12-05
**Port Separation Implemented**: 2025-12-05
