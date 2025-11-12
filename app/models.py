"""Database models for PantryPilot."""
from datetime import datetime, date
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class Household(SQLModel, table=True):
    """Represents a household/home space."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    locations: List["Location"] = Relationship(back_populates="household")
    items: List["Item"] = Relationship(back_populates="household")


class Location(SQLModel, table=True):
    """Hierarchical storage locations (Kitchen > Fridge > Top Shelf)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="location.id")
    household_id: int = Field(foreign_key="household.id")
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    household: Optional[Household] = Relationship(back_populates="locations")
    parent: Optional["Location"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Location.id"}
    )
    children: List["Location"] = Relationship(back_populates="parent")
    items: List["Item"] = Relationship(back_populates="location")

    def get_full_path(self) -> str:
        """Get full hierarchical path (e.g., 'Kitchen > Fridge > Top Shelf')."""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class Item(SQLModel, table=True):
    """Inventory item (product definition)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: str = Field(index=True)  # Food, Tools, Cleaning, etc.
    subcategory: Optional[str] = None  # Dairy, Vegetables, etc.
    quantity: float = Field(default=1.0)
    unit: str = Field(default="count")  # count, kg, g, ml, liter, etc.
    location_id: int = Field(foreign_key="location.id")
    household_id: int = Field(foreign_key="household.id")

    # Dates
    acquired_date: Optional[date] = None
    expiry_date: Optional[date] = None

    # Additional info
    notes: Optional[str] = None
    barcode: Optional[str] = Field(default=None, index=True)
    image_path: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    household: Optional[Household] = Relationship(back_populates="items")
    location: Optional[Location] = Relationship(back_populates="items")

    @property
    def is_expired(self) -> bool:
        """Check if item is expired."""
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry."""
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    @property
    def expiry_status(self) -> str:
        """Get expiry status: expired, expiring_soon, fresh, no_expiry, or n/a."""
        # Check if item is food-related
        food_categories = ["食物", "food", "Food", "食品", "饮料", "Drink", "drinks"]
        is_food = self.category.lower() in [c.lower() for c in food_categories]

        # For non-food items, return n/a
        if not is_food:
            return "n/a"

        # For food items, check expiry date
        if not self.expiry_date:
            return "no_expiry"
        days = self.days_until_expiry
        if days < 0:
            return "expired"
        elif days <= 3:
            return "expiring_soon"
        else:
            return "fresh"


class Event(SQLModel, table=True):
    """Track inventory events (check-in, check-out, move, etc.)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    event_type: str = Field(index=True)  # check_in, check_out, move, update, delete
    quantity_change: Optional[float] = None
    old_location_id: Optional[int] = None
    new_location_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImportHistory(SQLModel, table=True):
    """Track import history to prevent duplicates."""
    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str = Field(index=True)
    file_name: str
    imported_count: int = Field(default=0)
    error_count: int = Field(default=0)
    household_id: int = Field(foreign_key="household.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
