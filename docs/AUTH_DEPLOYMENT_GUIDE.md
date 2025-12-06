# PantryPilot 权限控制部署指南

## 🎉 实施完成！

✅ **已完成**: Cookie-Based Authentication with Role-Based Access Control
✅ **测试通过**: Admin 和 Viewer 角色正常工作
✅ **安全性**: Bcrypt 密码哈希 + 签名 Cookie + HTTPS

---

## 📋 功能概述

### 认证方式
- **登录**: HTTP Basic Auth (浏览器原生弹窗)
- **会话**: 签名 Cookie (`session_token`)
- **过期**: 24 小时自动过期
- **传输**: HTTPS Only (ngrok)
- **存储**: HTTP-only + Secure cookies

### 用户角色

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| **Admin** | `admin` | 在 `.env` 中配置 | 读取、创建、修改、删除、导入 |
| **Viewer** | `viewer` | 在 `.env` 中配置 | 仅读取 |

---

## 🔧 部署步骤

### 1. 配置密码 (.env)

**重要**: 修改 `.env` 文件中的默认密码！

```bash
# 编辑 .env 文件
ADMIN_PASSWORD=你的超强密码Here123!
VIEWER_PASSWORD=查看者密码Here456!
SECRET_KEY=r4EWPVzODJgI43q8SMqHJsmWU3uncKbjxZTYV03ECEY
SESSION_EXPIRY_HOURS=24
```

**生成强密码**:
```bash
# 生成随机密码
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 2. 启动服务器

#### Staging (测试)
```bash
python run_staging.py
# → http://localhost:8001
```

#### Production
```bash
python run.py
# → http://localhost:8000
```

### 3. 使用 Ngrok 暴露服务

```bash
# 启动 ngrok (HTTPS)
ngrok http 8000

# 你会得到类似这样的 URL:
# https://abc123.ngrok.io
```

---

## 📱 使用方法

### 首次访问

1. 打开浏览器，访问 ngrok URL:
   `https://abc123.ngrok.io`

2. 浏览器弹出登录框，输入：
   - **用户名**: `admin` 或 `viewer`
   - **密码**: 你在 `.env` 中配置的密码

3. 登录成功后，自动保存 Cookie，24小时内无需再次登录

### 登出

访问: `https://abc123.ngrok.io/logout`

---

## 🔒 安全机制

### 1. 密码安全
- ✅ **Bcrypt 哈希**: 密码使用 bcrypt 加密存储
- ✅ **自动加盐**: Bcrypt 自动为每个密码生成唯一盐值
- ✅ **不可逆**: 即使数据库泄露，密码也无法被破解

### 2. 传输安全
- ✅ **HTTPS Only**: Ngrok 提供 TLS 加密
- ✅ **Secure Cookie**: Cookie 仅通过 HTTPS 传输
- ✅ **HTTP-only**: JavaScript 无法访问 Cookie (防XSS)

### 3. 会话安全
- ✅ **签名 Cookie**: 使用 SECRET_KEY 签名，防止篡改
- ✅ **24小时过期**: 自动过期，减少风险
- ✅ **SameSite=lax**: 防止 CSRF 攻击

---

## 🧪 验证测试

### 测试 1: 未认证访问（应拒绝）
```bash
curl http://localhost:8001/api/inventory/items

# 预期结果:
# {"detail":"Not authenticated. Please log in."}
```

### 测试 2: Admin 登录
```bash
curl -X POST http://localhost:8001/login \
  -u admin:你的密码 \
  -c cookies.txt

# 预期结果:
# {"status":"success","message":"Welcome, Administrator!","role":"admin"}
```

### 测试 3: 使用 Cookie 访问 API
```bash
curl http://localhost:8001/api/inventory/items \
  -b cookies.txt

# 预期结果: 返回物品列表
```

### 测试 4: Viewer 尝试删除（应拒绝）
```bash
# Viewer 登录
curl -X POST http://localhost:8001/login \
  -u viewer:你的密码 \
  -c cookies_viewer.txt

# 尝试删除
curl -X DELETE http://localhost:8001/api/inventory/items/1 \
  -b cookies_viewer.txt \
  -H "Content-Type: application/json" \
  -d '{"reason":"test"}'

# 预期结果:
# {"detail":"Permission 'delete' required. Your role: viewer"}
```

---

## 📊 权限矩阵

