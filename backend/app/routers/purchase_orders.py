"""
Purchase Order router — admin-only endpoints.

POST /api/v1/purchase-orders/{pr_id}/issue  → generate PO dari PR yang APPROVED
GET  /api/v1/purchase-orders                → list semua PO yang sudah diterbitkan
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_requisition import PurchaseRequisition
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.purchase_order import POOut

router = APIRouter(prefix="/api/v1/purchase-orders", tags=["purchase-orders"])


def _generate_po_number() -> str:
    """Generate a PO number like PO-20260415-XXXXXXXX using current UTC timestamp."""
    now = datetime.now(timezone.utc)
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PO-{now.strftime('%Y%m%d')}-{seq}"


# ── POST /{pr_id}/issue ───────────────────────────────────────────
@router.post(
    "/{pr_id}/issue",
    status_code=status.HTTP_201_CREATED,
    summary="Terbitkan Purchase Order dari PR yang sudah APPROVED",
)
async def issue_purchase_order(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin menerbitkan PO resmi untuk PR yang sudah di-approve.
    - Hanya PR dengan status APPROVED yang bisa diterbitkan PO-nya.
    - Satu PR hanya bisa punya satu PO (unique constraint).
    - Budget dialokasikan = total_amount dari PR.
    - Status PR berubah menjadi PO_ISSUED.
    - Mencatat issued_by (admin ID) dan timestamp.
    """
    # Fetch PR
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.purchase_order))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan",
        )

    # Must be APPROVED
    if pr.status != PRStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PO hanya bisa diterbitkan untuk PR dengan status APPROVED. "
                   f"Status saat ini: {pr.status}",
        )

    # Check if PO already exists for this PR
    if pr.purchase_order is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PO sudah pernah diterbitkan untuk PR ini",
        )

    # Create PO
    po = PurchaseOrder(
        po_number=_generate_po_number(),
        pr_id=pr.id,
        issued_by=admin.id,
        allocated_budget=float(pr.total_amount),
    )
    db.add(po)

    # Update PR status
    pr.status = PRStatus.PO_ISSUED

    await db.commit()
    await db.refresh(po)

    return APIResponse(
        success=True,
        data=POOut.model_validate(po).model_dump(mode="json"),
        message="Purchase Order berhasil diterbitkan",
    )


# ── GET /{pr_id}/my-po ───────────────────────────────────────────
@router.get(
    "/{pr_id}/my-po",
    summary="Lihat PO untuk PR tertentu (requester)",
)
async def get_my_po_for_pr(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester dapat melihat PO yang diterbitkan untuk PR miliknya.
    Hanya requester yang memiliki PR tersebut yang bisa mengakses.
    """
    # Verify PR exists and belongs to the requester
    result = await db.execute(
        select(PurchaseRequisition).where(
            PurchaseRequisition.id == pr_id,
            PurchaseRequisition.requester_id == current_user.id
        )
    )
    pr = result.scalar_one_or_none()
    
    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Requisition tidak ditemukan atau bukan milik Anda",
        )
    
    # Fetch PO for this PR
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.pr_id == pr_id)
    )
    po = result.scalar_one_or_none()
    
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order belum diterbitkan untuk PR ini",
        )
    
    return APIResponse(
        success=True,
        data=POOut.model_validate(po).model_dump(mode="json"),
        message="OK",
    )


# ── GET / ─────────────────────────────────────────────────────────
@router.get(
    "/",
    summary="List semua Purchase Order",
)
async def list_purchase_orders(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin melihat daftar semua PO yang sudah diterbitkan.
    Mendukung pagination.
    """
    base = select(PurchaseOrder)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

    # Fetch page
    offset = (page - 1) * per_page
    rows_q = (
        base.order_by(PurchaseOrder.issued_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(rows_q)
    pos = result.scalars().all()

    return PaginatedResponse(
        success=True,
        data=[POOut.model_validate(po).model_dump(mode="json") for po in pos],
        message="OK",
        pagination=PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )
