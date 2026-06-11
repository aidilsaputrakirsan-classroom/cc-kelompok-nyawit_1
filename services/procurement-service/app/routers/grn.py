import os
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_current_user, CurrentUser
from app.db.session import get_db
from app.models.enums import PRStatus
from app.models.grn_document import GRNDocument
from app.models.purchase_order import PurchaseOrder
from app.schemas.common import APIResponse
from app.schemas.grn_document import GRNOut

router = APIRouter(prefix="/api/v1/grn", tags=["grn"])

# ── Constants ─────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = settings.max_upload_bytes  # from config (default 5 MB)


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename.
    """
    name = os.path.basename(filename)
    name = re.sub(r"[^\w.\-]", "_", name)
    name_part, ext = os.path.splitext(name)
    max_name_length = 200
    if len(name_part) > max_name_length:
        name_part = name_part[:max_name_length]
    unique = uuid.uuid4().hex[:12]
    return f"{unique}_{name_part}{ext}"


async def _validate_and_save(
    file: UploadFile,
    upload_dir: Path,
    label: str,
) -> str:
    """
    Validate file type & size, then save to disk.
    Returns the relative path from the project root.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Tipe file tidak diizinkan ({file.content_type}). "
                   f"Hanya JPG, PNG, dan PDF yang diterima.",
        )

    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Ekstensi file tidak diizinkan ({ext}). "
                   f"Hanya .jpg, .jpeg, .png, .pdf yang diterima.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Ukuran file melebihi batas maksimum "
                   f"{settings.MAX_UPLOAD_SIZE_MB}MB "
                   f"({len(content) / (1024*1024):.1f}MB).",
        )

    safe_name = _sanitize_filename(file.filename or "unknown")
    file_path = upload_dir / safe_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return str(file_path)


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
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Requester meng-upload 2 dokumen bukti penerimaan barang:
    1. commercial_invoice — faktur komersial
    2. goods_photo — foto barang
    """
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

    if pr.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk submit dokumen pada PO ini",
        )

    if pr.status != PRStatus.PO_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dokumen hanya bisa di-submit saat status PO_ISSUED. Status saat ini: {pr.status}",
        )

    if po.grn_document is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dokumen GRN sudah pernah di-submit untuk PO ini",
        )

    upload_dir = Path(settings.UPLOAD_DIR) / str(po_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    invoice_path = await _validate_and_save(
        commercial_invoice, upload_dir, "commercial_invoice"
    )
    photo_path = await _validate_and_save(
        goods_photo, upload_dir, "goods_photo"
    )

    grn = GRNDocument(
        po_id=po.id,
        requester_id=current_user.id,
        receipt_url=invoice_path,
        commercial_invoice_url=invoice_path,
        goods_photo_url=photo_path,
    )
    db.add(grn)

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
    current_user: CurrentUser = Depends(get_current_user),
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

    if current_user.id != grn.requester_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk melihat dokumen GRN ini",
        )

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="Detail dokumen GRN berhasil diambil",
    )
