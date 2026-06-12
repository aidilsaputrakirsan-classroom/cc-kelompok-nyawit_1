"""
GRN (Goods Received Note) router — requester endpoints.

POST /api/v1/grn/{po_id}/submit-doc  → upload commercial_invoice & goods_photo
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.grn_document import GRNDocument
from app.models.purchase_order import PurchaseOrder
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.grn_document import GRNOut
from app.utils.uploads import validate_and_save as _validate_and_save

router = APIRouter(prefix="/api/v1/grn", tags=["grn"])


# ── POST /{po_id}/submit-doc ──────────────────────────────────────
@router.post(
    "/{po_id}/submit-doc",
    status_code=status.HTTP_201_CREATED,
    summary="Upload dokumen GRN (commercial invoice & goods photo)",
)
async def submit_grn_documents(
    po_id: int,
    commercial_invoice: UploadFile = File(
        ..., description="File commercial invoice (JPG/PNG/PDF, max 5MB)"
    ),
    goods_photo: UploadFile = File(
        ..., description="Foto barang diterima (JPG/PNG/PDF, max 5MB)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Requester meng-upload 2 dokumen bukti penerimaan barang:
    1. commercial_invoice — faktur komersial
    2. goods_photo — foto barang

    Validasi:
    - Tipe file: JPG, PNG, PDF
    - Ukuran max: 5MB per file
    - Hanya bisa dilakukan jika status PR = PO_ISSUED
    - Satu PO hanya bisa punya satu GRN submission

    Setelah berhasil, status PR berubah ke DOC_SUBMITTED.
    File disimpan di backend/uploads/{po_id}/.
    """
    # Fetch PO with its PR
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.purchase_requisition),
            selectinload(PurchaseOrder.grn_document),
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order tidak ditemukan",
        )

    pr = po.purchase_requisition

    # Only the requester who owns the PR can submit GRN
    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk submit dokumen pada PO ini",
        )

    # Status must be PO_ISSUED.
    # Note: an existing GRN with PR back at PO_ISSUED means it was returned by
    # the admin for correction, so re-submission (overwrite) is allowed here.
    if pr.status != PRStatus.PO_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dokumen hanya bisa di-submit saat status PO_ISSUED. "
                   f"Status saat ini: {pr.status}",
        )

    # Create upload directory: backend/uploads/{po_id}/
    upload_dir = Path(settings.UPLOAD_DIR) / str(po_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Validate and save files
    invoice_path = await _validate_and_save(
        commercial_invoice, upload_dir, "commercial_invoice"
    )
    photo_path = await _validate_and_save(
        goods_photo, upload_dir, "goods_photo"
    )

    if po.grn_document is not None:
        # Re-submission after a returned GRN — update the existing record in place
        grn = po.grn_document
        grn.receipt_url = invoice_path
        grn.commercial_invoice_url = invoice_path
        grn.goods_photo_url = photo_path
        grn.requester_id = current_user.id
        grn.verification_note = None  # clear the previous return reason
        grn.submitted_at = func.now()
    else:
        # First-time submission
        grn = GRNDocument(
            po_id=po.id,
            requester_id=current_user.id,
            receipt_url=invoice_path,  # receipt_url stores the primary document
            commercial_invoice_url=invoice_path,
            goods_photo_url=photo_path,
        )
        db.add(grn)

    # Update PR status to DOC_SUBMITTED
    pr.status = PRStatus.DOC_SUBMITTED

    await db.commit()
    await db.refresh(grn)

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="Dokumen GRN berhasil di-submit",
    )


# ── GET /{grn_id} ─────────────────────────────────────────────────
@router.get(
    "/{grn_id}",
    summary="Get GRN document details by ID",
)
async def get_grn_document(
    grn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve GRN document details by ID.
    Only accessible by the requester who submitted the GRN or admin users.
    """
    result = await db.execute(
        select(GRNDocument)
        .options(
            selectinload(GRNDocument.purchase_order).selectinload(PurchaseOrder.purchase_requisition)
        )
        .where(GRNDocument.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if grn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN document tidak ditemukan",
        )

    # Check permissions: only requester who owns it or admins can view
    po = grn.purchase_order
    pr = po.purchase_requisition
    
    # Check if current user is the requester who submitted this GRN or an admin
    if current_user.id != grn.requester_id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk melihat dokumen GRN ini",
        )

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="Detail dokumen GRN berhasil diambil",
    )



# ── GET /by-po/{po_id} ────────────────────────────────────────────
@router.get(
    "/by-po/{po_id}",
    summary="Get GRN document by Purchase Order ID",
)
async def get_grn_by_po(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil dokumen GRN berdasarkan PO ID.
    Hanya bisa diakses oleh requester pemilik PR terkait atau admin.
    Mengembalikan GRN id yang sebenarnya (tidak menebak dari po_id).
    """
    result = await db.execute(
        select(GRNDocument)
        .options(
            selectinload(GRNDocument.purchase_order).selectinload(
                PurchaseOrder.purchase_requisition
            )
        )
        .where(GRNDocument.po_id == po_id)
    )
    grn = result.scalar_one_or_none()

    if grn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokumen GRN belum di-submit untuk PO ini",
        )

    # Permission: requester owner of the PR or admin
    is_admin = current_user.role.value == "admin" if hasattr(
        current_user.role, "value"
    ) else str(current_user.role) == "admin"
    if not is_admin and current_user.id != grn.requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk melihat dokumen GRN ini",
        )

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="OK",
    )
