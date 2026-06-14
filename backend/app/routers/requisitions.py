"""
Purchase Requisition router — requester endpoints.

POST /api/v1/requisitions          → create PR + line items (status SUBMITTED)
GET  /api/v1/requisitions          → list PR milik requester (pagination + filter)
GET  /api/v1/requisitions/{id}     → detail PR + line items + status history
"""

import json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.datastructures import UploadFile

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.pr_line_item import PRLineItem
from app.models.purchase_requisition import PurchaseRequisition
from app.models.user import User
from app.models.vendor_quote import VendorQuote
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.pr_line_item import ItemSchema
from app.schemas.purchase_requisition import PROut, PRUpdate
from app.schemas.vendor_quote import VendorQuoteIn
from app.services.vendor_quote_rules import (
    VendorQuoteError,
    validate_single_recommended,
    validate_vendor_count,
)
from app.utils.uploads import validate_and_save

router = APIRouter(prefix="/api/v1/requisitions", tags=["requisitions"])

_VENDOR_FILE_RE = re.compile(r"^vendor_quotes\[(\d+)\]\.survey_evidence$")


def _generate_pr_number() -> str:
    """Generate a PR number like PR-20260415-XXXX using current UTC timestamp."""
    now = datetime.now(timezone.utc)
    # Microseconds provide uniqueness within the same second
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PR-{now.strftime('%Y%m%d')}-{seq}"


def _cleanup_files(paths: list[str]) -> None:
    """Best-effort removal of files saved during a failed transaction (Req 1.7)."""
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
        except OSError:
            pass


async def _parse_pr_multipart(request: Request):
    """Parse multipart PR payload: fields, items_json, vendor_quotes_json, files.

    Returns (title, justification, items, quotes, files_by_index).
    Raises HTTPException 400 on malformed input.
    """
    form = await request.form()

    title = (form.get("title") or "").strip()
    justification = form.get("justification")
    if justification is not None:
        justification = justification.strip() or None

    items_json = form.get("items_json")
    vendor_quotes_json = form.get("vendor_quotes_json")

    if not title:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Judul PR wajib diisi.")
    if not items_json:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Daftar item (items_json) wajib diisi.")
    if not vendor_quotes_json:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Penawaran vendor (vendor_quotes_json) wajib diisi.",
        )

    try:
        items = [ItemSchema.model_validate(i) for i in json.loads(items_json)]
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Format item tidak valid: {e}")
    if not items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Minimal 1 line item diperlukan.")

    try:
        quotes = [VendorQuoteIn.model_validate(q) for q in json.loads(vendor_quotes_json)]
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Format penawaran vendor tidak valid: {e}"
        )
    if not quotes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Minimal satu penawaran vendor diperlukan."
        )

    files: dict[int, UploadFile] = {}
    for key, value in form.multi_items():
        m = _VENDOR_FILE_RE.match(key)
        if m and isinstance(value, UploadFile):
            files[int(m.group(1))] = value

    return title, justification, items, quotes, files


def _validate_vendor_rules(total: float, quotes: list[VendorQuoteIn], files: dict[int, UploadFile]) -> None:
    """Validate vendor count, single recommended, and per-vendor file presence."""
    threshold = Decimal(str(settings.QUOTE_THRESHOLD))
    try:
        validate_vendor_count(Decimal(str(total)), threshold, len(quotes))
        validate_single_recommended([q.is_recommended for q in quotes])
    except VendorQuoteError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    for idx in range(len(quotes)):
        if idx not in files:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Vendor #{idx + 1}: berkas bukti survei wajib diunggah.",
            )


