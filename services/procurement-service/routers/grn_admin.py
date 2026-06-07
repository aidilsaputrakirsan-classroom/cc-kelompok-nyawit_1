"""
GRN admin router — admin verifikasi dokumen.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_client import verify_token_with_auth_service
from database import get_db
from models import GRNDocument, PRStatus, PurchaseOrder
from schemas import APIResponse, GRNOut, GRNVerify

router = APIRouter(prefix="/api/v1/grn/admin", tags=["grn-admin"])


async def _require_admin(request: Request, authorization: str = Header(...)) -> dict:
    user = await verify_token_with_auth_service(request, authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya admin.")
    return user


# ── PUT /{grn_id}/verify ──────────────────────────────────────────
@router.put("/{grn_id}/verify")
async def verify_grn(
    grn_id: int,
    body: GRNVerify,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(_require_admin),
):
    """Admin verifikasi/close GRN."""
    result = await db.execute(
        select(GRNDocument)
        .options(
            selectinload(GRNDocument.purchase_order)
            .selectinload(PurchaseOrder.purchase_requisition)
        )
        .where(GRNDocument.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if grn is None:
        raise HTTPException(status_code=404, detail="GRN Document tidak ditemukan")

    po = grn.purchase_order
    pr = po.purchase_requisition

    # Validate status transition
    valid_transitions = {
        PRStatus.DOC_SUBMITTED: PRStatus.VERIFIED,
        PRStatus.VERIFIED: PRStatus.CLOSED,
    }

    if pr.status not in valid_transitions:
        raise HTTPException(
            status_code=409,
            detail=f"GRN tidak bisa diverifikasi. Status PR: {pr.status}",
        )

    expected_target = valid_transitions[pr.status]
    if body.status != expected_target:
        raise HTTPException(
            status_code=400,
            detail=f"Dari {pr.status}, status selanjutnya harus {expected_target}",
        )

    grn.verification_note = body.verification_note
    pr.status = body.status

    await db.commit()
    await db.refresh(grn)

    label = "diverifikasi" if body.status == PRStatus.VERIFIED else "ditutup (closed)"
    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message=f"GRN berhasil {label}",
    )
