"""Inventory management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session
from datetime import date, datetime
from pydantic import BaseModel
import logging
import os

from ..database import get_session
from ..models import Item, Event
from .. import crud

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

# Setup logging for deletions
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
deletion_logger = logging.getLogger("inventory_deletions")
deletion_logger.setLevel(logging.INFO)

# Create file handler
log_file = os.path.join(log_dir, "item_deletions.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
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


@router.post("/items", response_model=Item)
def create_item(
    name: str,
    category: str,
    quantity: float,
    unit: str,
    location_path: str,
    household_id: int = 1,
    acquired_date: Optional[date] = None,
    expiry_date: Optional[date] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Create new inventory item."""
    # Get or create household
    household = crud.get_or_create_household(session)

    # Get or create location
    location = crud.get_or_create_location_by_path(
        session, location_path, household.id
    )

    # Create item
    item = Item(
        name=name,
        category=category,
        quantity=quantity,
        unit=unit,
        location_id=location.id,
        household_id=household.id,
        acquired_date=acquired_date,
        expiry_date=expiry_date,
        notes=notes
    )

    return crud.create_item(session, item)


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
