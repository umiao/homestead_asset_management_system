"""Data import endpoints for TSV/CSV files."""
import csv
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body
from sqlmodel import Session
from datetime import datetime, date
from io import StringIO
from pydantic import BaseModel

from ..database import get_session
from ..models import Item
from .. import crud

router = APIRouter(prefix="/api/import", tags=["import"])


class ImportFileRequest(BaseModel):
    """Request model for file path import."""
    file_path: str
    household_id: int = 1


def parse_quantity(quantity_str: str) -> float:
    """Parse quantity, handling Chinese characters."""
    if not quantity_str or quantity_str.strip() == "":
        return 1.0

    quantity_str = quantity_str.strip()

    # Try direct conversion first
    try:
        return float(quantity_str)
    except ValueError:
        pass

    # Handle common Chinese quantity indicators
    chinese_numbers = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '百': 100, '千': 1000, '万': 10000,
        '零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4,
        '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
        '拾': 10, '佰': 100, '仟': 1000, '萬': 10000,
        '多个': 2, '多': 2, '若干': 1, '一些': 2,
        '几个': 2, '数个': 2, '少许': 1
    }

    # Check if it's a known Chinese phrase
    if quantity_str in chinese_numbers:
        return float(chinese_numbers[quantity_str])

    # Try to extract numbers from mixed strings
    import re
    numbers = re.findall(r'\d+\.?\d*', quantity_str)
    if numbers:
        return float(numbers[0])

    # Default to 1 if can't parse
    return 1.0


def parse_date(date_str: str) -> date:
    """Parse date from string. Supports multiple formats."""
    if not date_str or date_str.strip() == "":
        return None

    # Try multiple date formats
    formats = [
        "%Y-%m-%d",      # 2025-01-15
        "%m/%d/%Y",      # 11/12/2025
        "%d/%m/%Y",      # 15/01/2025
        "%Y/%m/%d",      # 2025/01/15
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    # If no format matches, return None
    return None


@router.post("/tsv")
async def import_tsv(
    file: UploadFile = File(...),
    household_id: int = 1,
    session: Session = Depends(get_session)
):
    """Import inventory from TSV file."""
    if not file.filename.endswith(('.tsv', '.csv', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="File must be TSV or CSV format"
        )

    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    # Determine delimiter
    delimiter = '\t' if file.filename.endswith('.tsv') else ','

    # Parse TSV/CSV
    reader = csv.DictReader(StringIO(content_str), delimiter=delimiter)

    # Get or create household
    household = crud.get_or_create_household(session)

    imported_items = []
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            # Extract data
            name = row.get('name', '').strip()
            category = row.get('category', 'Miscellaneous').strip()
            quantity = parse_quantity(row.get('quantity', '1'))
            unit = row.get('unit', 'count').strip()
            location_path = row.get('location_path', 'Uncategorized').strip()
            acquired_date = parse_date(row.get('acquired_date', ''))
            expiry_date = parse_date(row.get('expiry_date', ''))
            notes = row.get('notes', '').strip()

            if not name:
                errors.append(f"Row {row_num}: Missing item name")
                continue

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

            created_item = crud.create_item(session, item)
            imported_items.append(created_item)

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return {
        "message": f"Import completed",
        "imported_count": len(imported_items),
        "error_count": len(errors),
        "errors": errors,
        "items": [item.id for item in imported_items]
    }


@router.post("/tsv/file-path")
def import_tsv_from_path(
    request: ImportFileRequest,
    session: Session = Depends(get_session)
):
    """Import inventory from TSV file path (for local files)."""
    file_path = request.file_path
    household_id = request.household_id
    try:
        # Determine delimiter
        delimiter = '\t' if file_path.endswith('.tsv') else ','

        # Get or create household
        household = crud.get_or_create_household(session)

        imported_items = []
        errors = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Extract data
                    name = row.get('name', '').strip()
                    category = row.get('category', 'Miscellaneous').strip()
                    quantity = parse_quantity(row.get('quantity', '1'))
                    unit = row.get('unit', 'count').strip()
                    location_path = row.get('location_path', 'Uncategorized').strip()
                    acquired_date = parse_date(row.get('acquired_date', ''))
                    expiry_date = parse_date(row.get('expiry_date', ''))
                    notes = row.get('notes', '').strip()

                    if not name:
                        errors.append(f"Row {row_num}: Missing item name")
                        continue

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

                    created_item = crud.create_item(session, item)
                    imported_items.append(created_item)

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

        return {
            "message": f"Import completed",
            "imported_count": len(imported_items),
            "error_count": len(errors),
            "errors": errors,
            "items": [item.id for item in imported_items]
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
