"""
API endpoints for autocomplete suggestions with LFU cache.

Provides endpoints for:
- Getting autocomplete suggestions for various fields
- Recording field usage
- Managing and monitoring cache statistics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session
from typing import List, Dict, Optional
from app.database import get_session
from app.services.autocomplete_cache import LFUAutocompleteService

router = APIRouter(prefix="/api/autocomplete", tags=["autocomplete"])


@router.get("/suggestions/{field_type}")
def get_autocomplete_suggestions(
    field_type: str,
    query: str = Query(default="", description="Search query to filter suggestions"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions"),
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> List[Dict]:
    """
    Get autocomplete suggestions for a specific field type.

    Supported field types:
    - category: Product categories (Food, Tools, Cleaning, etc.)
    - location_path: Hierarchical location paths (Kitchen > Fridge > Top Shelf)
    - unit: Measurement units (kg, g, liter, count, etc.)
    - name_prefix: Common item name prefixes

    Args:
        field_type: Type of field to get suggestions for
        query: Optional search query to filter suggestions (case-insensitive)
        limit: Maximum number of suggestions to return (1-50)
        household_id: Household ID for multi-tenant support

    Returns:
        List of suggestion dictionaries with:
        - value: The suggestion text
        - frequency: Usage frequency count
        - last_used: Last usage timestamp (ISO format)

    Example:
        GET /api/autocomplete/suggestions/category?query=food&limit=5
        Response:
        [
            {"value": "Food", "frequency": 145, "last_used": "2025-12-04T10:30:00"},
            {"value": "Food > Dairy", "frequency": 42, "last_used": "2025-12-03T15:20:00"}
        ]
    """
    service = LFUAutocompleteService(session, household_id)

    try:
        suggestions = service.get_suggestions(
            field_type=field_type,
            query=query,
            limit=limit
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/suggestions/{field_type}/simple")
def get_simple_suggestions(
    field_type: str,
    limit: int = Query(default=10, ge=1, le=50),
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> List[str]:
    """
    Get simple list of autocomplete suggestions (values only).

    Returns only the suggestion values without metadata,
    suitable for simple dropdown/datalist population.

    Args:
        field_type: Type of field to get suggestions for
        limit: Maximum number of suggestions
        household_id: Household ID

    Returns:
        List of suggestion strings, ordered by frequency

    Example:
        GET /api/autocomplete/suggestions/category/simple?limit=5
        Response: ["Food", "Tools", "Cleaning", "Office", "Garden"]
    """
    service = LFUAutocompleteService(session, household_id)

    try:
        suggestions = service.get_top_suggestions(field_type, limit)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/record")
def record_field_usage(
    field_type: str = Query(..., description="Type of field used"),
    value: str = Query(..., description="Value that was used"),
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Record usage of a field value to update LFU cache.

    This endpoint should be called when a user selects or enters
    a value in the Add Item form to track usage frequency.

    Args:
        field_type: Type of field ('category', 'location_path', etc.)
        value: The value that was used
        household_id: Household ID

    Returns:
        Success confirmation with updated frequency

    Example:
        POST /api/autocomplete/record?field_type=category&value=Food
        Response: {"success": true, "field_type": "category", "value": "Food"}
    """
    if not value or not value.strip():
        raise HTTPException(status_code=400, detail="Value cannot be empty")

    service = LFUAutocompleteService(session, household_id)

    try:
        service.record_usage(field_type, value)
        return {
            "success": True,
            "field_type": field_type,
            "value": value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record usage: {str(e)}")


@router.get("/statistics")
def get_cache_statistics(
    field_type: Optional[str] = Query(default=None, description="Optional field type filter"),
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Get statistics about the autocomplete cache.

    Useful for monitoring cache size, usage patterns, and debugging.

    Args:
        field_type: Optional field type to get stats for (None = all types)
        household_id: Household ID

    Returns:
        Dictionary with:
        - total_entries: Total number of cached entries
        - by_field_type: Breakdown by field type (count, total frequency)
        - top_values: Most frequently used values across all types

    Example:
        GET /api/autocomplete/statistics
        Response:
        {
            "total_entries": 245,
            "by_field_type": {
                "category": {"count": 12, "total_frequency": 1250},
                "location_path": {"count": 45, "total_frequency": 890}
            },
            "top_values": [...]
        }
    """
    service = LFUAutocompleteService(session, household_id)

    try:
        stats = service.get_statistics(field_type)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/initialize")
def initialize_cache_from_data(
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Initialize autocomplete cache from existing inventory data.

    Scans all items in the database and populates the cache with
    categories, location paths, and units based on existing usage.

    This should be run once when setting up the cache for the first time,
    or to rebuild the cache from scratch.

    Args:
        household_id: Household ID

    Returns:
        Dictionary with count of entries created per field type

    Example:
        POST /api/autocomplete/initialize
        Response:
        {
            "success": true,
            "counts": {
                "category": 12,
                "location_path": 45,
                "unit": 8
            },
            "message": "Cache initialized successfully"
        }
    """
    service = LFUAutocompleteService(session, household_id)

    try:
        counts = service.initialize_from_existing_data()
        return {
            "success": True,
            "counts": counts,
            "message": "Cache initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize cache: {str(e)}")


@router.post("/cleanup")
def cleanup_cache(
    field_type: Optional[str] = Query(default=None, description="Optional field type to clean"),
    household_id: int = Query(default=1),
    session: Session = Depends(get_session)
) -> Dict:
    """
    Clean up low-frequency entries from the cache.

    Removes entries with very low usage frequency (maintenance operation).

    Args:
        field_type: Optional field type to clean (None = all types)
        household_id: Household ID

    Returns:
        Dictionary with number of entries removed

    Example:
        POST /api/autocomplete/cleanup?field_type=category
        Response: {"success": true, "removed_count": 15}
    """
    service = LFUAutocompleteService(session, household_id)

    try:
        removed_count = service.cleanup_low_frequency(field_type)
        return {
            "success": True,
            "removed_count": removed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup cache: {str(e)}")
