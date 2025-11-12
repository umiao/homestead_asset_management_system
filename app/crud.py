"""CRUD operations for inventory management."""
from typing import List, Optional
from sqlmodel import Session, select, or_, func
from datetime import date, timedelta
from .models import Household, Location, Item, Event


def get_or_create_household(session: Session, name: str = "My Home") -> Household:
    """Get or create default household."""
    statement = select(Household).where(Household.name == name)
    household = session.exec(statement).first()
    if not household:
        household = Household(name=name, description="Default household")
        session.add(household)
        session.commit()
        session.refresh(household)
    return household


def get_or_create_location_by_path(
    session: Session,
    path: str,
    household_id: int
) -> Location:
    """
    Get or create location from hierarchical path.
    Example: "Kitchen > Fridge > Top Shelf"
    """
    parts = [p.strip() for p in path.split(">")]
    parent = None

    for part in parts:
        # Check if location exists
        statement = select(Location).where(
            Location.name == part,
            Location.household_id == household_id,
            Location.parent_id == (parent.id if parent else None)
        )
        location = session.exec(statement).first()

        if not location:
            location = Location(
                name=part,
                household_id=household_id,
                parent_id=parent.id if parent else None
            )
            session.add(location)
            session.commit()
            session.refresh(location)

        parent = location

    return parent


def create_item(session: Session, item: Item) -> Item:
    """Create new inventory item."""
    session.add(item)
    session.commit()
    session.refresh(item)

    # Log event
    event = Event(
        item_id=item.id,
        event_type="check_in",
        quantity_change=item.quantity,
        new_location_id=item.location_id,
        notes=f"Initial check-in: {item.name}"
    )
    session.add(event)
    session.commit()

    return item


def get_item(session: Session, item_id: int) -> Optional[Item]:
    """Get item by ID."""
    return session.get(Item, item_id)


def get_all_items(
    session: Session,
    household_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Item]:
    """Get all items for a household."""
    statement = select(Item).where(
        Item.household_id == household_id
    ).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def search_items(
    session: Session,
    household_id: int,
    query: Optional[str] = None,
    category: Optional[str] = None,
    location_id: Optional[int] = None,
    expiry_status: Optional[str] = None
) -> List[Item]:
    """Search items with filters."""
    statement = select(Item).where(Item.household_id == household_id)

    if query:
        statement = statement.where(
            or_(
                Item.name.contains(query),
                Item.notes.contains(query)
            )
        )

    if category:
        statement = statement.where(Item.category == category)

    if location_id:
        statement = statement.where(Item.location_id == location_id)

    items = list(session.exec(statement).all())

    # Filter by expiry status if specified
    if expiry_status:
        items = [item for item in items if item.expiry_status == expiry_status]

    return items


def update_item(session: Session, item_id: int, updates: dict) -> Optional[Item]:
    """Update item fields."""
    item = session.get(Item, item_id)
    if not item:
        return None

    old_location_id = item.location_id

    for key, value in updates.items():
        if hasattr(item, key):
            setattr(item, key, value)

    session.add(item)
    session.commit()
    session.refresh(item)

    # Log event if location changed
    if old_location_id != item.location_id:
        event = Event(
            item_id=item.id,
            event_type="move",
            old_location_id=old_location_id,
            new_location_id=item.location_id,
            notes=f"Moved {item.name}"
        )
        session.add(event)
        session.commit()

    return item


def delete_item(session: Session, item_id: int) -> bool:
    """Delete an item."""
    item = session.get(Item, item_id)
    if not item:
        return False

    # Log event
    event = Event(
        item_id=item.id,
        event_type="delete",
        quantity_change=-item.quantity,
        notes=f"Deleted {item.name}"
    )
    session.add(event)

    session.delete(item)
    session.commit()
    return True


def get_expiring_items(
    session: Session,
    household_id: int,
    days: int = 7
) -> List[Item]:
    """Get items expiring within specified days."""
    target_date = date.today() + timedelta(days=days)
    statement = select(Item).where(
        Item.household_id == household_id,
        Item.expiry_date.isnot(None),
        Item.expiry_date <= target_date,
        Item.expiry_date >= date.today()
    )
    return list(session.exec(statement).all())


def get_expired_items(session: Session, household_id: int) -> List[Item]:
    """Get expired items."""
    statement = select(Item).where(
        Item.household_id == household_id,
        Item.expiry_date.isnot(None),
        Item.expiry_date < date.today()
    )
    return list(session.exec(statement).all())


def get_location_hierarchy(session: Session, household_id: int) -> List[Location]:
    """Get all locations for a household."""
    statement = select(Location).where(Location.household_id == household_id)
    return list(session.exec(statement).all())


def get_categories(session: Session, household_id: int) -> List[str]:
    """Get all unique categories."""
    statement = select(Item.category).where(
        Item.household_id == household_id
    ).distinct()
    return list(session.exec(statement).all())
