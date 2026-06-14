"""
Purchase Requisition admin router — procurement admin endpoints.

GET  /api/v1/requisitions/admin          → list semua PR (pagination + filter)
PUT  /api/v1/requisitions/admin/{id}/review → approve / reject PR
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_role
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_requisition import PurchaseRequisition
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.purchase_requisition import PROut, PRReviewRequest
from app.services.vendor_quote_rules import (
    VendorQuoteError,
    compute_allocated_budget,
    resolve_selected_vendor,
)

router = APIRouter(prefix="/api/v1/requisitions/admin", tags=["requisitions-admin"])


def _generate_po_number() -> str:
    """Generate a PO number like PO-20260415-XXXXXXXX using current UTC timestamp."""
    now = datetime.now(timezone.utc)
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PO-{now.strftime('%Y%m%d')}-{seq}"


# ── GET / ─────────────────────────────────────────────────────────
@router.get(
    "/",
    summary="List semua PR (admin only)",
)
async def list_all_requisitions(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    status_filter: PRStatus | None = Query(None, alias="status", description="Filter berdasarkan status"),
    requester_id: int | None = Query(None, description="Filter berdasarkan requester ID"),
    category: str | None = Query(None, description="Filter berdasarkan kategori item (mencari di nama item)"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin melihat semua PR dari seluruh requester.
    Mendukung pagination, filter by status, filter by requester, dan filter by kategori.
    Filter kategori akan mencari PR yang memiliki line items dengan nama mengandung kata kunci kategori.
    """
    base = select(PurchaseRequisition)

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)
    if requester_id is not None:
        base = base.where(PurchaseRequisition.requester_id == requester_id)
    
    # Filter by category - find PRs that have line items containing the category keyword
    if category is not None:
        from app.models.pr_line_item import PRLineItem
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

    # Fetch requester names for all PRs in this page
    requester_ids = list({pr.requester_id for pr in prs})
    if requester_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(requester_ids))
        )
        users_map = {u.id: u.full_name for u in users_result.scalars().all()}
    else:
        users_map = {}

    # Add requester_name to each PR
    prs_with_names = []
    for pr in prs:
        pr_dict = PROut.model_validate(pr).model_dump(mode="json")
        pr_dict["requester_name"] = users_map.get(pr.requester_id)
        prs_with_names.append(pr_dict)

    return PaginatedResponse(
        success=True,
        data=prs_with_names,
        message="OK",
        pagination=PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


# ── PUT /{id}/review ──────────────────────────────────────────────
@router.put(
    "/{pr_id}/review",
    summary="Review PR — approve (sekaligus terbitkan PO) atau reject",
)
async def review_requisition(
    pr_id: int,
    body: PRReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin me-review sebuah PR berstatus SUBMITTED.

    - action=REJECT: PR → REJECTED, approval_note wajib.
    - action=APPROVE: terbitkan PO untuk vendor terpilih (default = vendor
      rekomendasi, bisa di-override via selected_vendor_quote_id) dan PR →
      PO_ISSUED dalam satu transaksi. allocated_budget = harga vendor terpilih
      (atau total_amount untuk PR legacy tanpa vendor).
    """
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
            selectinload(PurchaseRequisition.purchase_order),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    # ── REJECT ────────────────────────────────────────────────────
    if body.action == "REJECT":
        if pr.status != PRStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"PR tidak bisa di-review. Status saat ini: {pr.status}. "
                       f"Hanya PR dengan status SUBMITTED yang bisa di-review.",
            )
        pr.status = PRStatus.REJECTED
        pr.approval_note = body.approval_note
        await db.commit()
        pr = await _get_pr_full_admin(db, pr_id)
        return APIResponse(
            success=True,
            data=PROut.model_validate(pr).model_dump(mode="json"),
            message="Purchase Requisition berhasil ditolak",
        )

    # ── APPROVE (+ issue PO) ──────────────────────────────────────
    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PR tidak bisa di-approve. Status saat ini: {pr.status}.",
        )
    if pr.purchase_order is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PO sudah pernah diterbitkan untuk PR ini",
        )

    try:
        selected = resolve_selected_vendor(
            pr.vendor_quotes, body.selected_vendor_quote_id
        )
    except VendorQuoteError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    budget = compute_allocated_budget(selected, pr.total_amount)

    # Update is_recommended flags based on admin's selection
    # Reset all vendor quotes to not recommended
    for quote in pr.vendor_quotes:
        quote.is_recommended = False
    
    # Set the selected vendor as recommended (if there is a selected vendor)
    if selected is not None:
        # Find and mark the selected vendor quote as recommended
        for quote in pr.vendor_quotes:
            if quote.id == selected.id:
                quote.is_recommended = True
                break

    po = PurchaseOrder(
        po_number=_generate_po_number(),
        pr_id=pr.id,
        issued_by=admin.id,
        allocated_budget=float(budget),
        selected_vendor_quote_id=selected.id if selected is not None else None,
    )
    db.add(po)
    pr.status = PRStatus.PO_ISSUED
    pr.approval_note = body.approval_note

    await db.commit()
    pr = await _get_pr_full_admin(db, pr_id)
    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="Purchase Requisition disetujui dan Purchase Order diterbitkan",
    )


async def _get_pr_full_admin(db: AsyncSession, pr_id: int) -> PurchaseRequisition | None:
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.line_items),
            selectinload(PurchaseRequisition.vendor_quotes),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    return result.scalar_one_or_none()


# ── GET /categories ───────────────────────────────────────────────
@router.get(
    "/categories",
    summary="Get unique categories from all line items (admin only)",
)
async def get_all_item_categories(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin mendapatkan daftar kategori unik dari semua item di seluruh sistem.
    Kategori diekstrak dari kata-kata unik dalam item_name.
    """
    from app.models.pr_line_item import PRLineItem
    
    # Get all distinct item names across all PRs
    result = await db.execute(
        select(PRLineItem.item_name).distinct()
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


# ── GET /{id} ─────────────────────────────────────────────────────
# NOTE: Must be declared AFTER /categories so the literal "categories"
# path is matched before this dynamic {pr_id} route.
@router.get(
    "/{pr_id}",
    summary="Detail PR (admin only)",
)
async def get_requisition_detail_admin(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin melihat detail satu PR beserta line items, tanpa batasan kepemilikan.
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

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="OK",
    )
