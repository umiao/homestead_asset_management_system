# LFU Cache-based Autocomplete Feature

## 概述 / Overview

本系统实现了基于LFU（Least Frequently Used，最不经常使用）缓存策略的智能自动补全功能，为"添加物品"表单的 **Category（类别）**、**Location Path（位置路径）** 和 **Unit（单位）** 字段提供智能推荐。

This system implements an intelligent autocomplete feature based on the LFU (Least Frequently Used) cache strategy, providing smart suggestions for the **Category**, **Location Path**, and **Unit** fields in the "Add Item" form.

---

## 核心特性 / Key Features

### 1. **LFU缓存机制 / LFU Cache Mechanism**
- 基于使用频率自动排序建议选项
- 自动淘汰低频使用的条目（当缓存达到上限时）
- 动态更新：每次创建物品时自动记录使用频率
- 支持多租户（按 household_id 隔离数据）

- Automatically ranks suggestions by usage frequency
- Automatically evicts low-frequency entries when cache limit is reached
- Dynamic updates: Records usage frequency automatically when creating items
- Multi-tenant support (data isolated by household_id)

### 2. **智能建议 / Smart Suggestions**
- **实时过滤**：根据用户输入动态筛选建议
- **频率徽章**：显示每个选项的使用次数
- **键盘导航**：支持方向键、回车键、Esc键
- **鼠标交互**：点击选择，悬停高亮

- **Real-time filtering**: Dynamically filters suggestions based on user input
- **Frequency badges**: Displays usage count for each option
- **Keyboard navigation**: Arrow keys, Enter, Escape support
- **Mouse interaction**: Click to select, hover to highlight

### 3. **优雅的UI设计 / Elegant UI Design**
- 现代化下拉菜单样式
- 平滑过渡动画
- 响应式设计（适配移动端）
- 支持暗黑模式

- Modern dropdown menu styling
- Smooth transition animations
- Responsive design (mobile-friendly)
- Dark mode support

---

## 技术架构 / Technical Architecture

### **Backend (Python + FastAPI)**

#### 1. 数据库模型 / Database Model
**文件位置 / File:** `app/services/autocomplete_cache.py`

```python
class AutocompleteCache(SQLModel, table=True):
    id: Optional[int]
    field_type: str          # 'category', 'location_path', 'unit'
    value: str               # 缓存的值 / The cached value
    frequency: int           # 使用频率（LFU核心指标）/ Usage frequency
    last_used: datetime      # 最后使用时间 / Last used timestamp
    created_at: datetime     # 创建时间 / Created timestamp
    household_id: int        # 租户隔离 / Tenant isolation
```

#### 2. LFU服务类 / LFU Service Class
**类名 / Class:** `LFUAutocompleteService`

**关键方法 / Key Methods:**

| 方法 / Method | 功能 / Functionality |
|--------------|-------------------|
| `record_usage()` | 记录字段使用，增加频率计数 / Record field usage, increment frequency |
| `get_suggestions()` | 获取建议列表（支持查询过滤）/ Get suggestion list (with query filtering) |
| `get_top_suggestions()` | 获取Top N建议（简单字符串列表）/ Get top N suggestions (simple string list) |
| `initialize_from_existing_data()` | 从现有数据初始化缓存 / Initialize cache from existing data |
| `cleanup_low_frequency()` | 清理低频条目 / Clean up low-frequency entries |
| `get_statistics()` | 获取缓存统计信息 / Get cache statistics |

**缓存管理策略 / Cache Management Strategy:**
- **最大缓存大小 / Max Cache Size:** 100条记录/字段类型
- **最小频率阈值 / Min Frequency Threshold:** 2次（用于自动清理）
- **淘汰策略 / Eviction Policy:** 当超过最大缓存大小时，删除频率最低的条目

#### 3. API端点 / API Endpoints
**路由前缀 / Route Prefix:** `/api/autocomplete`

**文件位置 / File:** `app/routers/autocomplete.py`

| 端点 / Endpoint | 方法 / Method | 功能 / Functionality |
|----------------|--------------|-------------------|
| `/suggestions/{field_type}` | GET | 获取自动补全建议（支持查询过滤）/ Get autocomplete suggestions (with query filtering) |
| `/suggestions/{field_type}/simple` | GET | 获取简单建议列表（仅值）/ Get simple suggestion list (values only) |
| `/record` | POST | 记录字段使用 / Record field usage |
| `/statistics` | GET | 获取缓存统计信息 / Get cache statistics |
| `/initialize` | POST | 从现有数据初始化缓存 / Initialize cache from existing data |
| `/cleanup` | POST | 清理低频条目 / Clean up low-frequency entries |