async def _get_pr_full(db: AsyncSession, pr_id: int) -> PurchaseRequisition | None:
    """Fetch a PR with line_items and vendor_quotes eagerly loaded."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    return result.scalar_one_or_none()


# ── POST / ────────────────────────────────────────────────────────
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Buat Purchase Requisition baru (multipart + penawaran vendor)",
)
async def create_requisition(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester membuat PR baru beserta line items dan penawaran vendor.

    Body: multipart/form-data
      - title, justification
      - items_json: JSON array line items
      - vendor_quotes_json: JSON array metadata vendor
      - vendor_quotes[i].survey_evidence: berkas bukti survei per vendor

    Status langsung SUBMITTED. Total dihitung dari line items. Jumlah minimal
    vendor mengikuti ambang nilai. Transaksi atomik: bila gagal di tengah,
    seluruh PR dibatalkan dan berkas yang sempat tersimpan dibersihkan.
    """
    title, justification, items, quotes, files = await _parse_pr_multipart(request)

    total = sum(round(item.quantity * item.estimated_unit_price, 2) for item in items)

    # Validasi aturan vendor sebelum menyentuh database (Req 1.6, 3.x, 4.x, 2.5)
    _validate_vendor_rules(total, quotes, files)

    pr = PurchaseRequisition(
        pr_number=_generate_pr_number(),
        requester_id=current_user.id,
        title=title,
        justification=justification,
        status=PRStatus.SUBMITTED,
        total_amount=total,
    )
    db.add(pr)

    saved_paths: list[str] = []
    try:
        await db.flush()  # dapatkan pr.id & pr.pr_number

        # Line items
        for item in items:
            subtotal = round(item.quantity * item.estimated_unit_price, 2)
            db.add(
                PRLineItem(
                    pr_id=pr.id,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit_of_measure=item.unit_of_measure,
                    estimated_unit_price=item.estimated_unit_price,
                    subtotal=subtotal,
                )
            )

        # Vendor quotes + bukti survei
        upload_dir = Path(settings.UPLOAD_DIR) / "vendor_quotes" / pr.pr_number
        upload_dir.mkdir(parents=True, exist_ok=True)
        for idx, q in enumerate(quotes):
            path = await validate_and_save(
                files[idx], upload_dir, f"Vendor #{idx + 1} bukti survei"
            )
            saved_paths.append(path)
            db.add(
                VendorQuote(
                    pr_id=pr.id,
                    vendor_name=q.vendor_name,
                    vendor_contact=q.vendor_contact,
                    quoted_price=q.quoted_price,
                    survey_date=q.survey_date,
                    survey_evidence_url=path,
                    is_recommended=q.is_recommended,
                )
            )

        await db.commit()
    except HTTPException:
        await db.rollback()
        _cleanup_files(saved_paths)
        raise
    except Exception:
        # Req 1.7: jangan tinggalkan PR tanpa vendor quote
        await db.rollback()
        _cleanup_files(saved_paths)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal membuat Purchase Requisition.",
        )

    pr = await _get_pr_full(db, pr.id)
    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="Purchase Requisition berhasil dibuat",
    )


# ── GET / ─────────────────────────────────────────────────────────
@router.get(
    "/",
    summary="List PR milik requester",
)
async def list_my_requisitions(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    status_filter: PRStatus | None = Query(None, alias="status", description="Filter berdasarkan status"),
    category: str | None = Query(None, description="Filter berdasarkan kategori item (mencari di nama item)"),
    q: str | None = Query(None, description="Search by keyword in title or justification"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menampilkan daftar PR milik requester yang sedang login.
    Mendukung pagination, filter berdasarkan status dan kategori, serta pencarian bebas.
    Filter kategori akan mencari PR yang memiliki line items dengan nama mengandung kata kunci kategori.
    Search (q) akan mencari PR dengan title atau justification yang mengandung keyword.
    """
    # Base query — only own PRs
    base = select(PurchaseRequisition).where(
        PurchaseRequisition.requester_id == current_user.id
    )

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)
    
    # Search by keyword in title or justification
    if q:
        from sqlalchemy import or_
        base = base.where(
            or_(
                PurchaseRequisition.title.ilike(f"%{q}%"),
                PurchaseRequisition.justification.ilike(f"%{q}%")
            )
        )
    
    # Filter by category - find PRs that have line items containing the category keyword
    if category is not None:
        base = (
            base.join(PRLineItem)
            .where(PRLineItem.item_name.ilike(f"%{category}%"))
            .distinct()
        )

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

    # Fetch page
    offset = (page - 1) * per_page
    rows_q = (
        base.options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
        )
        .order_by(PurchaseRequisition.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(rows_q)
    prs = result.scalars().all()

    return PaginatedResponse(
        success=True,
        data=[PROut.model_validate(pr).model_dump(mode="json") for pr in prs],
        message="OK",
        pagination=PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


# ── GET /{id} ─────────────────────────────────────────────────────
@router.get(
    "/{pr_id}",
    summary="Detail PR + line items",
)
async def get_requisition_detail(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menampilkan detail PR beserta line items.
    Requester hanya bisa melihat PR miliknya sendiri.
    """
    pr = await _get_pr_full(db, pr_id)

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    # Requester can only see their own PRs
    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke PR ini",
        )

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="OK",
    )


