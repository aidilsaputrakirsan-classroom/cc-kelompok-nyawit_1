"""
Purchase Requisition router — requester endpoints.

Perbedaan dengan monolith:
- Tidak pakai get_current_user() → pakai verify_token_with_auth_service()
- current_user bukan User object → tapi dict {user_id, email, full_name, role}
- Akses user_id via user["user_id"] bukan current_user.id
"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_client import verify_token_with_auth_service
from database import get_db
from models import PRLineItem, PRStatus, PurchaseRequisition
from schemas import (
    APIResponse, ItemOut, PaginatedResponse, PaginationMeta,
    PRCreate, PROut, PRUpdate,
)

router = APIRouter(prefix="/api/v1/requisitions", tags=["requisitions"])


def _generate_pr_number() -> str:
    now = datetime.now(timezone.utc)
    seq = now.strftime("%H%M%S%f")[:8]
    return f"PR-{now.strftime('%Y%m%d')}-{seq}"


# ── POST / ────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_requisition(
    body: PRCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),  # ← dari Auth Service!
):
    """Requester membuat PR baru."""
    total = sum(
        round(item.quantity * item.estimated_unit_price, 2) for item in body.items
    )

    pr = PurchaseRequisition(
        pr_number=_generate_pr_number(),
        requester_id=user["user_id"],  # ← user_id dari Auth Service response
        title=body.title,
        justification=body.justification,
        status=PRStatus.SUBMITTED,
        total_amount=total,
    )
    db.add(pr)
    await db.flush()

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
@router.get("/")
async def list_my_requisitions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: PRStatus | None = Query(None, alias="status"),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """List PR milik requester yang login."""
    base = select(PurchaseRequisition).where(
        PurchaseRequisition.requester_id == user["user_id"]
    )

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)
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


# ── GET /categories ───────────────────────────────────────────────
@router.get("/categories")
async def get_item_categories(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Get unique categories dari line items milik user."""
    result = await db.execute(
        select(PRLineItem.item_name)
        .join(PurchaseRequisition)
        .where(PurchaseRequisition.requester_id == user["user_id"])
        .distinct()
    )
    item_names = [row[0] for row in result.all()]

    keywords = set()
    for name in item_names:
        words = name.lower().replace("-", " ").replace("_", " ").split()
        keywords.update([w for w in words if len(w) > 2])

    return APIResponse(success=True, data={"categories": sorted(keywords)}, message="OK")


# ── GET /{id} ─────────────────────────────────────────────────────
@router.get("/{pr_id}")
async def get_requisition_detail(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Detail PR + line items."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(status_code=404, detail="Purchase Requisition tidak ditemukan")
    if pr.requester_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke PR ini")

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="OK",
    )


# ── PUT /{id} ─────────────────────────────────────────────────────
@router.put("/{pr_id}")
async def update_requisition(
    pr_id: int,
    body: PRUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Edit PR yang masih SUBMITTED."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(status_code=404, detail="Purchase Requisition tidak ditemukan")
    if pr.requester_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke PR ini")
    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Hanya PR SUBMITTED yang bisa diedit")

    pr.title = body.title
    pr.justification = body.justification
    pr.line_items.clear()
    await db.flush()

    total = sum(round(i.quantity * i.estimated_unit_price, 2) for i in body.items)
    pr.total_amount = total

    for item in body.items:
        subtotal = round(item.quantity * item.estimated_unit_price, 2)
        line = PRLineItem(
            pr_id=pr.id, item_name=item.item_name, quantity=item.quantity,
            unit_of_measure=item.unit_of_measure,
            estimated_unit_price=item.estimated_unit_price, subtotal=subtotal,
        )
        db.add(line)
        pr.line_items.append(line)

    await db.commit()

    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.line_items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message="Purchase Requisition berhasil diperbarui",
    )


# ── DELETE /{id} ──────────────────────────────────────────────────
@router.delete("/{pr_id}")
async def delete_requisition(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Batalkan PR yang masih SUBMITTED."""
    result = await db.execute(
        select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if pr is None:
        raise HTTPException(status_code=404, detail="Purchase Requisition tidak ditemukan")
    if pr.requester_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke PR ini")
    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Hanya PR SUBMITTED yang bisa dibatalkan")

    await db.delete(pr)
    await db.commit()

    return APIResponse(success=True, data=None, message="Purchase Requisition berhasil dibatalkan")
