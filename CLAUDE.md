Below is the updated and professionalized version of your **PantryPilot PRD**, rewritten in English and formatted to follow **good practices for a `CLAUDE.md`-style document** (concise, well-structured, technically actionable, and implementation-oriented).
It keeps all original details but improves readability, hierarchy, and engineering clarity.

---

# **PantryPilot — Product Requirement & Technical Design Document (V1 → V2 Blueprint)**

## 1. Overview

**Codename:** PantryPilot
**Goal:** Manage the full lifecycle of household inventory — including items, tools, and miscellaneous supplies — through **ingestion, tracking, expiration management, and intelligent querying**.

### **Key Features**

* **LLM-driven Q&A:** Natural language queries for availability, location, expiration, or substitutions.
* **Multimodal ingestion:** Bulk import from structured files, receipts, or images; automatic parsing to structured data.
* **Lifecycle management:** Automated in/out timestamps, shelf-life estimation, and proactive expiration alerts.
* **Visualization:** Interactive 2D floorplan view of household storage, with clickable inventory regions and search-based highlighting.

---

## 2. Target Users & Core Scenarios

### **Personas**

* **Home Organizer:** Manages purchases and storage; needs to know “what’s expiring” or “where things are.”
* **Family Members:** Ask ad-hoc queries such as “Do we have batteries?” or “Where’s the pizza cutter?”
* **Power Users:** Upload receipts, take photos, and want instant, structured inventory import.

### **User Stories**

* Import existing folders or CSV lists to auto-generate structured inventories.
* Upload a photo of food or tools — system auto-detects name, quantity, category, and adds to stock.
* Ask: “When does the milk expire?” or “Do we have a Phillips screwdriver?” and receive an instant answer plus visual location.
* Auto-track item check-in/out timestamps; estimate shelf life and alert before expiry.
* Explore a 2D home layout to visualize inventory and click to locate items.

---

## 3. Scope

### **Included in V1**

* **Bulk Import:** CSV/JSON/YAML and directory scanning (filenames, Exif, barcode).
* **Image Recognition:** OCR and photo-based ingestion.
* **GUI:** Web or desktop interface with listing, search, and basic reports.
* **LLM Q&A:** Unified local/cloud abstraction for querying and classification.
* **Shelf-life & Alerts:** Hybrid rule-based + model estimation; local or email notifications.
* **2D Floorplan:** Import SVG/image and annotate clickable regions.

### **Excluded (V2+)**

* Advanced multi-user permissions.
* Complex indoor navigation (limited to hierarchical path guidance).
* Automated price comparison or shopping suggestions.

---

## 4. Data Model (Schema)

### **Core Entities**

* `Household`: a logical space.
* `Location`: hierarchical nodes (“Kitchen > Fridge > Freezer”).
* `Item`: product definition (name, category, unit, etc.).
* `StockLot`: batch with timestamps, quantity, and expiry.
* `Media`: images, receipts, floorplans.
* `Rule`: shelf-life and alert definitions.
* `Event`: record of check-in/out/move/edit.

*(See Appendix for full JSON schema example)*

---

## 5. System Architecture (Python-first)

### **Tech Stack**

| Layer           | Technology                                               |
| --------------- | -------------------------------------------------------- |
| Backend         | **FastAPI**, **SQLModel/SQLAlchemy**, **Pydantic**       |
| DB              | SQLite (dev), PostgreSQL (prod, JSONB + full-text)       |
| Scheduler       | APScheduler (local) / Celery + Redis (prod)              |
| Search          | pgvector or FAISS (semantic search)                      |
| CV/OCR          | OpenCV, Pillow, pyzbar, Tesseract                        |
| LLM             | Custom `LLMProvider` abstraction for OpenAI/local models |
| GUI (Web)**     | FastAPI + Jinja/HTMX or NiceGUI (recommended)            |
| GUI (Desktop)** | PyQt6 or Tkinter                                         |
| Storage         | Local FS or S3-compatible (MinIO)                        |
| Auth            | Multi-user (email + magic link); OAuth-ready             |

### **Major Components**

* **ingestion:** file import & normalization
* **vision:** barcode/OCR/image recognition
* **nlq:** intent & entity recognition, LLM Q&A
* **inventory:** CRUD for items, stock, events, and rules
* **scheduler:** expiration scan & notifications
* **floorplan:** 2D region mapping & visualization
* **ui:** frontend and template logic

---

## 6. Key Flows

### **6.1 Batch Import**

1. User uploads folder/CSV/JSON/YAML.
2. `ingestion` auto-detects format → parses → optional LLM normalization.
3. `inventory.upsert_items()` creates or merges entries.
4. Generates import report (added, merged, conflicts).

### **6.2 Photo Recognition**

1. Upload → `vision.detect()` (barcode → lookup, else OCR/classification).
2. `nlq.normalize()` cleans and categorizes metadata.
3. `inventory.create_stock_lot()` adds item and timestamps.
4. `rules.estimate_shelf_life()` sets expiry and alert schedule.

### **6.3 Natural Language Q&A**

Query: “Do we still have eggs in the fridge?”
→ `nlq.intent()` parses → searches inventory with semantic filters → returns quantities, expiry, and visual floorplan highlight.

### **6.4 Stock Events & Alerts**

* **Check-out:** scan or select items → `Event(check_out)` updates quantity.
* **Daily job:** 9 AM expiry scan → triggers alerts (UI/email/popup).

---

## 7. GUI Design

### **Main Sections**

* **Inventory:** List, filter, search (by name/location/expiry).
* **Ingestion:** Bulk import, photo upload, manual add.
* **Floorplan:** 2D view — click to reveal region inventory.
* **Ask (Chat):** LLM-based Q&A with linked item cards.
* **Alerts:** Expiring, expired, low-stock notifications.
* **Settings:** Locations, rules, backup, models, privacy.

### **Key UX Features**

* Unified search (semantic + fuzzy).
* Editable hierarchical location tree.
* SVG-based floorplan editor with polygon region binding.
* Sidebar Q&A results with “highlight on map” actions.

---

## 8. Interfaces (FastAPI Spec Sketch)

### **REST Endpoints**

```
POST /api/import/batch
POST /api/vision/photo
POST /api/inventory/items
PUT  /api/inventory/items/{id}
PATCH /api/inventory/stock/{lot_id}
GET  /api/inventory/search?q=...&location=...&tag=...
POST /api/events
GET  /api/alerts
POST /api/alerts/ack
POST /api/nlq/query
POST /api/floorplan
PUT  /api/floorplan/regions
GET  /api/report/expiring?days=7
```

### **LLM Abstraction**

```python
class LLMProvider(Protocol):
    def classify(self, text: str) -> dict: ...
    def normalize_item(self, raw: dict) -> dict: ...
    def answer(self, question: str, context: dict) -> dict: ...
```

---

## 9. Shelf-life Estimation Rules

**Priority:** Barcode/brand > Category > Default rule.
**Sources:** Public food safety datasets + user-defined overrides.

```
expires_at = acquired_at + base_days - condition_adjustment
```

* Auto-switch to `open_shelf_life_days` upon “opened” events.
* Alert offsets: `[3, 1]` days before expiry (multi-channel).

---

## 10. 2D Floorplan Rendering

* **Storage:** SVG with region polygons bound to `location_id`.
* **Interaction:** Hover highlight, click to show inventory, search-based highlighting.
* **Path rule:** simple parent–child hierarchy (room → cabinet → drawer).

---

## 11. Privacy & Security

* **Local-first:** data stored locally/NAS; cloud backup optional.
* **Sensitive info encrypted** (addresses, photos).
* **Configurable LLM routing** (local/cloud); default anonymized.
* **Audit log** for external access.

---

## 12. Extensibility

* Plugin ingestion (e.g., e-commerce orders, digital receipts).
* IoT/NFC integration for fast stock-in/out.
* Smart scales for consumption tracking.
* Recipe integration (V2): suggest dishes & shopping lists.

---

## 13. Testing & Monitoring

* **Unit test coverage:** >70% (core ≥85%).
* **E2E tests:** import → detect → Q&A → alert → render.
* **Synthetic checks:** scheduled expiry → alert simulation.
* **Observability:** OpenTelemetry + sampled logs.
* **Audit trails** for all data access.
* **CRITICAL:** Use separate test db rather than the production DB.

---

## 14. Development Guidelines

### **Database Environment**

**CRITICAL: Always use staging database for testing and development**

- **Production DB**: `data/pantrypilot.db` - Use ONLY for production operations
- **Staging DB**: `data_staging/pantrypilot.db` - Use for ALL testing, development, and experimentation

**Commands:**
- **Development/Testing**: `python run_staging.py` (uses staging database)
- **Production**: `python run.py` (uses production database)

**Rules:**
1. NEVER write test data to production database
2. ALWAYS use `run_staging.py` for feature development and testing
3. When testing new features (imports, OCR, inventory changes), use staging environment
4. Production database should only contain real user data
5. Before deploying changes, test thoroughly in staging environment first
