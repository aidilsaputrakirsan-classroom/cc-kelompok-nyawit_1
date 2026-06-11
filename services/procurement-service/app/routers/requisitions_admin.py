import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_role, CurrentUser
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.purchase_requisition import PurchaseRequisition
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.purchase_requisition import PROut, PRStatusUpdate

router = APIRouter(prefix="/api/v1/requisitions/admin", tags=["requisitions-admin"])


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
    db: AsyncSession = Depends(get_db),
    admin: CurrentUser = Depends(require_role(["admin"])),
):
    """
    Admin melihat semua PR dari seluruh requester.
    Mendukung pagination, filter by status, dan filter by requester.
    """
    base = select(PurchaseRequisition)

    if status_filter is not None:
        base = base.where(PurchaseRequisition.status == status_filter)
    if requester_id is not None:
        base = base.where(PurchaseRequisition.requester_id == requester_id)

    count_q = select(func.count()).select_from(base.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / per_page))

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


# ── PUT /{id}/review ──────────────────────────────────────────────
@router.put(
    "/{pr_id}/review",
    summary="Review PR — approve atau reject",
)
async def review_requisition(
    pr_id: int,
    body: PRStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: CurrentUser = Depends(require_role(["admin"])),
):
    """
    Admin meng-approve atau me-reject sebuah PR.
    - Hanya PR dengan status SUBMITTED yang bisa di-review.
    - Status target hanya boleh APPROVED atau REJECTED.
    - approval_note wajib diisi.
    """
    if body.status not in (PRStatus.APPROVED, PRStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status review hanya boleh APPROVED atau REJECTED",
        )

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

    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PR tidak bisa di-review. Status saat ini: {pr.status}. "
                   f"Hanya PR dengan status SUBMITTED yang bisa di-review.",
        )

    pr.status = body.status
    pr.approval_note = body.approval_note

    await db.commit()
    await db.refresh(pr)
    await db.refresh(pr, attribute_names=["line_items"])

    action = "disetujui" if body.status == PRStatus.APPROVED else "ditolak"
    return APIResponse(
        success=True,
        data=PROut.model_validate(pr).model_dump(mode="json"),
        message=f"Purchase Requisition berhasil {action}",
    )