**使用示例 / Usage Examples:**

```bash
# 获取类别建议 / Get category suggestions
curl "http://localhost:8000/api/autocomplete/suggestions/category?limit=10"

# 带查询过滤 / With query filtering
curl "http://localhost:8000/api/autocomplete/suggestions/category?query=food&limit=5"

# 记录使用 / Record usage
curl -X POST "http://localhost:8000/api/autocomplete/record?field_type=category&value=Food"

# 初始化缓存（首次设置）/ Initialize cache (first-time setup)
curl -X POST "http://localhost:8000/api/autocomplete/initialize"

# 获取统计信息 / Get statistics
curl "http://localhost:8000/api/autocomplete/statistics"
```

---

### **Frontend (Vanilla JavaScript + CSS)**

#### 1. JavaScript组件 / JavaScript Component
**文件位置 / File:** `app/static/js/autocomplete.js`

**核心类 / Core Class:** `AutocompleteInput`

```javascript
// 初始化示例 / Initialization example
const autocomplete = new AutocompleteInput(inputElement, {
    fieldType: 'category',      // 字段类型 / Field type
    minChars: 0,                // 最小字符数触发建议 / Min chars to trigger
    maxSuggestions: 10,         // 最大建议数量 / Max suggestions
    debounceMs: 200,            // 防抖延迟（毫秒）/ Debounce delay (ms)
    household_id: 1             // 租户ID / Household ID
});

// 快捷初始化方法 / Quick initialization method
initAutocomplete('input-id', 'category', { maxSuggestions: 10 });
```

**事件处理 / Event Handlers:**
- `onInput`: 输入时触发建议获取（带防抖）
- `onFocus`: 聚焦时显示建议
- `onKeyDown`: 键盘导航（↑↓ 选择，Enter 确认，Esc 关闭）
- `onClick`: 点击选择建议

#### 2. CSS样式 / CSS Styling
**文件位置 / File:** `app/static/css/autocomplete.css`

**关键样式类 / Key CSS Classes:**

| 类名 / Class | 用途 / Purpose |
|-------------|--------------|
| `.autocomplete-dropdown` | 下拉菜单容器 / Dropdown container |
| `.autocomplete-item` | 建议条目 / Suggestion item |
| `.autocomplete-item.selected` | 选中的建议 / Selected suggestion |
| `.autocomplete-value` | 建议文本 / Suggestion text |
| `.autocomplete-badge` | 频率徽章 / Frequency badge |

**设计特点 / Design Features:**
- 圆角边框、阴影效果
- 鼠标悬停 + 键盘选中的视觉反馈
- 自定义滚动条样式
- 平滑淡入动画
- 响应式布局（移动端优化）

---

## 集成指南 / Integration Guide

### **步骤1：首次初始化缓存 / Step 1: Initialize Cache (First Time)**

在首次使用前，需要从现有数据初始化缓存：

```bash
curl -X POST http://localhost:8000/api/autocomplete/initialize
```

**响应示例 / Response Example:**
```json
{
    "success": true,
    "counts": {
        "category": 12,
        "location_path": 45,
        "unit": 8
    },
    "message": "Cache initialized successfully"
}
```

### **步骤2：在HTML中引入资源 / Step 2: Include Resources in HTML**

在页面的 `<head>` 部分添加CSS：

```html
<link rel="stylesheet" href="/static/css/autocomplete.css">
```

在页面底部添加JavaScript：

```html
<script src="/static/js/autocomplete.js"></script>
```

### **步骤3：初始化自动补全 / Step 3: Initialize Autocomplete**

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // 为类别字段初始化 / Initialize for category field
    initAutocomplete('item-category', 'category', {
        minChars: 0,
        maxSuggestions: 10,
        debounceMs: 150
    });

    // 为位置路径字段初始化 / Initialize for location path field
    initAutocomplete('item-location', 'location_path', {
        minChars: 0,
        maxSuggestions: 10
    });

    // 为单位字段初始化 / Initialize for unit field
    initAutocomplete('item-unit', 'unit', {
        minChars: 0,
        maxSuggestions: 8
    });
});
```

### **步骤4：确保表单字段支持文本输入 / Step 4: Ensure Form Fields Support Text Input**

自动补全要求输入框为 `<input type="text">`，而非 `<select>` 下拉框。

**修改前 / Before:**
```html
<select id="item-unit" class="form-select" required>
    <option value="count">count</option>
    <option value="kg">kg</option>
    ...
</select>
```

**修改后 / After:**
```html
<input type="text" id="item-unit" class="form-input"
       placeholder="e.g., count, kg, liter" required>
```

---

## 自动记录使用频率 / Automatic Usage Recording

每次用户通过"添加物品"表单创建新物品时，系统会自动记录以下字段的使用：

When a user creates a new item via the "Add Item" form, the system automatically records the usage of the following fields:

**代码位置 / Code Location:** `app/routers/inventory.py` (Lines 154-179)

```python
# Initialize autocomplete service
autocomplete_service = LFUAutocompleteService(session, household.id)

# ... (创建物品逻辑 / Create item logic) ...

# Record usage in autocomplete cache
if item_data.get("category"):
    autocomplete_service.record_usage("category", item_data.get("category"))
if location_path:
    autocomplete_service.record_usage("location_path", location_path)
if item_data.get("unit"):
    autocomplete_service.record_usage("unit", item_data.get("unit"))
```

---

## 测试结果 / Test Results

### **API测试 / API Testing**

#### 1. 初始化缓存 / Initialize Cache
```bash
curl -X POST http://localhost:8000/api/autocomplete/initialize
```
**结果 / Result:**
```json
{
    "success": true,
    "counts": {
        "category": 30,
        "location_path": 13,
        "unit": 20
    },
    "message": "Cache initialized successfully"
}
```

#### 2. 获取类别建议 / Get Category Suggestions
```bash
curl "http://localhost:8000/api/autocomplete/suggestions/category?limit=5"
```
**结果 / Result:**
```json
[
    {"value": "食物", "frequency": 72, "last_used": "2025-12-05T06:34:22.502197"},
    {"value": "食品", "frequency": 28, "last_used": "2025-12-05T06:34:22.503196"},
    {"value": "厨具", "frequency": 17, "last_used": "2025-12-05T06:34:22.499195"},
    {"value": "工具", "frequency": 14, "last_used": "2025-12-05T06:34:22.493197"},
    {"value": "杂物", "frequency": 3, "last_used": "2025-12-05T06:34:22.496195"}
]
```

#### 3. 获取位置路径建议 / Get Location Path Suggestions
```bash
curl "http://localhost:8000/api/autocomplete/suggestions/location_path?limit=5"
```
**结果 / Result:**
```json
[
    {"value": "冰箱 > 冷藏", "frequency": 44, "last_used": "2025-12-05T06:34:22.514343"},
    {"value": "厨房墙挂储物柜", "frequency": 27, "last_used": "2025-12-05T06:34:22.513343"},
    {"value": "厨房 > 冰箱上柜（1号柜）", "frequency": 22, "last_used": "2025-12-05T06:34:22.512343"},
    {"value": "厨房 > 冰箱右柜（2号柜）（上）", "frequency": 15, "last_used": "2025-12-05T06:34:22.512343"},
    {"value": "冰箱 > 冷冻", "frequency": 14, "last_used": "2025-12-05T06:34:22.514343"}
]
```

#### 4. 获取单位建议 / Get Unit Suggestions
```bash
curl "http://localhost:8000/api/autocomplete/suggestions/unit?limit=8"
```
**结果 / Result:**
```json
[
    {"value": "包", "frequency": 39, "last_used": "2025-12-05T06:34:22.507711"},
    {"value": "个", "frequency": 31, "last_used": "2025-12-05T06:34:22.504710"},
    {"value": "count", "frequency": 29, "last_used": "2025-12-05T06:34:22.509334"},
    {"value": "件", "frequency": 27, "last_used": "2025-12-05T06:34:22.505710"},
    {"value": "袋", "frequency": 9, "last_used": "2025-12-05T06:34:22.509334"},
    {"value": "罐", "frequency": 5, "last_used": "2025-12-05T06:34:22.510342"},
    {"value": "把", "frequency": 5, "last_used": "2025-12-05T06:34:22.506710"},
    {"value": "箱", "frequency": 2, "last_used": "2025-12-05T06:34:22.511343"}
]
```

#### 5. 统计信息 / Statistics
```bash
curl "http://localhost:8000/api/autocomplete/statistics"
```
**结果 / Result:**
```json
{
    "total_entries": 63,
    "by_field_type": {
        "category": {"count": 30, "total_frequency": 165},
        "unit": {"count": 20, "total_frequency": 165},
        "location_path": {"count": 13, "total_frequency": 165}
    },
    "top_values": [
        {"field_type": "category", "value": "食物", "frequency": 72, ...},
        {"field_type": "location_path", "value": "冰箱 > 冷藏", "frequency": 44, ...},
        ...
    ]
}
```

---

## 配置选项 / Configuration Options

### **LFU服务配置 / LFU Service Configuration**

在 `app/services/autocomplete_cache.py` 中可调整以下参数：

```python
class LFUAutocompleteService:
    DEFAULT_MAX_CACHE_SIZE = 100        # 每个字段类型的最大缓存条目数
    MIN_FREQUENCY_THRESHOLD = 2         # 自动清理的最小频率阈值
