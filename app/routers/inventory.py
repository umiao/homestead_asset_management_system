"""Inventory management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session
from datetime import date, datetime
from pydantic import BaseModel
import logging
import os

from ..database import get_session, ENVIRONMENT
from ..models import Item, Event
from .. import crud
from ..services.autocomplete_cache import LFUAutocompleteService

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

# Setup logging for deletions
# Environment-based log separation
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Use different log file based on environment
# Production: logs/item_deletions.log
# Staging: logs/item_deletions_staging.log
if ENVIRONMENT == 'staging':
    log_file = os.path.join(log_dir, "item_deletions_staging.log")
else:
    log_file = os.path.join(log_dir, "item_deletions.log")

deletion_logger = logging.getLogger(f"inventory_deletions_{ENVIRONMENT}")
deletion_logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create formatter - include environment in log messages
formatter = logging.Formatter(
    f'%(asctime)s - [{ENVIRONMENT.upper()}] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
deletion_logger.addHandler(file_handler)


class DeleteItemRequest(BaseModel):
    """Request model for item deletion with reason."""
    reason: str
    checkout_record: Optional[str] = None


@router.get("/items")
def list_items(
    household_id: int = Query(default=1),
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List all inventory items with computed fields."""
    items = crud.get_all_items(session, household_id, skip, limit)
    return [
        {
            **item.model_dump(),
            "expiry_status": item.expiry_status,
            "days_until_expiry": item.days_until_expiry,
            "is_expired": item.is_expired
        }
        for item in items
    ]


@router.get("/items/search")
def search_items(
    household_id: int = Query(default=1),
    q: Optional[str] = None,
    category: Optional[str] = None,
    location_id: Optional[int] = None,
    expiry_status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Search items with filters and computed fields."""
    items = crud.search_items(
        session,
        household_id,
        query=q,
        category=category,
        location_id=location_id,
        expiry_status=expiry_status
    )
    return [
        {
            **item.model_dump(),
            "expiry_status": item.expiry_status,
            "days_until_expiry": item.days_until_expiry,
            "is_expired": item.is_expired
        }
        for item in items
    ]


@router.get("/items/{item_id}")
def get_item(item_id: int, session: Session = Depends(get_session)):
    """Get item by ID with computed fields."""
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        **item.model_dump(),
        "expiry_status": item.expiry_status,
        "days_until_expiry": item.days_until_expiry,
        "is_expired": item.is_expired
    }


@router.post("/items")
def create_item(
    item_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Create new inventory item(s). Supports comma-separated names for bulk creation."""
    # Get or create household
    household = crud.get_or_create_household(session)

    # Get or create location
    location_path = item_data.get("location_path")
    if not location_path:
        raise HTTPException(status_code=400, detail="location_path is required")

    location = crud.get_or_create_location_by_path(
        session, location_path, household.id
    )

    # Convert date strings to date objects
    acquired_date = item_data.get("acquired_date")
    if acquired_date and isinstance(acquired_date, str):
        acquired_date = datetime.strptime(acquired_date, "%Y-%m-%d").date()
    elif not acquired_date:
        acquired_date = None

    expiry_date = item_data.get("expiry_date")
    if expiry_date and isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    elif not expiry_date:
        expiry_date = None

    # Check if name contains commas for bulk creation
    name_input = item_data.get("name", "")

    if not name_input or not name_input.strip():
        raise HTTPException(status_code=400, detail="name is required")

    # Check if comma exists (support both English and Chinese commas)
    if "," in name_input or "，" in name_input:
        # Normalize Chinese comma to English comma, then split
        normalized_input = name_input.replace("，", ",")
        names = [n.strip() for n in normalized_input.split(",") if n.strip()]
    else:
        # Single item
        names = [name_input.strip()]

    created_items = []

    # Initialize autocomplete service
    autocomplete_service = LFUAutocompleteService(session, household.id)

    # Create item(s)
    for name in names:
        item = Item(
            name=name,
            category=item_data.get("category"),
            quantity=item_data.get("quantity"),
            unit=item_data.get("unit"),
            location_id=location.id,
            household_id=household.id,
            acquired_date=acquired_date,
            expiry_date=expiry_date,
            notes=item_data.get("notes")
        )
        created_item = crud.create_item(session, item)
        created_items.append(created_item)

    # Record usage in autocomplete cache
    if item_data.get("category"):
        autocomplete_service.record_usage("category", item_data.get("category"))
    if location_path:
        autocomplete_service.record_usage("location_path", location_path)
    if item_data.get("unit"):
        autocomplete_service.record_usage("unit", item_data.get("unit"))

    # Return single item or list based on input
    if len(created_items) == 1:
        return created_items[0]
    else:
        return {
            "message": f"Successfully created {len(created_items)} items",
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "location_id": item.location_id,
                    "household_id": item.household_id,
                    "acquired_date": item.acquired_date.isoformat() if item.acquired_date else None,
                    "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                    "notes": item.notes,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                for item in created_items
            ],
            "count": len(created_items)
        }


