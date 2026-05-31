"""
GRN (Goods Received Note) router — requester upload dokumen.
"""

import os
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_client import verify_token_with_auth_service
from database import get_db
from models import GRNDocument, PRStatus, PurchaseOrder, PurchaseRequisition
from schemas import APIResponse, GRNOut

router = APIRouter(prefix="/api/v1/grn", tags=["grn"])

# ── Constants ─────────────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
MAX_FILE_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def _sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    name = re.sub(r"[^\w.\-]", "_", name)
    name_part, ext = os.path.splitext(name)
    if len(name_part) > 200:
        name_part = name_part[:200]
    unique = uuid.uuid4().hex[:12]
    return f"{unique}_{name_part}{ext}"


async def _validate_and_save(file: UploadFile, upload_dir: Path, label: str) -> str:
    """Validasi file dan simpan ke disk."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{label}: Tipe file tidak diizinkan ({file.content_type}). Hanya JPG, PNG, PDF.",
        )

    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"{label}: Ekstensi tidak diizinkan ({ext}). Hanya .jpg, .jpeg, .png, .pdf.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"{label}: File terlalu besar ({len(content)/(1024*1024):.1f}MB). Max {MAX_UPLOAD_SIZE_MB}MB.",
        )

    safe_name = _sanitize_filename(file.filename or "unknown")
    file_path = upload_dir / safe_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return str(file_path)


# ── POST /{po_id}/submit-doc ──────────────────────────────────────
@router.post("/{po_id}/submit-doc", status_code=status.HTTP_201_CREATED)
async def submit_grn_documents(
    po_id: int,
    commercial_invoice: UploadFile = File(...),
    goods_photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Requester upload dokumen bukti penerimaan barang."""
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
        raise HTTPException(status_code=404, detail="Purchase Order tidak ditemukan")

    pr = po.purchase_requisition
    if pr.requester_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses untuk PO ini")
    if pr.status != PRStatus.PO_ISSUED:
        raise HTTPException(
            status_code=409,
            detail=f"Dokumen hanya bisa di-submit saat PO_ISSUED. Status: {pr.status}",
        )
    if po.grn_document is not None:
        raise HTTPException(status_code=409, detail="GRN sudah pernah di-submit untuk PO ini")

    # Save files
    upload_dir = Path(UPLOAD_DIR) / str(po_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    invoice_path = await _validate_and_save(commercial_invoice, upload_dir, "commercial_invoice")
    photo_path = await _validate_and_save(goods_photo, upload_dir, "goods_photo")

    grn = GRNDocument(
        po_id=po.id,
        requester_id=user["user_id"],
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
@router.get("/{grn_id}")
async def get_grn_document(
    grn_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token_with_auth_service),
):
    """Get GRN document details."""
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
        raise HTTPException(status_code=404, detail="GRN document tidak ditemukan")

    # Check access: requester yang submit atau admin
    if user["user_id"] != grn.requester_id and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke GRN ini")

    return APIResponse(
        success=True,
        data=GRNOut.model_validate(grn).model_dump(mode="json"),
        message="OK",
    )
