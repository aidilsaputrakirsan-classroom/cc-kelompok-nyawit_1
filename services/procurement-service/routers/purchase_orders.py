"""
Purchase Order router — issue PO & list PO.
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_client import verify_token_with_auth_service
from database import get_db
from models import PRStatus, PurchaseOrder, PurchaseRequisition
from schemas import APIResponse, PaginatedResponse, PaginationMeta, POOut

router = APIRouter(prefix="/api/v1/purchase-orders", tags=["purchase-orders"])


async def _require_admin(authorization: str = Header(...)) -> dict:
    user = await verify_token_with_auth_service(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya admin.")
    return user


def _generate_po_number() -> str:
    now = datetime.now(timezone.utc)
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PO-{now.strftime('%Y%m%d')}-{seq}"


# ── POST /{pr_id}/issue ───────────────────────────────────────────
@router.post("/{pr_id}/issue", status_code=status.HTTP_201_CREATED)
async def issue_purchase_order(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin menerbitkan PO untuk PR yang sudah APPROVED."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.purchase_order))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(status_code=404, detail="Purchase Requisition tidak ditemukan")
    if pr.status != PRStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=f"PO hanya untuk PR APPROVED. Status saat ini: {pr.status}",
        )
    if pr.purchase_order is not None:
        raise HTTPException(status_code=409, detail="PO sudah pernah diterbitkan untuk PR ini")

    po = PurchaseOrder(
        po_number=_generate_po_number(),
        pr_id=pr.id,
        issued_by=admin["user_id"],  # ← user_id dari Auth Service
        allocated_budget=float(pr.total_amount),
    )
    db.add(po)
    pr.status = PRStatus.PO_ISSUED

    await db.commit()
    await db.refresh(po)

    return APIResponse(
        success=True,
        data=POOut.model_validate(po).model_dump(mode="json"),
        message="Purchase Order berhasil diterbitkan",
    )


# ── GET /{pr_id}/my-po ───────────────────────────────────────────
@router.get("/{pr_id}/my-po")
async def get_my_po_for_pr(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Requester melihat PO untuk PR miliknya."""
    result = await db.execute(
        select(PurchaseRequisition).where(
            PurchaseRequisition.id == pr_id,
            PurchaseRequisition.requester_id == user["user_id"],
        )
    )
    pr = result.scalar_one_or_none()
    if pr is None:
        raise HTTPException(status_code=404, detail="PR tidak ditemukan atau bukan milik Anda")

    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.pr_id == pr_id)
    )
    po = result.scalar_one_or_none()
    if po is None:
        raise HTTPException(status_code=404, detail="PO belum diterbitkan untuk PR ini")

    return APIResponse(
        success=True,
        data=POOut.model_validate(po).model_dump(mode="json"),
        message="OK",
    )


# ── GET / ─────────────────────────────────────────────────────────
@router.get("/")
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin: list semua PO."""
    base = select(PurchaseOrder)

    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

    offset = (page - 1) * per_page
    rows_q = base.order_by(PurchaseOrder.issued_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(rows_q)
    pos = result.scalars().all()

    return PaginatedResponse(
        success=True,
        data=[POOut.model_validate(po).model_dump(mode="json") for po in pos],
        message="OK",
        pagination=PaginationMeta(
            page=page, per_page=per_page,
            total_items=total_items, total_pages=total_pages,
        ),
    )