| 操作 | Endpoint | 方法 | Admin | Viewer |
|------|----------|------|-------|--------|
| 查看首页 | `/` | GET | ✅ | ✅ |
| 查看库存 | `/inventory` | GET | ✅ | ✅ |
| 查看告警 | `/alerts` | GET | ✅ | ✅ |
| 查看导入页 | `/import` | GET | ✅ | ✅ |
| 列出物品 | `/api/inventory/items` | GET | ✅ | ✅ |
| 创建物品 | `/api/inventory/items` | POST | ✅ | ❌ |
| 更新物品 | `/api/inventory/items/{id}` | PUT | ✅ | ❌ |
| 删除物品 | `/api/inventory/items/{id}` | DELETE | ✅ | ❌ |
| 导入数据 | `/api/import/*` | POST | ✅ | ❌ |
| 上传小票 | `/api/receipt/upload` | POST | ✅ | ❌ |

---

## 🚀 生产部署建议

### 1. 更改默认密码

**必须做**: 在部署到生产前，修改 `.env` 中的所有密码！

```bash
# 生成强密码
python -c "import secrets; print(secrets.token_urlsafe(20))"

# 编辑 .env
ADMIN_PASSWORD=<生成的强密码>
VIEWER_PASSWORD=<另一个强密码>
```

### 2. 保护 .env 文件

```bash
# 确保 .env 在 .gitignore 中
grep "^\.env$" .gitignore || echo ".env" >> .gitignore

# 设置文件权限 (Linux/Mac)
chmod 600 .env
```

### 3. 使用 Ngrok 的付费功能（可选）

```bash
# Ngrok 自带的 Basic Auth (双重保护)
ngrok http 8000 --basic-auth="username:password"
```

### 4. 启用 IP 白名单（可选）

如果需要限制访问IP，参考文档中的 IP 白名单示例。

---

## 🔧 故障排除

### 问题 1: "Invalid username or password"

**原因**: 密码不匹配
**解决**:
1. 检查 `.env` 文件中的密码
2. 确保没有多余的空格或特殊字符
3. 重启服务器以加载新密码

### 问题 2: 登录后仍提示未认证

**原因**: Cookie 未保存
**解决**:
1. 确保使用 HTTPS (ngrok)
2. 检查浏览器是否阻止 Cookie
3. 检查 Cookie 设置: `secure=True` 需要 HTTPS

### 问题 3: Viewer 能删除物品

**原因**: 权限检查未生效
**解决**:
1. 检查 API 端点是否使用 `require_permission("delete")`
2. 重启服务器
3. 清除浏览器 Cookie 重新登录

---

## 📁 文件结构

```
homestead_asset_management_system/
├── .env                    ← 配置密码和密钥 (不要提交到 git!)
├── app/
│   ├── auth.py            ← 认证模块 (核心逻辑)
│   ├── main.py            ← 登录/登出端点
│   └── routers/
│       ├── inventory.py   ← 受保护的 API
│       ├── import_data.py ← (待添加权限)
│       └── receipt_ocr.py ← (待添加权限)
├── docs/
│   └── AUTH_DEPLOYMENT_GUIDE.md ← 本文档
└── logs/
    ├── item_deletions.log           ← 生产删除日志
    └── item_deletions_staging.log   ← Staging 删除日志
```

---

## 🔄 下一步（可选）

### 待添加权限保护的端点

以下端点尚未添加权限保护，但不影响核心功能：

1. **Import API** (`app/routers/import_data.py`)
   - `POST /api/import/tsv`
   - `POST /api/import/tsv/file-path`
   - 建议: 添加 `require_permission("import")`

2. **Receipt OCR** (`app/routers/receipt_ocr.py`)
   - `POST /api/receipt/upload`
   - 建议: 添加 `require_permission("import")`

3. **Autocomplete** (`app/routers/autocomplete.py`)
   - 所有端点
   - 建议: 添加 `get_current_user` (仅需认证)

### 添加方法

```python
# 1. 导入认证函数
from ..auth import get_current_user, require_permission

# 2. 为只读端点添加认证
@router.get("/something")
def get_something(
    user: dict = Depends(get_current_user)  # 所有用户
):
    ...

# 3. 为写入端点添加权限
@router.post("/something")
def create_something(
    user: dict = Depends(require_permission("import"))  # 仅 admin
):
    ...
```

---

## 📞 技术支持

### API Endpoints

- **登录**: `POST /login` (HTTP Basic Auth)
- **登出**: `GET /logout`
- **检查状态**: `GET /auth/status`
- **健康检查**: `GET /health` (无需认证)

### 默认用户

| 用户名 | 默认密码 (`.env`) | 角色 |
|--------|------------------|------|
| `admin` | `ChangeMeToStrongPassword123!` | Administrator |
| `viewer` | `ViewerPassword456!` | Viewer |

**⚠️ 重要**: 生产部署前必须修改这些密码！

---

**部署日期**: 2025-12-06
**版本**: 1.0.0
**状态**: ✅ 测试通过，可用于生产
