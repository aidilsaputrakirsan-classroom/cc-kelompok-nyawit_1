"""
Purchase Requisition router — requester endpoints.

POST /api/v1/requisitions          → create PR + line items (status SUBMITTED)
GET  /api/v1/requisitions          → list PR milik requester (pagination + filter)
GET  /api/v1/requisitions/{id}     → detail PR + line items + status history
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.pr_line_item import PRLineItem
from app.models.purchase_requisition import PurchaseRequisition
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.pr_line_item import ItemOut
from app.schemas.purchase_requisition import PRCreate, PROut, PRUpdate

router = APIRouter(prefix="/api/v1/requisitions", tags=["requisitions"])


def _generate_pr_number() -> str:
    """Generate a PR number like PR-20260415-XXXX using current UTC timestamp."""
    now = datetime.now(timezone.utc)
    # Microseconds provide uniqueness within the same second
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PR-{now.strftime('%Y%m%d')}-{seq}"


# ── POST / ────────────────────────────────────────────────────────
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Buat Purchase Requisition baru",
)
async def create_requisition(
    body: PRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester membuat PR baru beserta line items.
    Status langsung di-set ke SUBMITTED.
    Total amount dihitung otomatis dari line items.
    """
    # Calculate total from line items
    total = sum(
        round(item.quantity * item.estimated_unit_price, 2) for item in body.items
    )

    pr = PurchaseRequisition(
        pr_number=_generate_pr_number(),
        requester_id=current_user.id,
        title=body.title,
        justification=body.justification,
        status=PRStatus.SUBMITTED,
        total_amount=total,
    )
    db.add(pr)
    await db.flush()  # get pr.id before creating line items

    # Create line items
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

    await db.commit()
    await db.refresh(pr, attribute_names=["line_items"])

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Menampilkan daftar PR milik requester yang sedang login.
    Mendukung pagination dan filter berdasarkan status.
    """
    # Base query — only own PRs
    base = select(PurchaseRequisition).where(
        PurchaseRequisition.requester_id == current_user.id
    )

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

    # Fetch page
    offset = (page - 1) * per_page
    rows_q = (
        base.options(selectinload(PurchaseRequisition.line_items))
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
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

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
        .options(selectinload(PurchaseRequisition.line_items))
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

    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya PR dengan status SUBMITTED yang bisa diedit",
        )

    # Update PR fields
    pr.title = body.title
    pr.justification = body.justification

    # Remove old line items
    for old_item in pr.line_items:
        await db.delete(old_item)

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

    await db.commit()
    await db.refresh(pr, attribute_names=["line_items"])

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="Purchase Requisition berhasil diperbarui",
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

    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya PR dengan status SUBMITTED yang bisa dibatalkan",
        )

    await db.delete(pr)
    await db.commit()

    return APIResponse(
        success=True,
        data=None,
        message="Purchase Requisition berhasil dibatalkan dan dihapus",
    )