```

### **前端配置 / Frontend Configuration**

在初始化时可传递的选项：

```javascript
initAutocomplete('input-id', 'category', {
    minChars: 0,           // 最小输入字符数（0=总是显示建议）
    maxSuggestions: 10,    // 最大建议数量
    debounceMs: 200,       // 防抖延迟（毫秒）
    household_id: 1        // 租户ID
});
```

---

## 维护与监控 / Maintenance & Monitoring

### **定期清理 / Periodic Cleanup**

建议定期清理低频条目以保持缓存效率：

```bash
# 清理所有字段的低频条目 / Clean up low-frequency entries for all fields
curl -X POST "http://localhost:8000/api/autocomplete/cleanup"

# 仅清理特定字段 / Clean up specific field only
curl -X POST "http://localhost:8000/api/autocomplete/cleanup?field_type=category"
```

### **监控缓存状态 / Monitor Cache Status**

定期检查统计信息以了解缓存使用情况：

```bash
curl "http://localhost:8000/api/autocomplete/statistics"
```

---

## 文件清单 / File Checklist

| 文件路径 / File Path | 功能 / Functionality |
|---------------------|-------------------|
| `app/services/autocomplete_cache.py` | LFU缓存服务 + 数据库模型 / LFU cache service + DB model |
| `app/routers/autocomplete.py` | 自动补全API端点 / Autocomplete API endpoints |
| `app/routers/inventory.py` | 集成使用记录逻辑 / Integrated usage recording |
| `app/static/js/autocomplete.js` | 前端自动补全组件 / Frontend autocomplete component |
| `app/static/css/autocomplete.css` | 下拉菜单样式 / Dropdown menu styles |
| `app/templates/inventory.html` | 集成自动补全到表单 / Integrated autocomplete into form |
| `app/database.py` | 数据库初始化（包含AutocompleteCache表）/ DB initialization |
| `app/main.py` | 注册autocomplete路由 / Registered autocomplete router |

---

## 常见问题 / FAQ

### Q1: 缓存会自动更新吗？/ Does the cache update automatically?
**A:** 是的。每次通过"添加物品"表单创建物品时，系统会自动记录使用频率。
Yes. Every time an item is created via the "Add Item" form, the system automatically records usage frequency.

### Q2: 如何重置缓存？/ How to reset the cache?
**A:** 删除数据库中的 `autocomplete_cache` 表所有记录，然后重新运行初始化：
Delete all records from the `autocomplete_cache` table in the database, then re-run initialization:
```bash
curl -X POST http://localhost:8000/api/autocomplete/initialize
```

### Q3: 缓存大小限制是多少？/ What is the cache size limit?
**A:** 默认每个字段类型最多缓存100条记录。可在 `LFUAutocompleteService` 类中修改 `DEFAULT_MAX_CACHE_SIZE`。
Default: 100 entries per field type. Adjust `DEFAULT_MAX_CACHE_SIZE` in `LFUAutocompleteService` class.

### Q4: 支持多用户吗？/ Does it support multi-user?
**A:** 是的。缓存按 `household_id` 隔离，每个家庭的缓存互不干扰。
Yes. Cache is isolated by `household_id`, ensuring each household has separate cache.

### Q5: 如何禁用某个字段的自动补全？/ How to disable autocomplete for a specific field?
**A:** 移除该字段的 `initAutocomplete()` 调用即可。
Simply remove the `initAutocomplete()` call for that field.

---

## 未来改进 / Future Enhancements

- [ ] 支持拼音搜索（中文输入优化）/ Pinyin search support (Chinese input optimization)
- [ ] 添加"最近使用"时间权重（结合LRU策略）/ Add "recently used" time weight (combine with LRU)
- [ ] 支持用户自定义建议（置顶选项）/ User-defined pinned suggestions
- [ ] 多语言建议合并（中英文同义词）/ Multilingual suggestion merging (Chinese-English synonyms)
- [ ] 移动端触摸优化 / Mobile touch optimization
- [ ] 建议分组显示（按子类别）/ Grouped suggestions (by subcategory)

---

## 贡献 / Contributing

如有问题或改进建议，请提交Issue或Pull Request。

For issues or improvement suggestions, please submit an Issue or Pull Request.

**Generated with Claude Code** 🤖
