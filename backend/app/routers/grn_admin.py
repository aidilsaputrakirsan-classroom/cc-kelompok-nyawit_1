"""
GRN admin router — admin verification endpoints.

PUT /api/v1/grn/admin/{id}/verify  → admin verifikasi dokumen GRN
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_role
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.grn_document import GRNDocument
from app.models.purchase_order import PurchaseOrder
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.grn_document import GRNOut, GRNReturn, GRNVerify

router = APIRouter(prefix="/api/v1/grn/admin", tags=["grn-admin"])


# ── PUT /{grn_id}/verify ──────────────────────────────────────────
@router.put(
    "/{grn_id}/verify",
    summary="Verifikasi dokumen GRN",
)
async def verify_grn(
    grn_id: int,
    body: GRNVerify,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin me-review dokumen GRN dan mengubah status:
    - VERIFIED  → dokumen sudah diverifikasi
    - CLOSED    → proses procurement selesai

    Hanya GRN yang PR-nya berstatus DOC_SUBMITTED (untuk VERIFIED)
    atau VERIFIED (untuk CLOSED) yang bisa diproses.
    verification_note wajib diisi.
    """
    # Fetch GRN with PO → PR chain loaded eagerly
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN Document tidak ditemukan",
        )

    # Navigate to PR through PO
    po = grn.purchase_order
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data inkonsisten: PO tidak ditemukan untuk GRN ini",
        )

    pr = po.purchase_requisition
    if pr is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data inkonsisten: PR tidak ditemukan untuk PO ini",
        )

    # Validate status transition
    valid_transitions = {
        PRStatus.DOC_SUBMITTED: PRStatus.VERIFIED,
        PRStatus.VERIFIED: PRStatus.CLOSED,
    }

    if pr.status not in valid_transitions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GRN tidak bisa diverifikasi. Status PR saat ini: {pr.status}. "
                   f"Status yang valid: {', '.join(str(s) for s in valid_transitions.keys())}",
        )

    expected_target = valid_transitions[pr.status]
    if body.status != expected_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status target tidak valid. Dari {pr.status}, "
                   f"status selanjutnya harus {expected_target}",
        )

    # Update
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


# ── PUT /{grn_id}/return ──────────────────────────────────────────
@router.put(
    "/{grn_id}/return",
    summary="Kembalikan dokumen GRN ke requester untuk diperbaiki",
)
async def return_grn(
    grn_id: int,
    body: GRNReturn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Admin mengembalikan dokumen GRN yang tidak sesuai ke requester.
    - Hanya GRN yang PR-nya berstatus DOC_SUBMITTED yang bisa dikembalikan.
    - Status PR dikembalikan ke PO_ISSUED sehingga requester bisa upload ulang.
    - verification_note diisi sebagai alasan pengembalian (terlihat oleh requester).
    - Record GRN dipertahankan; file akan ditimpa saat requester submit ulang.
    """
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN Document tidak ditemukan",
        )

    po = grn.purchase_order
    if po is None or po.purchase_requisition is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data inkonsisten: PO/PR tidak ditemukan untuk GRN ini",
        )

    pr = po.purchase_requisition

    if pr.status != PRStatus.DOC_SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GRN tidak bisa dikembalikan. Status PR saat ini: {pr.status}. "
                   f"Hanya GRN dengan status DOC_SUBMITTED yang bisa dikembalikan.",
        )

    grn.verification_note = body.verification_note
    pr.status = PRStatus.PO_ISSUED

    await db.commit()
    await db.refresh(grn)

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="Dokumen GRN dikembalikan ke requester untuk diperbaiki",
    )
