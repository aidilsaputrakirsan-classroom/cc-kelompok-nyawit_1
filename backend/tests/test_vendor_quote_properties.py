"""
Property-based tests for vendor-quote-procurement pure logic.

Feature: vendor-quote-procurement
Each property is verified with one Hypothesis test (min 100 examples).
Pure logic only (no I/O), so these run fast and deterministically.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.vendor_quote import VendorQuoteIn
from app.services.vendor_quote_rules import (
    MIN_VENDOR_ABOVE_THRESHOLD,
    MIN_VENDOR_AT_OR_BELOW_THRESHOLD,
    VendorQuoteError,
    compute_allocated_budget,
    required_min_vendors,
    resolve_selected_vendor,
    validate_single_recommended,
    validate_vendor_count,
)

_money = st.decimals(min_value=Decimal("0"), max_value=Decimal("100000000"), places=2)
_threshold = st.decimals(min_value=Decimal("1"), max_value=Decimal("100000000"), places=2)


# Feature: vendor-quote-procurement, Property 1: Aturan jumlah minimal vendor berbasis ambang
@settings(max_examples=100)
@given(total=_money, threshold=_threshold, count=st.integers(min_value=0, max_value=10))
def test_property_1_min_vendor_threshold(total, threshold, count):
    expected_min = (
        MIN_VENDOR_ABOVE_THRESHOLD if total > threshold else MIN_VENDOR_AT_OR_BELOW_THRESHOLD
    )
    assert required_min_vendors(total, threshold) == expected_min

    if count >= expected_min:
        # tidak boleh raise
        validate_vendor_count(total, threshold, count)
    else:
        with pytest.raises(VendorQuoteError):
            validate_vendor_count(total, threshold, count)


# Feature: vendor-quote-procurement, Property 2: Tepat satu vendor rekomendasi
@settings(max_examples=100)
@given(flags=st.lists(st.booleans(), min_size=0, max_size=8))
def test_property_2_single_recommended(flags):
    if sum(1 for f in flags if f) == 1:
        validate_single_recommended(flags)  # lolos
    else:
        with pytest.raises(VendorQuoteError):
            validate_single_recommended(flags)


def _make_quotes(prices, recommended_index):
    """Build quote-like objects with unique ids and exactly one recommended."""
    return [
        SimpleNamespace(
            id=i + 1,
            quoted_price=Decimal(p),
            is_recommended=(i == recommended_index),
        )
        for i, p in enumerate(prices)
    ]


# Feature: vendor-quote-procurement, Property 3: Resolusi vendor terpilih
@settings(max_examples=100)
@given(
    prices=st.lists(st.integers(min_value=1, max_value=10_000_000), min_size=1, max_size=6),
    rec_seed=st.integers(min_value=0, max_value=5),
    pick=st.integers(min_value=-3, max_value=10),
)
def test_property_3_resolve_selected_vendor(prices, rec_seed, pick):
    rec_idx = rec_seed % len(prices)
    quotes = _make_quotes(prices, rec_idx)
    valid_ids = {q.id for q in quotes}

    # selected_id None → recommended vendor
    assert resolve_selected_vendor(quotes, None).id == quotes[rec_idx].id

    if pick in valid_ids:
        assert resolve_selected_vendor(quotes, pick).id == pick
    else:
        with pytest.raises(VendorQuoteError):
            resolve_selected_vendor(quotes, pick)


# Feature: vendor-quote-procurement, Property 4: Alokasi budget PO sama dengan harga vendor terpilih
@settings(max_examples=100)
@given(
    price=st.integers(min_value=1, max_value=10_000_000),
    total=_money,
    has_selected=st.booleans(),
)
def test_property_4_allocated_budget(price, total, has_selected):
    if has_selected:
        selected = SimpleNamespace(id=1, quoted_price=Decimal(price), is_recommended=True)
        assert compute_allocated_budget(selected, total) == Decimal(price)
    else:
        # Legacy: tidak ada vendor terpilih → pakai total PR
        assert compute_allocated_budget(None, total) == Decimal(total)


# Feature: vendor-quote-procurement, Property 8: Harga vendor wajib positif
@settings(max_examples=100)
@given(
    price=st.decimals(min_value=Decimal("-1000"), max_value=Decimal("10000000"), places=2),
)
def test_property_8_quoted_price_positive(price):
    payload = {
        "vendor_name": "PT Uji",
        "vendor_contact": "08123456789",
        "quoted_price": price,
        "survey_date": "2026-01-01",
        "is_recommended": True,
    }
    if price > 0:
        model = VendorQuoteIn.model_validate(payload)
        assert model.quoted_price == price
    else:
        with pytest.raises(Exception):
            VendorQuoteIn.model_validate(payload)