# ── GET /categories ───────────────────────────────────────────────
@router.get(
    "/categories",
    summary="Get unique categories from line items",
)
async def get_item_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan daftar kategori unik dari nama item yang pernah dibuat.
    Kategori diekstrak dari kata-kata unik dalam item_name.
    """
    # Get all distinct item names for this user
    result = await db.execute(
        select(PRLineItem.item_name)
        .join(PurchaseRequisition)
        .where(PurchaseRequisition.requester_id == current_user.id)
        .distinct()
    )
    item_names = [row[0] for row in result.all()]
    
    # Extract unique keywords (simple approach: split by space and get unique words)
    keywords = set()
    for name in item_names:
        # Split by common separators and get individual words
        words = name.lower().replace('-', ' ').replace('_', ' ').split()
        keywords.update([word for word in words if len(word) > 2])  # Filter out very short words
    
    # Return sorted list of keywords as potential categories
    categories = sorted(list(keywords))
    
    return APIResponse(
        success=True,
        data={"categories": categories},
        message="OK",
    )


# ── PUT /{id} ─────────────────────────────────────────────────────
@router.put(
    "/{pr_id}",
    summary="Edit PR yang masih SUBMITTED",
)
async def update_requisition(
    pr_id: int,
    body: PRUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester mengedit PR yang masih berstatus SUBMITTED.
    Hanya pemilik PR yang bisa mengedit.
    Line items lama dihapus dan diganti dengan yang baru.
    """
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke PR ini",
        )

    if pr.status not in (PRStatus.SUBMITTED, PRStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya PR berstatus SUBMITTED atau REJECTED yang bisa diedit",
        )

    # Track whether this is a revision of a rejected PR (resubmit flow)
    was_rejected = pr.status == PRStatus.REJECTED

    # Update PR fields
    pr.title = body.title
    pr.justification = body.justification

    # Remove old line items by clearing the relationship list
    # This triggers cascade delete automatically
    pr.line_items.clear()
    await db.flush()  # Ensure deletions are processed

    # Calculate new total and create new line items
    total = sum(
        round(item.quantity * item.estimated_unit_price, 2) for item in body.items
    )
    pr.total_amount = total

    for item in body.items:
        subtotal = round(item.quantity * item.estimated_unit_price, 2)
        line = PRLineItem(
            pr_id=pr.id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit_of_measure=item.unit_of_measure,
            estimated_unit_price=item.estimated_unit_price,
            subtotal=subtotal,
        )
        db.add(line)
        # Explicitly add to relationship list
        pr.line_items.append(line)

    # If this was a rejected PR, re-validate the existing vendor quotes against
    # the new total (Req 8.4), then resubmit it (REJECTED → SUBMITTED).
    if was_rejected:
        threshold = Decimal(str(settings.QUOTE_THRESHOLD))
        try:
            validate_vendor_count(Decimal(str(total)), threshold, len(pr.vendor_quotes))
            validate_single_recommended([q.is_recommended for q in pr.vendor_quotes])
        except VendorQuoteError as e:
            await db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        pr.status = PRStatus.SUBMITTED
        pr.approval_note = None

    await db.commit()

    # Re-fetch the PR with relationships eagerly loaded
    pr = await _get_pr_full(db, pr_id)

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message=(
            "Purchase Requisition berhasil direvisi dan diajukan ulang"
            if was_rejected
            else "Purchase Requisition berhasil diperbarui"
        ),
    )


