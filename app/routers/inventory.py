"""Inventory management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from datetime import date

from ..database import get_session
from ..models import Item
from .. import crud

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/items", response_model=List[Item])
def list_items(
    household_id: int = Query(default=1),
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List all inventory items."""
    return crud.get_all_items(session, household_id, skip, limit)


@router.get("/items/search", response_model=List[Item])
def search_items(
    household_id: int = Query(default=1),
    q: Optional[str] = None,
    category: Optional[str] = None,
    location_id: Optional[int] = None,
    expiry_status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Search items with filters."""
    return crud.search_items(
        session,
        household_id,
        query=q,
        category=category,
        location_id=location_id,
        expiry_status=expiry_status
    )


@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int, session: Session = Depends(get_session)):
    """Get item by ID."""
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


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
    item = crud.update_item(session, item_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    """Delete item."""
    success = crud.delete_item(session, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@router.get("/expiring", response_model=List[Item])
def get_expiring_items(
    household_id: int = Query(default=1),
    days: int = Query(default=7),
    session: Session = Depends(get_session)
):
    """Get items expiring within specified days."""
    return crud.get_expiring_items(session, household_id, days)


@router.get("/expired", response_model=List[Item])
def get_expired_items(
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
):
    """Get expired items."""
    return crud.get_expired_items(session, household_id)


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
