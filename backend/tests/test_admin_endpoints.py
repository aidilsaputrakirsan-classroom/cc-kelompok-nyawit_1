"""Test Admin endpoints untuk coverage - simplified."""
import pytest
from io import BytesIO

from sqlalchemy import select

from app.models.enums import PRStatus
from app.models.purchase_requisition import PurchaseRequisition
from tests.conftest import pr_multipart


async def _create_pr(client, headers, title, price=5000):
    """Helper: buat PR via multipart, kembalikan pr_id."""
    data, files = pr_multipart(
        title,
        "Testing",
        [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": price}],
    )
    resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=headers
    )
    return resp.json()["data"]["id"]


async def _approve_and_get_po_id(client, auth_headers, admin_auth_headers, pr_id):
    """Approve PR (jalur baru menerbitkan PO + set PO_ISSUED) lalu ambil po_id."""
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Approved"},
        headers=admin_auth_headers,
    )
    po_resp = await client.get(
        f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers
    )
    return po_resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_admin_list_requisitions(client, admin_auth_headers):
    """Test admin list semua PR → 200."""
    response = await client.get("/api/v1/requisitions/admin/", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data


@pytest.mark.asyncio
async def test_admin_review_approve(client, auth_headers, admin_auth_headers):
    """Test admin approve PR → 200, status menjadi PO_ISSUED."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk Approve")

    response = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Approved"},
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PO_ISSUED"


@pytest.mark.asyncio
async def test_admin_review_reject(client, auth_headers, admin_auth_headers):
    """Test admin reject PR → 200."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk Reject")

    response = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "REJECT", "approval_note": "Rejected"},
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_admin_issue_po(client, auth_headers, admin_auth_headers, db_session):
    """Test admin issue PO (endpoint legacy) → 201.

    Endpoint legacy /issue hanya untuk PR berstatus APPROVED, sementara jalur
    baru tidak pernah menghasilkan APPROVED. Maka set status PR ke APPROVED
    langsung lewat db sebelum memanggil /issue.
    """
    pr_id = await _create_pr(client, auth_headers, "PR untuk PO", price=1000)

    # Set status PR menjadi APPROVED langsung lewat db
    pr = (await db_session.execute(
        select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id)
    )).scalar_one()
    pr.status = PRStatus.APPROVED
    await db_session.commit()

    response = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)

    assert response.status_code == 201
    assert "po_number" in response.json()["data"]


@pytest.mark.asyncio
async def test_admin_list_purchase_orders(client, admin_auth_headers):
    """Test admin list POs → 200."""
    response = await client.get("/api/v1/purchase-orders/", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_admin_get_categories(client, admin_auth_headers):
    """Test admin get categories → 200."""
    response = await client.get("/api/v1/requisitions/admin/categories", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "categories" in data["data"]


@pytest.mark.asyncio
async def test_requester_submit_grn(client, auth_headers, admin_auth_headers):
    """Test requester submit GRN documents → 201."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk GRN", price=1000)

    # Approve (jalur baru menerbitkan PO & set PO_ISSUED) lalu ambil po_id
    po_id = await _approve_and_get_po_id(client, auth_headers, admin_auth_headers, pr_id)

    # Submit GRN
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")

    response = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={"commercial_invoice": invoice_file, "goods_photo": photo_file},
        headers=auth_headers
    )

    assert response.status_code == 201
    assert "id" in response.json()["data"]


@pytest.mark.asyncio
async def test_requester_get_grn(client, auth_headers, admin_auth_headers):
    """Test requester get GRN detail → 200."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk Get GRN", price=1000)

    po_id = await _approve_and_get_po_id(client, auth_headers, admin_auth_headers, pr_id)

    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")

    grn_resp = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={"commercial_invoice": invoice_file, "goods_photo": photo_file},
        headers=auth_headers
    )

    grn_id = grn_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/grn/{grn_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["id"] == grn_id


@pytest.mark.asyncio
async def test_admin_verify_grn(client, auth_headers, admin_auth_headers):
    """Test admin verify GRN → 200."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk Verify", price=1000)

    po_id = await _approve_and_get_po_id(client, auth_headers, admin_auth_headers, pr_id)

    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")

    grn_resp = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={"commercial_invoice": invoice_file, "goods_photo": photo_file},
        headers=auth_headers
    )

    grn_id = grn_resp.json()["data"]["id"]

    # Verify GRN
    response = await client.put(
        f"/api/v1/grn/admin/{grn_id}/verify",
        json={"status": "VERIFIED", "verification_note": "Verified"},
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_requester_get_my_po(client, auth_headers, admin_auth_headers):
    """Test requester get PO untuk PR miliknya → 200."""
    pr_id = await _create_pr(client, auth_headers, "PR untuk Get PO", price=1000)

    # Approve (jalur baru langsung menerbitkan PO)
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Approved"},
        headers=admin_auth_headers
    )

    response = await client.get(f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers)

    assert response.status_code == 200
    assert "po_number" in response.json()["data"]
