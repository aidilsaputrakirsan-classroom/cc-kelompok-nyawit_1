"""
Property-based tests for shared upload utilities.

Feature: vendor-quote-procurement
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.utils.uploads import sanitize_filename


# Feature: vendor-quote-procurement, Property 7: Sanitasi nama berkas
# Validates: Requirements 5.4
@settings(max_examples=100)
@given(
    name=st.text(min_size=0, max_size=80),
    ext=st.sampled_from([".jpg", ".jpeg", ".png", ".pdf"]),
)
def test_property_7_sanitize_filename(name, ext):
    raw = f"{name}{ext}"
    out1 = sanitize_filename(raw)
    out2 = sanitize_filename(raw)

    # Tidak mengandung pemisah direktori maupun path traversal
    assert "/" not in out1
    assert "\\" not in out1
    assert ".." not in out1

    # Ekstensi asli dipertahankan
    assert out1.endswith(ext)

    # Dua pemanggilan menghasilkan nama berbeda (prefix UUID unik)
    assert out1 != out2


# Feature: vendor-quote-procurement, Property 7 (lanjutan): path traversal eksplisit
@settings(max_examples=100)
@given(
    depth=st.integers(min_value=1, max_value=6),
    base=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=20,
    ),
)
def test_property_7_path_traversal(depth, base):
    raw = "../" * depth + base + ".png"
    out = sanitize_filename(raw)
    assert "/" not in out
    assert ".." not in out
    assert out.endswith(".png")
