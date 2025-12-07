"""
Router for receipt OCR and batch item import functionality.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from pathlib import Path
from datetime import datetime, date
import shutil
import uuid
import hashlib
from typing import Optional

from ..database import get_session
from .. import crud
from ..models import Item, ImportHistory
from ..auth import get_current_user, require_permission

# Import OCR service with error handling
try:
    from ..services.llm_ocr import LLMOCRService
    OCR_SERVICE_AVAILABLE = True
except ImportError as e:
    OCR_SERVICE_AVAILABLE = False
    print(f"Warning: OCR service not available: {e}")

router = APIRouter(prefix="/api/receipt", tags=["receipt-ocr"])

# Configure upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "receipts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def parse_iso_date(date_str: Optional[str]) -> Optional[date]:
    """
    Parse date in ISO format YYYY-MM-DD only.

    This avoids ambiguity (e.g., 01/02/2025 could be Jan 2 or Feb 1).
    The LLM is instructed to always output dates in ISO format.

    Args:
        date_str: Date string in ISO format YYYY-MM-DD

    Returns:
        date object or None if parsing fails or input is null
    """
    if not date_str or date_str == "null":
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        print(f"Warning: Could not parse date '{date_str}' - expected ISO format YYYY-MM-DD. Error: {e}")
        return None


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_ocr_service():
    """Dependency to get OCR service instance."""
    if not OCR_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OCR service not available. Please install google-genai: pip install google-genai"
        )

    try:
        return LLMOCRService()
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize OCR service: {str(e)}"
        )


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    auto_import: bool = True,
    force_reimport: bool = Query(default=False),
    session: Session = Depends(get_session),
    user: dict = Depends(require_permission("import"))  # Only admin can upload receipts
):
    """
    Upload and process a receipt or product image.

    Args:
        file: The image file to process
        auto_import: If True, automatically import items to inventory
        force_reimport: If True, process even if receipt was already uploaded
        session: Database session

    Returns:
        JSON with extracted items and import results
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"receipt_{timestamp}_{unique_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Calculate file hash to check for duplicates
        file_hash = calculate_file_hash(file_path)

        # Check if this receipt was already imported
        if not force_reimport:
            household = crud.get_or_create_household(session)
            existing = session.exec(
                select(ImportHistory)
                .where(ImportHistory.file_hash == file_hash)
                .where(ImportHistory.household_id == household.id)
            ).first()

            if existing:
                # Delete the newly uploaded file since it's a duplicate
                file_path.unlink()
                return JSONResponse(
                    status_code=409,
                    content={
                        "success": False,
                        "error": "Duplicate receipt detected",
                        "message": f"This receipt was already processed on {existing.created_at.strftime('%Y-%m-%d %H:%M')}",
                        "existing_import": {
                            "id": existing.id,
                            "file_name": existing.file_name,
                            "imported_count": existing.imported_count,
                            "created_at": existing.created_at.isoformat()
                        }
                    }
                )

        # Process with OCR
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.process_receipt(str(file_path))

        if not ocr_result.get("success"):
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "OCR processing failed",
                    "details": ocr_result.get("error"),
                    "file_path": str(file_path)
                }
            )

        items_data = ocr_result.get("items", [])

        # Auto-import if requested
        import_results = []
        if auto_import and items_data:
            household = crud.get_or_create_household(session)

            for item_data in items_data:
                try:
                    # Get or create location
                    location_path = item_data.get("location_path")
                    if not location_path:
                        raise ValueError("Missing location_path")

                    location = crud.get_or_create_location_by_path(
                        session, location_path, household.id
                    )

                    # Parse dates in ISO format only (YYYY-MM-DD)
                    acquired_date = None
                    if item_data.get("acquired_date"):
                        acquired_date = parse_iso_date(item_data.get("acquired_date"))

                    expiry_date = None
                    if item_data.get("expiry_date"):
                        expiry_date = parse_iso_date(item_data.get("expiry_date"))

                    # Create item
                    item = Item(
                        name=item_data.get("name"),
                        category=item_data.get("category"),
                        quantity=item_data.get("quantity", 1.0),
                        unit=item_data.get("unit", "count"),
                        location_id=location.id,
                        household_id=household.id,
                        acquired_date=acquired_date,
                        expiry_date=expiry_date,
                        notes=item_data.get("notes")
                    )

                    created_item = crud.create_item(session, item)
                    import_results.append({
                        "success": True,
                        "item_id": created_item.id,
                        "item_name": created_item.name
                    })

                except Exception as e:
                    import_results.append({
                        "success": False,
                        "item_name": item_data.get("name", "Unknown"),
                        "error": str(e)
                    })

            # Create import history record
            successful_count = sum(1 for r in import_results if r["success"])
            failed_count = sum(1 for r in import_results if not r["success"])

            import_history = ImportHistory(
                file_path=str(file_path),
                file_name=f"OCR: {filename}",
                file_hash=file_hash,
                imported_count=successful_count,
                error_count=failed_count,
                household_id=household.id,
                notes=f"AI-powered receipt scan - {len(items_data)} items recognized"
            )
            session.add(import_history)
            session.commit()
            session.refresh(import_history)

        # Return results
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": filename,
            "ocr_result": {
                "items_found": len(items_data),
                "items": items_data
            },
            "import_results": {
                "auto_import": auto_import,
                "total": len(import_results),
                "successful": sum(1 for r in import_results if r["success"]),
                "failed": sum(1 for r in import_results if not r["success"]),
                "details": import_results
            }
        }

    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Error processing receipt: {str(e)}"
        )


@router.get("/status")
async def get_ocr_status(
    user: dict = Depends(get_current_user)  # All authenticated users can check status
):
    """Check if OCR service is available and configured."""
    if not OCR_SERVICE_AVAILABLE:
        return {
            "available": False,
            "error": "google-genai package not installed",
            "install_command": "pip install google-genai"
        }

    try:
        service = LLMOCRService()
        return {
            "available": True,
            "model": service.model,
            "api_key_configured": bool(service.api_key)
        }
    except ValueError as e:
        return {
            "available": False,
            "error": str(e),
            "instructions": [
                "1. Copy config.secret.example to config.secret",
                "2. Get API key from https://aistudio.google.com/app/apikey",
                "3. Add your key to config.secret"
            ]
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/history")
async def get_receipt_history(
    user: dict = Depends(get_current_user)  # All authenticated users can view history
):
    """Get list of uploaded receipt files."""
    try:
        receipts = []
        for file_path in UPLOAD_DIR.glob("receipt_*"):
            stat = file_path.stat()
            receipts.append({
                "filename": file_path.name,
                "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size_bytes": stat.st_size,
                "path": str(file_path)
            })

        # Sort by upload time (newest first)
        receipts.sort(key=lambda x: x["uploaded_at"], reverse=True)

        return {
            "total": len(receipts),
            "receipts": receipts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving receipt history: {str(e)}"
        )
