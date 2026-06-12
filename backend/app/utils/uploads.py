"""
Shared file-upload utilities.

Centralizes validation, sanitization, and saving of uploaded files so that
both the GRN router and the vendor-quote (PR creation) flow share identical,
well-tested behavior.
"""

import os
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# ── Constants ─────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = settings.max_upload_bytes  # from config (default 5 MB)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename:
    - Strip directory components (path traversal protection)
    - Remove non-alphanumeric chars (except dot, hyphen, underscore)
    - Prepend a UUID to guarantee uniqueness
    - Limit total length to avoid filesystem limits
    """
    # Take only the basename (strip path traversal)
    name = os.path.basename(filename)
    # Remove any character that is not alphanumeric, dot, hyphen, or underscore
    name = re.sub(r"[^\w.\-]", "_", name)

    # Split name and extension to handle them separately
    name_part, ext = os.path.splitext(name)

    # Limit the name part to prevent exceeding filesystem limits
    max_name_length = 200  # stay under 255 char filesystem limit
    if len(name_part) > max_name_length:
        name_part = name_part[:max_name_length]

    # Prepend UUID for uniqueness
    unique = uuid.uuid4().hex[:12]
    return f"{unique}_{name_part}{ext}"


async def validate_and_save(
    file: UploadFile,
    upload_dir: Path,
    label: str,
) -> str:
    """
    Validate file type & size, then save to disk.
    Returns the stored path (relative to project root) for DB storage.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Tipe file tidak diizinkan ({file.content_type}). "
                   f"Hanya JPG, PNG, dan PDF yang diterima.",
        )

    # Validate extension
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Ekstensi file tidak diizinkan ({ext}). "
                   f"Hanya .jpg, .jpeg, .png, .pdf yang diterima.",
        )

    # Read content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: Ukuran file melebihi batas maksimum "
                   f"{settings.MAX_UPLOAD_SIZE_MB}MB "
                   f"({len(content) / (1024*1024):.1f}MB).",
        )

    # Sanitize filename and save
    safe_name = sanitize_filename(file.filename or "unknown")
    file_path = upload_dir / safe_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Return relative path for DB storage
    return str(file_path)
