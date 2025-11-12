# PantryPilot - 中文支持说明 (Chinese Language Support)

## ✅ 支持的功能 (Supported Features)

PantryPilot 完全支持中文！以下功能都可以使用中文：

### 1. **物品名称** (Item Names)
- ✅ 中文物品名称: 电饭煲、洗发水、螺丝刀
- ✅ 英文名称: Rice Cooker, Shampoo, Screwdriver
- ✅ 混合名称: Herman Miller椅子

### 2. **分类** (Categories)
- ✅ 中文分类: 家电、工具、清洁用品
- ✅ 英文分类: Electronics, Tools, Cleaning

### 3. **单位** (Units)
- ✅ 中文单位: 个、件、台、瓶、盒、包、支
- ✅ 英文单位: piece, item, unit, bottle, box, pack

### 4. **位置路径** (Location Paths)
- ✅ 中文路径: 卧室 > 书架柜1号柜
- ✅ 英文路径: Bedroom > Bookshelf > Cabinet 1
- ✅ 混合路径: 卧室 > Closet > 抽屉

### 5. **备注说明** (Notes)
- ✅ 完全支持中文备注
- ✅ 混合中英文说明

---

## 📊 数量字段支持 (Quantity Field Support)

系统支持多种数量表示方式：

### 数字 (Numbers)
```
1, 2, 3, 10, 100
1.5, 2.5 (小数)
```

### 中文数字 (Chinese Numbers)
```
一, 二, 三, 四, 五, 六, 七, 八, 九, 十
```

### 中文数量词 (Chinese Quantity Terms)
```
多个 → 2
若干 → 1
一些 → 2
几个 → 2
数个 → 2
少许 → 1
```

### 混合格式 (Mixed Format)
```
"2个" → 2
"10台" → 10
"三件" → 3
```

---

## 📅 日期格式支持 (Date Format Support)

支持多种日期格式：

```
YYYY-MM-DD    → 2025-01-15
MM/DD/YYYY    → 11/12/2025
DD/MM/YYYY    → 15/01/2025
YYYY/MM/DD    → 2025/01/15
```

---

## 📝 TSV 文件格式示例 (TSV File Format Example)

### 中文示例 (Chinese Example)
```tsv
name	category	quantity	unit	location_path	acquired_date	expiry_date	notes
电饭煲	家电	1	台	厨房	11/12/2025	11/12/2030	三菱品牌
剪刀	工具	2	把	卧室 > 书架柜1号柜	11/12/2025	11/12/2030	文具用
洗发水	清洁	1	瓶	浴室 > 洗手台	11/12/2025	11/12/2030	海飞丝
```

### 混合示例 (Mixed Example)
```tsv
name	category	quantity	unit	location_path	acquired_date	expiry_date	notes
Herman Miller椅子	家具/办公	1	把	卧室	11/12/2025	11/12/2030
USB充电线	数码	多个	条	卧室 > 书架柜1号柜	11/12/2025	11/12/2030	Type-C接口
```

---

## 🔧 技术实现 (Technical Implementation)

### UTF-8 编码支持
- ✅ 数据库: SQLite 原生支持 Unicode
- ✅ 文件导入: UTF-8 编码读取
- ✅ Web UI: `<meta charset="UTF-8">`
- ✅ API 响应: JSON UTF-8

### 智能解析
```python
# 自动解析中文数量
"多个" → 2.0
"三" → 3.0
"10台" → 10.0

# 自动解析日期格式
"11/12/2025" → 2025-11-12
"2025-01-15" → 2025-01-15
```

---

## 💡 使用建议 (Usage Tips)

### 1. 文件编码
确保 TSV 文件使用 **UTF-8 编码**保存：
- Windows 记事本: 另存为 → 编码选择 "UTF-8"
- Excel: 保存为 → CSV UTF-8 (逗号分隔)(*.csv)
- VS Code: 右下角选择 "UTF-8"

### 2. 混合使用
可以自由混合中英文：
```
name: Herman Miller椅子
category: 家具/办公
unit: 个
location_path: 卧室 > Closet > 抽屉1
```

### 3. 数量建议
- 优先使用阿拉伯数字: `1, 2, 10`
- 中文数字: `一, 二, 三`
- 避免复杂表达: 用 `10` 而不是 `十个左右`

### 4. 日期格式
- 推荐: `YYYY-MM-DD` (2025-01-15)
- 也支持: `MM/DD/YYYY` (11/12/2025)
- 避免歧义: 使用 4 位年份

---

## 🧪 测试示例 (Test Examples)

### 通过 Web UI 添加
```
名称: 电饭煲
分类: 家电
数量: 1
单位: 台
位置: 厨房 > 储物柜 > 下层
```

### 通过 API 添加
```bash
curl -X POST "http://localhost:8000/api/inventory/items" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "name": "电饭煲",
    "category": "家电",
    "quantity": 1,
    "unit": "台",
    "location_path": "厨房 > 储物柜",
    "household_id": 1
  }'
```

### 批量导入 TSV
1. 准备 UTF-8 编码的 TSV 文件
2. 访问 http://localhost:8000/import
3. 点击 "Import Sample Data Now" 或上传文件
4. 查看导入结果

---

## ⚠️ 常见问题 (Common Issues)

### 问题 1: 中文显示为乱码
**解决方案:**
- 确保 TSV 文件使用 UTF-8 编码
- 浏览器正确显示中文 (现代浏览器默认支持)

### 问题 2: 导入失败
**检查:**
- 文件格式是否为 TSV (Tab-separated)
- 文件编码是否为 UTF-8
- 数量字段是否包含无法识别的字符

### 问题 3: 数量解析错误
**支持的格式:**
- ✅ 阿拉伯数字: 1, 2, 10, 100
- ✅ 中文数字: 一, 二, 三, 十
- ✅ 常用词: 多个, 若干, 一些
- ❌ 不支持: 好几个, 很多, 大约10个

---

## 🚀 开始使用 (Getting Started)

```bash
# 1. 启动服务器
python run.py

# 2. 访问 Web UI
http://localhost:8000

# 3. 导入中文数据
访问: http://localhost:8000/import
点击: "Import Sample Data Now"

# 4. 浏览中文物品
访问: http://localhost:8000/inventory
```

---

## 📚 完整功能列表

- ✅ 中文物品名称、分类、单位
- ✅ 中文位置层级结构
- ✅ 中文备注和说明
- ✅ 中文数量解析
- ✅ 多种日期格式
- ✅ 混合中英文内容
- ✅ UTF-8 全链路支持
- ✅ Web UI 正确显示中文
- ✅ API 支持 JSON UTF-8

**PantryPilot 完全支持中文，开箱即用！** 🎉
