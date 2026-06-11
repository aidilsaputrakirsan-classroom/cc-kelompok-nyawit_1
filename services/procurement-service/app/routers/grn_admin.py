from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_role, CurrentUser
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.grn_document import GRNDocument
from app.models.purchase_order import PurchaseOrder
from app.schemas.common import APIResponse
from app.schemas.grn_document import GRNOut, GRNVerify

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
    admin: CurrentUser = Depends(require_role(["admin"])),
):
    """
    Admin me-review dokumen GRN dan mengubah status:
    - VERIFIED  → dokumen sudah diverifikasi
    - CLOSED    → proses procurement selesai
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
            detail=f"Status target tidak valid. Dari {pr.status}, status selanjutnya harus {expected_target}",
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
