# 家庭资产盘存系统 (Household Asset Management System)

A modern, intelligent inventory management system for household items, food, tools, and supplies. Track what you have, where it is, and when it expires.

## Features

- **Inventory Management**: Track items with name, category, quantity, location, and expiry dates
- **Hierarchical Locations**: Organize items in nested locations (Kitchen > Fridge > Top Shelf)
- **Smart Search**: Filter by name, category, location, and expiry status
- **Expiration Tracking**: Automatic alerts for expiring and expired items
- **Bulk Import**: Import existing inventory from TSV/CSV files
- **Beautiful UI**: Modern, responsive interface with intuitive navigation
- **Visual Hierarchy**: Tree view of locations and storage areas

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser to:
```
http://localhost:8000
```

## Usage

### Import Sample Data

The easiest way to get started is to import the sample data:

1. Navigate to the **Import** page
2. Click "Import Sample Data Now"
3. The system will load 56 sample items including food, tools, and household supplies

Alternatively, you can import via API:
```bash
curl -X POST "http://localhost:8000/api/import/tsv/file-path" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "src/sample_asset_data.tsv", "household_id": 1}'
```

### Add Items Manually

1. Go to the **Inventory** page
2. Click "➕ Add Item"
3. Fill in the form:
   - Name (required)
   - Category (required)
   - Quantity and Unit
   - Location path (e.g., "Kitchen > Pantry > Top Shelf")
   - Acquired and expiry dates
   - Notes
4. Click "Save Item"

### Search and Filter

Use the search bar and filters on the Inventory page:
- **Search**: Type item name or notes
- **Category Filter**: Select specific category
- **Expiry Filter**: Filter by expiry status (Fresh, Expiring Soon, Expired)
- **Location Tree**: Click on locations in the sidebar to view items in that location

### View Alerts

The **Alerts** page shows:
- Expired items (items past their expiry date)
- Items expiring soon (customizable: 3, 7, 14, or 30 days)
- All items with expiry dates, sorted by expiry date

## Project Structure

```
homestead_asset_management_system/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── database.py          # Database connection
│   ├── crud.py              # CRUD operations
│   ├── routers/
│   │   ├── inventory.py     # Inventory endpoints
│   │   └── import_data.py   # Import endpoints
│   ├── static/
│   │   └── css/
│   │       └── styles.css   # UI styles
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── index.html       # Dashboard
│       ├── inventory.html   # Inventory management
│       ├── import.html      # Data import
│       └── alerts.html      # Expiration alerts
├── src/
│   └── sample_asset_data.tsv  # Sample data
├── data/
│   └── pantrypilot.db       # SQLite database (auto-created)
├── requirements.txt
└── README.md
```

## API Endpoints

### Inventory

- `GET /api/inventory/items` - List all items
- `GET /api/inventory/items/search` - Search items with filters
- `GET /api/inventory/items/{item_id}` - Get item by ID
- `POST /api/inventory/items` - Create new item
- `PUT /api/inventory/items/{item_id}` - Update item
- `DELETE /api/inventory/items/{item_id}` - Delete item
- `GET /api/inventory/expiring?days=7` - Get items expiring within N days
- `GET /api/inventory/expired` - Get expired items
- `GET /api/inventory/categories` - Get all categories
- `GET /api/inventory/locations` - Get location hierarchy

### Import

- `POST /api/import/tsv` - Upload and import TSV/CSV file
- `POST /api/import/tsv/file-path` - Import from local file path

## Data Import Format

Your TSV/CSV file should have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| name | Item name (required) | Whole Milk |
| category | Category | Dairy |
| quantity | Quantity amount | 1 |
| unit | Unit of measurement | gallon |
| location_path | Hierarchical path | Kitchen > Fridge > Main Shelf |
| acquired_date | Date acquired (YYYY-MM-DD) | 2025-01-08 |
| expiry_date | Expiration date (YYYY-MM-DD) | 2025-01-15 |
| notes | Additional notes | Organic |

### Example TSV Row

```
Whole Milk	Dairy	1	gallon	Kitchen > Fridge > Main Shelf	2025-01-08	2025-01-15	Organic
```

## Development

### Run in Development Mode

```bash
uvicorn app.main:app --reload --port 8000
```

### Run Tests (Future)

```bash
pytest
```

### Access API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Future Features (V2+)

- **LLM Q&A**: Natural language queries ("Do we have milk?")
- **Image Recognition**: Upload photos to auto-detect items
- **Receipt OCR**: Scan receipts to import items
- **2D Floorplan**: Visual map of your home with clickable inventory regions
- **Smart Alerts**: Email/push notifications for expiring items
- **Multi-user**: Family sharing and collaborative inventory
- **Mobile App**: Native mobile interface
- **Barcode Scanning**: Quick item lookup and addition

## Tech Stack

- **Backend**: FastAPI, SQLModel, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL-ready
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Styling**: Custom CSS with modern design system

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions, please check the API documentation at `/docs` or review the code comments.

---

**Built with ❤️ for better household management**
