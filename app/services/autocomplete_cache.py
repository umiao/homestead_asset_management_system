"""
LFU (Least Frequently Used) Cache for Autocomplete Suggestions

This module provides an LFU cache implementation for maintaining frequently used
values for fields like Category, Location Path, and Unit in the Add Item form.

Features:
- Tracks usage frequency for each field value
- Automatically evicts least frequently used items when cache is full
- Provides ranked suggestions based on frequency
- Supports multiple cache types (category, location_path, unit, etc.)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlmodel import Field, SQLModel, Session, select, or_
from collections import defaultdict
import json


class AutocompleteCache(SQLModel, table=True):
    """
    Database model for LFU autocomplete cache.

    Each record represents a cached value for a specific field type
    with its usage frequency and timestamp.
    """
    __tablename__ = "autocomplete_cache"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Field type: 'category', 'location_path', 'unit', 'name_prefix', etc.
    field_type: str = Field(index=True)

    # The cached value (e.g., "Food", "Kitchen > Fridge", "kg")
    value: str = Field(index=True)

    # Usage frequency count (LFU score)
    frequency: int = Field(default=1)

    # Last time this value was used
    last_used: datetime = Field(default_factory=datetime.utcnow)

    # Timestamp when first cached
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Household association for multi-tenant support
    household_id: int = Field(foreign_key="household.id", default=1)

    class Config:
        # Unique constraint: one entry per field_type + value + household
        table_args = (
            {"sqlite_autoincrement": True},
        )


class LFUAutocompleteService:
    """
    Service class for managing LFU autocomplete cache.

    Provides methods for:
    - Recording field usage
    - Getting top suggestions
    - Cleaning up least frequently used entries
    - Managing cache size
    """

    # Default maximum cache size per field type
    DEFAULT_MAX_CACHE_SIZE = 100

    # Minimum frequency to keep in cache (auto-cleanup threshold)
    MIN_FREQUENCY_THRESHOLD = 2

    def __init__(self, session: Session, household_id: int = 1):
        """
        Initialize the LFU autocomplete service.

        Args:
            session: SQLModel database session
            household_id: ID of the household (for multi-tenant support)
        """
        self.session = session
        self.household_id = household_id

    def record_usage(self, field_type: str, value: str) -> None:
        """
        Record usage of a field value, incrementing its frequency.

        If the value doesn't exist in cache, creates a new entry.
        If it exists, increments frequency and updates last_used timestamp.

        Args:
            field_type: Type of field ('category', 'location_path', etc.)
            value: The value that was used
        """
        if not value or not value.strip():
            return

        value = value.strip()

        # Check if entry already exists
        statement = select(AutocompleteCache).where(
            AutocompleteCache.field_type == field_type,
            AutocompleteCache.value == value,
            AutocompleteCache.household_id == self.household_id
        )
        cache_entry = self.session.exec(statement).first()

        if cache_entry:
            # Increment frequency and update timestamp
            cache_entry.frequency += 1
            cache_entry.last_used = datetime.utcnow()
        else:
            # Create new cache entry
            cache_entry = AutocompleteCache(
                field_type=field_type,
                value=value,
                frequency=1,
                household_id=self.household_id
            )
            self.session.add(cache_entry)

        self.session.commit()

        # Cleanup if cache is too large
        self._cleanup_if_needed(field_type)

    def get_suggestions(
        self,
        field_type: str,
        query: str = "",
        limit: int = 10,
        min_frequency: int = 1
    ) -> List[Dict]:
        """
        Get ranked autocomplete suggestions for a field.

        Returns suggestions sorted by frequency (descending), optionally
        filtered by a query string.

        Args:
            field_type: Type of field ('category', 'location_path', etc.)
            query: Optional query string to filter suggestions (case-insensitive)
            limit: Maximum number of suggestions to return
            min_frequency: Minimum frequency threshold for suggestions

        Returns:
            List of suggestion dictionaries with keys:
            - value: The suggestion text
            - frequency: Usage frequency count
            - last_used: Last usage timestamp
        """
        statement = select(AutocompleteCache).where(
            AutocompleteCache.field_type == field_type,
            AutocompleteCache.household_id == self.household_id,
            AutocompleteCache.frequency >= min_frequency
        )

        # Filter by query if provided
        if query:
            statement = statement.where(
                AutocompleteCache.value.ilike(f"%{query}%")
            )

        # Order by frequency (descending), then by last_used (descending)
        statement = statement.order_by(
            AutocompleteCache.frequency.desc(),
            AutocompleteCache.last_used.desc()
        ).limit(limit)

        results = self.session.exec(statement).all()

        return [
            {
                "value": entry.value,
                "frequency": entry.frequency,
                "last_used": entry.last_used.isoformat()
            }
            for entry in results
        ]

    def get_top_suggestions(self, field_type: str, limit: int = 10) -> List[str]:
        """
        Get top N suggestions for a field (simple string list).

        Args:
            field_type: Type of field
            limit: Maximum number of suggestions

        Returns:
            List of suggestion strings, ordered by frequency
        """
        suggestions = self.get_suggestions(field_type, limit=limit)
        return [s["value"] for s in suggestions]

    def _cleanup_if_needed(self, field_type: str) -> None:
        """
        Clean up cache if it exceeds maximum size.

        Removes least frequently used entries when cache size exceeds limit.

        Args:
            field_type: Type of field to clean up
        """
        # Count current cache size for this field type
        statement = select(AutocompleteCache).where(
            AutocompleteCache.field_type == field_type,
            AutocompleteCache.household_id == self.household_id
        )
        entries = self.session.exec(statement).all()

        current_size = len(entries)

        if current_size > self.DEFAULT_MAX_CACHE_SIZE:
            # Calculate how many to remove
            to_remove = current_size - self.DEFAULT_MAX_CACHE_SIZE

            # Sort by frequency (ascending) to get least frequently used
            sorted_entries = sorted(entries, key=lambda x: (x.frequency, x.last_used))

            # Remove least frequently used entries
            for entry in sorted_entries[:to_remove]:
                self.session.delete(entry)

            self.session.commit()

    def cleanup_low_frequency(self, field_type: Optional[str] = None) -> int:
        """
        Remove entries with very low frequency (cleanup maintenance).

        Args:
            field_type: Optional field type to clean (None = all types)

        Returns:
            Number of entries removed
        """
        statement = select(AutocompleteCache).where(
            AutocompleteCache.household_id == self.household_id,
            AutocompleteCache.frequency < self.MIN_FREQUENCY_THRESHOLD
        )

        if field_type:
            statement = statement.where(AutocompleteCache.field_type == field_type)

        entries = self.session.exec(statement).all()

        for entry in entries:
            self.session.delete(entry)

        self.session.commit()

        return len(entries)

    def get_statistics(self, field_type: Optional[str] = None) -> Dict:
        """
        Get cache statistics.

        Args:
            field_type: Optional field type to get stats for (None = all types)

        Returns:
            Dictionary with cache statistics:
            - total_entries: Total number of cached entries
            - by_field_type: Breakdown by field type
            - top_values: Most frequently used values
        """
        statement = select(AutocompleteCache).where(
            AutocompleteCache.household_id == self.household_id
        )

        if field_type:
            statement = statement.where(AutocompleteCache.field_type == field_type)

        entries = self.session.exec(statement).all()

        # Group by field type
        by_field_type = defaultdict(lambda: {"count": 0, "total_frequency": 0})

        for entry in entries:
            by_field_type[entry.field_type]["count"] += 1
            by_field_type[entry.field_type]["total_frequency"] += entry.frequency

        # Get top values across all field types
        top_entries = sorted(entries, key=lambda x: x.frequency, reverse=True)[:20]
        top_values = [
            {
                "field_type": entry.field_type,
                "value": entry.value,
                "frequency": entry.frequency,
                "last_used": entry.last_used.isoformat()
            }
            for entry in top_entries
        ]

        return {
            "total_entries": len(entries),
            "by_field_type": dict(by_field_type),
            "top_values": top_values
        }

    def initialize_from_existing_data(self) -> Dict[str, int]:
        """
        Initialize cache from existing inventory data.

        Scans existing items in the database and populates the cache
        with categories, location paths, and units.

        Returns:
            Dictionary with count of entries created per field type
        """
        from app.models import Item, Location

        counts = {"category": 0, "location_path": 0, "unit": 0}

        # Get all items for this household
        item_statement = select(Item).where(Item.household_id == self.household_id)
        items = self.session.exec(item_statement).all()

        # Count frequency of each category and unit
        category_freq = defaultdict(int)
        unit_freq = defaultdict(int)
        location_path_freq = defaultdict(int)

        for item in items:
            if item.category:
                category_freq[item.category] += 1
            if item.unit:
                unit_freq[item.unit] += 1

            # Get location path
            if item.location:
                location_path = self._get_location_full_path(item.location_id)
                if location_path:
                    location_path_freq[location_path] += 1

        # Bulk insert categories
        for category, freq in category_freq.items():
            # Check if already exists
            statement = select(AutocompleteCache).where(
                AutocompleteCache.field_type == "category",
                AutocompleteCache.value == category,
                AutocompleteCache.household_id == self.household_id
            )
            existing = self.session.exec(statement).first()

            if not existing:
                cache_entry = AutocompleteCache(
                    field_type="category",
                    value=category,
                    frequency=freq,
                    household_id=self.household_id
                )
                self.session.add(cache_entry)
                counts["category"] += 1

        # Bulk insert units
        for unit, freq in unit_freq.items():
            statement = select(AutocompleteCache).where(
                AutocompleteCache.field_type == "unit",
                AutocompleteCache.value == unit,
                AutocompleteCache.household_id == self.household_id
            )
            existing = self.session.exec(statement).first()

            if not existing:
                cache_entry = AutocompleteCache(
                    field_type="unit",
                    value=unit,
                    frequency=freq,
                    household_id=self.household_id
                )
                self.session.add(cache_entry)
                counts["unit"] += 1

        # Bulk insert location paths
        for location_path, freq in location_path_freq.items():
            statement = select(AutocompleteCache).where(
                AutocompleteCache.field_type == "location_path",
                AutocompleteCache.value == location_path,
                AutocompleteCache.household_id == self.household_id
            )
            existing = self.session.exec(statement).first()

            if not existing:
                cache_entry = AutocompleteCache(
                    field_type="location_path",
                    value=location_path,
                    frequency=freq,
                    household_id=self.household_id
                )
                self.session.add(cache_entry)
                counts["location_path"] += 1

        self.session.commit()

        return counts

    def _get_location_full_path(self, location_id: int) -> Optional[str]:
        """
        Get full hierarchical path for a location.

        Args:
            location_id: ID of the location

        Returns:
            Full path string like "Kitchen > Fridge > Top Shelf"
        """
        from app.models import Location

        statement = select(Location).where(Location.id == location_id)
        location = self.session.exec(statement).first()

        if not location:
            return None

        # Build path by traversing parent hierarchy
        parts = []
        current = location

        while current:
            parts.insert(0, current.name)
            if current.parent_id:
                parent_statement = select(Location).where(Location.id == current.parent_id)
                current = self.session.exec(parent_statement).first()
            else:
                current = None

        return " > ".join(parts)
