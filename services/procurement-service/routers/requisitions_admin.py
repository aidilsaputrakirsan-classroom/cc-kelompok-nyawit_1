"""
Purchase Requisition admin router — admin-only endpoints.

Perbedaan dengan monolith:
- Role check dilakukan via Auth Service (bukan query DB lokal)
- Admin user adalah dict, bukan User ORM object
"""

import math

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_client import verify_token_with_auth_service
from database import get_db
from models import PRLineItem, PRStatus, PurchaseRequisition
from schemas import (
    APIResponse, PaginatedResponse, PaginationMeta, PROut, PRStatusUpdate,
)

router = APIRouter(prefix="/api/v1/requisitions/admin", tags=["requisitions-admin"])


async def _require_admin(authorization: str = Header(...)) -> dict:
    """Dependency: pastikan user adalah admin."""
    user = await verify_token_with_auth_service(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya admin.")
    return user


# ── GET / ─────────────────────────────────────────────────────────
@router.get("/")
async def list_all_requisitions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: PRStatus | None = Query(None, alias="status"),
    requester_id: int | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin melihat semua PR."""
    base = select(PurchaseRequisition)

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)
    if requester_id is not None:
        base = base.where(PurchaseRequisition.requester_id == requester_id)
    if category is not None:
        base = base.join(PRLineItem).where(
            PRLineItem.item_name.ilike(f"%{category}%")
        ).distinct()

    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

    offset = (page - 1) * per_page
    rows_q = (
        base.options(selectinload(PurchaseRequisition.line_items))
        .order_by(PurchaseRequisition.created_at.desc())
        .offset(offset).limit(per_page)
    )
    result = await db.execute(rows_q)
    prs = result.scalars().all()

    return PaginatedResponse(
        success=True,
        data=[PROut.model_validate(pr).model_dump(mode="json") for pr in prs],
        message="OK",
        pagination=PaginationMeta(
            page=page, per_page=per_page,
            total_items=total_items, total_pages=total_pages,
        ),
    )


# ── PUT /{id}/review ──────────────────────────────────────────────
@router.put("/{pr_id}/review")
async def review_requisition(
    pr_id: int,
    body: PRStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin approve/reject PR."""
    if body.status not in (PRStatus.APPROVED, PRStatus.REJECTED):
        raise HTTPException(status_code=400, detail="Status hanya boleh APPROVED atau REJECTED")

    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(status_code=404, detail="Purchase Requisition tidak ditemukan")
    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(
            status_code=409,
            detail=f"Hanya PR SUBMITTED yang bisa di-review. Status saat ini: {pr.status}",
        )

    pr.status = body.status
    pr.approval_note = body.approval_note

    await db.commit()

    # Re-fetch PR untuk mendapatkan updated_at yang baru
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    action = "disetujui" if body.status == PRStatus.APPROVED else "ditolak"
    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message=f"Purchase Requisition berhasil {action}",
    )


# ── GET /categories ───────────────────────────────────────────────
@router.get("/categories")
async def get_all_item_categories(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin: get semua kategori unik."""
    result = await db.execute(select(PRLineItem.item_name).distinct())
    item_names = [row[0] for row in result.all()]

    keywords = set()
    for name in item_names:
        words = name.lower().replace("-", " ").replace("_", " ").split()
        keywords.update([w for w in words if len(w) > 2])

    return APIResponse(success=True, data={"categories": sorted(keywords)}, message="OK")