@router.put("/items/{item_id}", response_model=Item)
def update_item(
    item_id: int,
    updates: dict,
    session: Session = Depends(get_session)
):
    """Update item."""
    # Handle location_path if provided
    if "location_path" in updates:
        location_path = updates.pop("location_path")
        household = crud.get_or_create_household(session)
        location = crud.get_or_create_location_by_path(
            session, location_path, household.id
        )
        updates["location_id"] = location.id

    # Convert date strings to date objects
    if "acquired_date" in updates:
        if updates["acquired_date"] and isinstance(updates["acquired_date"], str):
            updates["acquired_date"] = datetime.strptime(updates["acquired_date"], "%Y-%m-%d").date()
        elif not updates["acquired_date"]:
            updates["acquired_date"] = None
    if "expiry_date" in updates:
        if updates["expiry_date"] and isinstance(updates["expiry_date"], str):
            updates["expiry_date"] = datetime.strptime(updates["expiry_date"], "%Y-%m-%d").date()
        elif not updates["expiry_date"]:
            updates["expiry_date"] = None

    item = crud.update_item(session, item_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    delete_request: DeleteItemRequest,
    session: Session = Depends(get_session)
):
    """Delete item with reason and logging."""
    # Get item details before deletion
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Create deletion event
    event = Event(
        item_id=item_id,
        event_type="delete",
        quantity_change=-item.quantity,
        notes=f"出库原因: {delete_request.reason}\n出库记录: {delete_request.checkout_record or 'N/A'}"
    )
    session.add(event)
    session.commit()

    # Log the deletion
    log_message = (
        f"删除物品 | "
        f"ID: {item.id} | "
        f"名称: {item.name} | "
        f"类别: {item.category} | "
        f"数量: {item.quantity} {item.unit} | "
        f"位置: {item.location.get_full_path() if item.location else 'Unknown'} | "
        f"出库原因: {delete_request.reason} | "
        f"出库记录: {delete_request.checkout_record or 'N/A'}"
    )
    deletion_logger.info(log_message)

    # Delete the item
    success = crud.delete_item(session, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "message": "Item deleted successfully",
        "deleted_item": {
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit
        }
    }


@router.get("/expiring")
def get_expiring_items(
    household_id: int = Query(default=1),
    days: int = Query(default=7),
    session: Session = Depends(get_session)
):
    """Get items expiring within specified days with computed fields."""
    items = crud.get_expiring_items(session, household_id, days)
    return [
        {
            **item.model_dump(),
            "expiry_status": item.expiry_status,
            "days_until_expiry": item.days_until_expiry,
            "is_expired": item.is_expired
        }
        for item in items
    ]


@router.get("/expired")
def get_expired_items(
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
):
    """Get expired items with computed fields."""
    items = crud.get_expired_items(session, household_id)
    return [
        {
            **item.model_dump(),
            "expiry_status": item.expiry_status,
            "days_until_expiry": item.days_until_expiry,
            "is_expired": item.is_expired
        }
        for item in items
    ]


@router.get("/categories")
def get_categories(
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
):
    """Get all categories."""
    return crud.get_categories(session, household_id)


@router.get("/locations")
def get_locations(
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
):
    """Get location hierarchy."""
    locations = crud.get_location_hierarchy(session, household_id)
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "parent_id": loc.parent_id,
            "full_path": loc.get_full_path()
        }
        for loc in locations
    ]
