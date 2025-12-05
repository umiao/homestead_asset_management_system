# PantryPilot Quick Start Guide

## First Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
```

The server will start at: **http://localhost:8000**

### 3. Import Sample Data

**Option A: Using the Web UI** (Recommended)
1. Open http://localhost:8000/import
2. Click **"Import Sample Data Now"**
3. Wait for confirmation

**Option B: Using API**
```bash
curl -X POST "http://localhost:8000/api/import/tsv/file-path" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "src/sample_asset_data.tsv", "household_id": 1}'
```

### 4. Explore the System

- **Dashboard**: http://localhost:8000 - View stats and recent items
- **Inventory**: http://localhost:8000/inventory - Browse all items with hierarchical tree
- **Alerts**: http://localhost:8000/alerts - See expiring items
- **API Docs**: http://localhost:8000/docs - Interactive API documentation

---

## Common Tasks

### Reset Database (Start Fresh)

If you accidentally imported data twice or want to start over:

```bash
python reset_database.py
```

Then restart the server and import sample data again.

### Add New Items

**Via Web UI:**
1. Go to http://localhost:8000/inventory
2. Click "➕ Add Item"
3. Fill in the form:
   - Name: "Peanut Butter"
   - Category: "Food"
   - Quantity: 1
   - Unit: jar
   - Location: "Kitchen > Pantry > Upper Shelf"
   - Expiry date: (optional)
4. Click "Save Item"

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/inventory/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Peanut Butter",
    "category": "Food",
    "quantity": 1,
    "unit": "jar",
    "location_path": "Kitchen > Pantry > Upper Shelf",
    "household_id": 1
  }'
```

### Search for Items

**In the Web UI:**
- Go to Inventory page
- Use the search bar to find items by name
- Use filters for category and expiry status
- Click locations in the sidebar to browse by area

**Via API:**
```bash
# Search by name
curl "http://localhost:8000/api/inventory/items/search?q=milk"

# Filter by category
curl "http://localhost:8000/api/inventory/items/search?category=Dairy"

# Filter by expiry status
curl "http://localhost:8000/api/inventory/items/search?expiry_status=expiring_soon"
```

### Import Your Own Data

Create a TSV file with these columns:
```
name	category	quantity	unit	location_path	acquired_date	expiry_date	notes
```

Example row:
```
Olive Oil	Condiments	750	ml	Kitchen > Pantry > Oil Shelf	2025-01-10	2026-01-10	Extra virgin
```

Then import via:
1. Web UI: http://localhost:8000/import (drag & drop or click to upload)
2. API: Use the `/api/import/tsv` endpoint with file upload

---

## Troubleshooting

### Port Already in Use
If port 8000 is busy, stop any running instances:
- Press `Ctrl+C` in the terminal running the server
- Or edit `run.py` to use a different port

### Import Not Working
Make sure:
1. The server is running (`python run.py`)
2. You're using the correct file path (relative to project root)
3. The TSV file has proper tab-separated columns

### Database Issues
If you see database errors:
```bash
python reset_database.py
```

### Can't See Hierarchical Locations
The locations are created automatically from the `location_path` field.
Use the format: `"Room > Container > Subcontainer"`
Example: `"Kitchen > Fridge > Top Shelf"`

---

## Sample Data Details

The included `src/sample_asset_data.tsv` contains:
- **56 items** across 7 main categories
- **51 locations** in hierarchical structure
- Mix of food items, tools, cleaning supplies, and office materials
- Some items have expiry dates for testing alert functionality

---

## Next Steps

1. ✅ Import sample data to explore the system
2. 🔍 Browse the hierarchical location tree
3. ⚠️ Check the Alerts page for expiring items
4. ➕ Add your own items via the web UI
5. 📄 Create your own TSV file for bulk import
6. 🔧 Customize categories and locations as needed

**Enjoy your PantryPilot!**