@router.put(
    "/{pr_id}/vendors",
    summary="Update vendor quotes untuk PR yang masih SUBMITTED",
)
async def update_vendor_quotes(
    pr_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester mengedit vendor quotes pada PR yang masih berstatus SUBMITTED atau REJECTED.
    Hanya pemilik PR yang bisa mengedit.
    Mendukung file upload untuk survey evidence.
    """
    # Fetch PR with vendor quotes
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke PR ini",
        )

    if pr.status not in (PRStatus.SUBMITTED, PRStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya PR berstatus SUBMITTED atau REJECTED yang bisa diedit",
        )

    # Parse multipart form data
    form = await request.form()
    vendor_quotes_json = form.get("vendor_quotes_json")

    if not vendor_quotes_json:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Penawaran vendor (vendor_quotes_json) wajib diisi.",
        )

    try:
        quotes_data = [VendorQuoteIn.model_validate(q) for q in json.loads(vendor_quotes_json)]
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Format penawaran vendor tidak valid: {e}"
        )

    if not quotes_data:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Minimal satu penawaran vendor diperlukan."
        )

    # Parse uploaded files
    files: dict[int, UploadFile] = {}
    for key, value in form.multi_items():
        m = _VENDOR_FILE_RE.match(key)
        if m and isinstance(value, UploadFile):
            files[int(m.group(1))] = value

    # Validate vendor rules
    total = float(pr.total_amount)
    threshold = Decimal(str(settings.QUOTE_THRESHOLD))
    try:
        validate_vendor_count(Decimal(str(total)), threshold, len(quotes_data))
        validate_single_recommended([q.is_recommended for q in quotes_data])
    except VendorQuoteError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    # Check that each vendor has a file (either new upload or existing)
    for idx in range(len(quotes_data)):
        if idx not in files:
            # Check if there's an existing file we can keep
            existing_quote = pr.vendor_quotes[idx] if idx < len(pr.vendor_quotes) else None
            if not existing_quote or not existing_quote.survey_evidence_url:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Vendor #{idx + 1}: berkas bukti survei wajib diunggah.",
                )

    # Save existing file URLs before clearing
    existing_file_urls = [q.survey_evidence_url for q in pr.vendor_quotes]

    # Delete old vendor quotes and their files (only if new file uploaded)
    saved_paths: list[str] = []
    for quote in pr.vendor_quotes:
        if quote.survey_evidence_url:
            try:
                Path(quote.survey_evidence_url).unlink(missing_ok=True)
            except OSError:
                pass
    pr.vendor_quotes.clear()
    await db.flush()

    # Create new vendor quotes with uploaded files
    for idx, quote_data in enumerate(quotes_data):
        # Handle file upload
        if idx in files:
            evidence_url = await validate_and_save(files[idx], user_id=current_user.id, prefix="vendor_quotes")
            saved_paths.append(evidence_url)
        else:
            # Keep existing file URL
            evidence_url = existing_file_urls[idx] if idx < len(existing_file_urls) else None

        quote = VendorQuote(
            pr_id=pr.id,
            vendor_name=quote_data.vendor_name,
            vendor_contact=quote_data.vendor_contact,
            quoted_price=quote_data.quoted_price,
            survey_date=quote_data.survey_date,
            survey_evidence_url=evidence_url,
            is_recommended=quote_data.is_recommended,
        )
        db.add(quote)
        pr.vendor_quotes.append(quote)

    # If this was a rejected PR, resubmit it
    was_rejected = pr.status == PRStatus.REJECTED
    if was_rejected:
        pr.status = PRStatus.SUBMITTED
        pr.approval_note = None

    await db.commit()

    # Re-fetch the PR with relationships eagerly loaded
    pr = await _get_pr_full(db, pr_id)

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message=(
            "Vendor quotes berhasil direvisi dan PR diajukan ulang"
            if was_rejected
            else "Vendor quotes berhasil diperbarui"
        ),
    )


# ── DELETE /{id} ──────────────────────────────────────────────────
@router.delete(
    "/{pr_id}",
    summary="Batalkan / hapus PR yang masih SUBMITTED",
)
async def delete_requisition(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester membatalkan/menghapus PR yang masih berstatus SUBMITTED.
    Hanya pemilik PR yang bisa menghapus.
    PR beserta line items akan dihapus permanen.
    """
    result = await db.execute(
        select(PurchaseRequisition)
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke PR ini",
        )

    if pr.status not in (PRStatus.SUBMITTED, PRStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya PR berstatus SUBMITTED atau REJECTED yang bisa dibatalkan",
        )

    await db.delete(pr)
    await db.commit()

    return APIResponse(
        success=True,
        data=None,
        message="Purchase Requisition berhasil dibatalkan dan dihapus",
    )
