"""
Integration test — alur procurement end-to-end lintas modul.

Berbeda dari unit test (yang menguji fungsi/aturan bisnis secara terisolasi),
test ini memverifikasi beberapa modul bekerja sama melalui HTTP API + database:

    auth → requisitions → admin review → purchase order → GRN → verify → close

Sekaligus membuktikan:
  - proteksi endpoint (akses tanpa token ditolak 401),
  - fitur search/filter pada list PR,
  - observability: setiap response membawa header correlation ID.
"""
from io import BytesIO

import pytest

from tests.conftest import pr_multipart


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_procurement_lifecycle(client, auth_headers, admin_auth_headers):
    """SUBMITTED → PO_ISSUED → DOC_SUBMITTED → VERIFIED → CLOSED."""

    # 1) Requester membuat PR + penawaran vendor (multipart).
    data, files = pr_multipart(
        "Pengadaan Laptop Kantor",
        "Kebutuhan operasional tim",
        [{
            "item_name": "Laptop Dinas",
            "quantity": 2,
            "unit_of_measure": "unit",
            "estimated_unit_price": 1000,
        }],
    )
    create_resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["success"] is True
    pr_id = body["data"]["id"]
    assert body["data"]["status"] == "SUBMITTED"

    # 2) PR muncul di list milik requester, dan search/filter bekerja.
    search_resp = await client.get(
        "/api/v1/requisitions/?category=Laptop", headers=auth_headers
    )
    assert search_resp.status_code == 200
    found = [pr["id"] for pr in search_resp.json()["data"]]
    assert pr_id in found

    # Filter dengan kata kunci yang tidak cocok → PR tidak muncul.
    miss_resp = await client.get(
        "/api/v1/requisitions/?category=TidakAda", headers=auth_headers
    )
    assert pr_id not in [pr["id"] for pr in miss_resp.json()["data"]]

    # 3) Proteksi endpoint: tanpa token harus ditolak.
    no_auth = await client.get("/api/v1/requisitions/")
    assert no_auth.status_code in (401, 403)

    # 4) Admin approve → PO otomatis diterbitkan, status PO_ISSUED.
    review_resp = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Disetujui"},
        headers=admin_auth_headers,
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["data"]["status"] == "PO_ISSUED"

    # 5) Requester mengambil PO untuk PR-nya.
    po_resp = await client.get(
        f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers
    )
    assert po_resp.status_code == 200
    po_id = po_resp.json()["data"]["id"]

    # 6) Requester submit dokumen GRN → DOC_SUBMITTED.
    grn_resp = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={
            "commercial_invoice": ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf"),
            "goods_photo": ("photo.jpg", BytesIO(b"fake image"), "image/jpeg"),
        },
        headers=auth_headers,
    )
    assert grn_resp.status_code == 201
    grn_id = grn_resp.json()["data"]["id"]

    # 7) Admin verifikasi GRN → VERIFIED.
    verify_resp = await client.put(
        f"/api/v1/grn/admin/{grn_id}/verify",
        json={"status": "VERIFIED", "verification_note": "Dokumen sesuai"},
        headers=admin_auth_headers,
    )
    assert verify_resp.status_code == 200

    # 8) Admin menutup procurement → CLOSED.
    close_resp = await client.put(
        f"/api/v1/grn/admin/{grn_id}/verify",
        json={"status": "CLOSED", "verification_note": "Procurement selesai"},
        headers=admin_auth_headers,
    )
    assert close_resp.status_code == 200

    # Status akhir PR harus CLOSED.
    detail_resp = await client.get(
        f"/api/v1/requisitions/{pr_id}", headers=auth_headers
    )
    assert detail_resp.json()["data"]["status"] == "CLOSED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_response_carries_correlation_id(client):
    """Observability: setiap response membawa header X-Correlation-ID."""
    # ID yang dikirim klien harus dipantulkan kembali (tracing lintas service).
    resp = await client.get("/health", headers={"X-Correlation-ID": "trace-int-1"})
    assert resp.headers.get("X-Correlation-ID") == "trace-int-1"

    # Tanpa header, server membuat correlation ID baru.
    resp2 = await client.get("/health")
    assert resp2.headers.get("X-Correlation-ID")
