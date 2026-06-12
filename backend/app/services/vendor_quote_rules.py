"""
Pure business rules for vendor-quote procurement.

These functions contain NO I/O and operate on plain values / duck-typed
quote objects (anything exposing ``id``, ``quoted_price``, ``is_recommended``),
so they can be exhaustively tested with property-based testing.

Validates requirements: 1.6, 3.2-3.6, 4.1-4.3, 6.3, 7.1-7.3, 10.1-10.2, 11.2-11.3
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

MIN_VENDOR_ABOVE_THRESHOLD = 3
MIN_VENDOR_AT_OR_BELOW_THRESHOLD = 1


class VendorQuoteError(Exception):
    """Domain error for vendor-quote rule violations (mapped to HTTP 400)."""


class QuoteLike(Protocol):
    id: int
    quoted_price: Decimal
    is_recommended: bool


def required_min_vendors(total_amount: Decimal, threshold: Decimal) -> int:
    """Jumlah minimal vendor berdasarkan ambang nilai.

    total > threshold → MIN_VENDOR_ABOVE_THRESHOLD (3);
    selain itu (termasuk total == 0) → MIN_VENDOR_AT_OR_BELOW_THRESHOLD (1).

    Req 3.2/3.3/3.6.
    """
    if total_amount > threshold:
        return MIN_VENDOR_ABOVE_THRESHOLD
    return MIN_VENDOR_AT_OR_BELOW_THRESHOLD


def validate_vendor_count(total_amount: Decimal, threshold: Decimal, count: int) -> None:
    """Pastikan jumlah vendor memenuhi minimal sesuai ambang.

    Raise VendorQuoteError jika count kurang dari minimal. Req 1.6, 3.2, 3.3.
    """
    minimum = required_min_vendors(total_amount, threshold)
    if count < minimum:
        raise VendorQuoteError(
            f"Minimal {minimum} penawaran vendor diperlukan untuk nilai PR ini."
        )


def validate_single_recommended(flags: list[bool]) -> None:
    """Pastikan tepat satu vendor ditandai sebagai rekomendasi.

    Req 4.1/4.2/4.3.
    """
    recommended_count = sum(1 for f in flags if f)
    if recommended_count == 0:
        raise VendorQuoteError(
            "Tepat satu vendor harus ditandai sebagai rekomendasi."
        )
    if recommended_count > 1:
        raise VendorQuoteError(
            "Hanya satu vendor yang boleh ditandai sebagai rekomendasi."
        )


def resolve_selected_vendor(quotes, selected_id):
    """Tentukan vendor terpilih.

    - quotes kosong (Legacy_PR) → None.
    - selected_id None → kembalikan Recommended_Vendor (is_recommended True).
    - selected_id ada di quotes → kembalikan quote dengan id itu.
    - selected_id tidak ada di quotes → raise VendorQuoteError (Req 7.3).

    Req 7.1/7.2/7.3 + 11.2.
    """
    if not quotes:
        return None

    if selected_id is None:
        for q in quotes:
            if q.is_recommended:
                return q
        # Tidak ada rekomendasi (seharusnya dicegah saat create); fallback aman.
        return None

    for q in quotes:
        if q.id == selected_id:
            return q

    raise VendorQuoteError("Vendor terpilih tidak valid untuk PR ini.")


def compute_allocated_budget(selected_quote, pr_total_amount: Decimal) -> Decimal:
    """Hitung allocated_budget PO.

    - selected_quote ada → quoted_price vendor terpilih (harga riil).
    - selected_quote None (Legacy_PR) → total_amount PR (bisa 0).

    Req 6.3/10.1/10.2 + 11.2/11.3.
    """
    if selected_quote is not None:
        return Decimal(selected_quote.quoted_price)
    return Decimal(pr_total_amount)
