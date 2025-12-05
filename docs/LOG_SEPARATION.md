# Log File Environment Separation

## Overview

Deletion logs are now separated by environment to prevent staging test data from polluting production audit logs.

## Implementation Date
**2025-12-05**

## Log File Locations

### Production Environment
- **File**: `logs/item_deletions.log`
- **Server**: `run.py` (port 8000)
- **Database**: `data/pantrypilot.db`
- **Format**: `YYYY-MM-DD HH:MM:SS - [PROD] - INFO - 删除物品 | ...`

### Staging Environment
- **File**: `logs/item_deletions_staging.log`
- **Server**: `run_staging.py` (port 8001)
- **Database**: `data/pantrypilot_staging.db`
- **Format**: `YYYY-MM-DD HH:MM:SS - [STAGING] - INFO - 删除物品 | ...`

## Code Changes

### Modified File: `app/routers/inventory.py`

**Before**:
```python
# Setup logging for deletions
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
deletion_logger = logging.getLogger("inventory_deletions")
deletion_logger.setLevel(logging.INFO)

# Create file handler
log_file = os.path.join(log_dir, "item_deletions.log")  # ❌ Same for all environments
file_handler = logging.FileHandler(log_file, encoding='utf-8')

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',  # ❌ No environment indicator
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

**After**:
```python
from ..database import get_session, ENVIRONMENT  # ✅ Import environment

# Setup logging for deletions
# Environment-based log separation
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Use different log file based on environment
# Production: logs/item_deletions.log
# Staging: logs/item_deletions_staging.log
if ENVIRONMENT == 'staging':
    log_file = os.path.join(log_dir, "item_deletions_staging.log")  # ✅ Staging log
else:
    log_file = os.path.join(log_dir, "item_deletions.log")  # ✅ Production log

deletion_logger = logging.getLogger(f"inventory_deletions_{ENVIRONMENT}")  # ✅ Unique logger per env
deletion_logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create formatter - include environment in log messages
formatter = logging.Formatter(
    f'%(asctime)s - [{ENVIRONMENT.upper()}] - %(levelname)s - %(message)s',  # ✅ [PROD] or [STAGING]
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
deletion_logger.addHandler(file_handler)
```

## Benefits

### 1. Clear Audit Trail
- Production logs contain **only real user deletions**
- Staging logs contain **only test deletions**
- No confusion about which environment a deletion occurred in

### 2. Environment Identification
Each log entry now includes environment tag:
```
2025-12-05 14:30:00 - [PROD] - INFO - 删除物品 | ...
2025-12-05 14:31:00 - [STAGING] - INFO - 删除物品 | ...
```

### 3. Testing Safety
- Test deletions in staging don't pollute production audit logs
- Can delete test items freely without affecting production history
- Production log remains clean and authoritative

### 4. Compliance & Audit
- Production deletion log is the authoritative record
- Staging log is for development/testing reference only
- Clear separation for compliance requirements

## Log File Status

### Current Files
```bash
$ ls -la logs/*.log

-rw-r--r-- 1 user group 7510 Dec  3 22:56 logs/item_deletions.log           # Production (historical)
-rw-r--r-- 1 user group    0 Dec  5 14:30 logs/item_deletions_staging.log  # Staging (new)
```

### Production Log (`item_deletions.log`)
- **Size**: 7.5 KB
- **Last Modified**: Dec 3, 2025
- **Contains**: Real user deletion history
- **Format (old entries)**: `YYYY-MM-DD HH:MM:SS - INFO - 删除物品 | ...`
- **Format (new entries)**: `YYYY-MM-DD HH:MM:SS - [PROD] - INFO - 删除物品 | ...`

### Staging Log (`item_deletions_staging.log`)
- **Size**: 0 bytes (newly created)
- **Last Modified**: Dec 5, 2025
- **Contains**: Test deletion history only
- **Format**: `YYYY-MM-DD HH:MM:SS - [STAGING] - INFO - 删除物品 | ...`

## Example Log Entries

### Production Log Entry
```
2025-12-05 14:30:00 - [PROD] - INFO - 删除物品 | ID: 123 | 名称: 牛奶 | 类别: 食品 | 数量: 1.0 瓶 | 位置: 冰箱 > 冷藏 | 出库原因: 已消耗 / Consumed | 出库记录: 早餐饮用
```

### Staging Log Entry
```
2025-12-05 14:31:00 - [STAGING] - INFO - 删除物品 | ID: 456 | 名称: 测试商品 | 类别: 测试 | 数量: 99.0 个 | 位置: 测试位置 | 出库原因: 测试删除 / Test deletion | 出库记录: 开发测试
```

## Verification

### Check Which Log File is Active
```bash
# Production server console
# Will see: logs/item_deletions.log being used

# Staging server console
# Will see: logs/item_deletions_staging.log being used
```

### View Production Deletions
```bash
tail -f logs/item_deletions.log
```

### View Staging Deletions
```bash
tail -f logs/item_deletions_staging.log
```

### Count Deletions by Environment
```bash
# Production
grep -c "删除物品" logs/item_deletions.log

# Staging
grep -c "删除物品" logs/item_deletions_staging.log
```

## Migration Notes

### Historical Data
- **Production log** (`item_deletions.log`) contains historical entries without `[PROD]` tag
- New entries will have `[PROD]` tag
- This is **intentional** - historical entries are still valid

### Backward Compatibility
- Old log entries without environment tag → production environment
- New log entries with `[PROD]` or `[STAGING]` tag → explicitly marked
- Both formats are valid and parseable

## Log Rotation (Future Enhancement)

**TODO**: Implement log rotation to prevent files from growing too large

Suggested configuration:
- **Max file size**: 10 MB
- **Backup count**: 5 files
- **Naming**: `item_deletions.log`, `item_deletions.log.1`, `item_deletions.log.2`, etc.
- **Staging**: `item_deletions_staging.log`, `item_deletions_staging.log.1`, etc.

Example with Python's `RotatingFileHandler`:
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
```

## Related Documentation

- `ENVIRONMENT_GUIDE.md` - Environment separation overview
- `docs/BUGFIX_STAGING_PORT.md` - Port separation for environments
- `CLAUDE.md` - Development guidelines

## Summary

✅ **Production logs**: `logs/item_deletions.log` (real deletions only)
✅ **Staging logs**: `logs/item_deletions_staging.log` (test deletions only)
✅ **Environment tag**: `[PROD]` or `[STAGING]` in each log entry
✅ **Logger separation**: Different logger instances per environment
✅ **Clear audit trail**: Production log is authoritative record

**Deletion logs are now fully isolated by environment, ensuring clean audit trails and safe testing.**
