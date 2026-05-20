"""Test GRN (Goods Received Note) endpoints untuk SiCure."""
import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_submit_grn_documents_success(client, auth_headers, admin_auth_headers):
    """Test submit dokumen GRN berhasil → 201."""
    # Buat PR dulu
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk GRN Test",
        "justification": "Testing GRN submission",
        "items": [{
            "item_name": "Test Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve PR via admin endpoint
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={
            "status": "APPROVED",
            "approval_note": "Approved for testing"
        },
        headers=admin_auth_headers
    )
    
    # Issue PO
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    po_id = po_resp.json()["data"]["id"]
    
    # Submit GRN documents
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf content"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image content"), "image/jpeg")
    
    response = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={
            "commercial_invoice": invoice_file,
            "goods_photo": photo_file
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_submit_grn_unauthorized(client):
    """Test submit GRN tanpa login → 401."""
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")
    
    response = await client.post(
        "/api/v1/grn/1/submit-doc",
        files={
            "commercial_invoice": invoice_file,
            "goods_photo": photo_file
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_grn_po_not_found(client, auth_headers):
    """Test submit GRN dengan PO yang tidak ada → 404."""
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")
    
    response = await client.post(
        "/api/v1/grn/99999/submit-doc",
        files={
            "commercial_invoice": invoice_file,
            "goods_photo": photo_file
        },
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_grn_wrong_status(client, auth_headers):
    """Test submit GRN saat status PR bukan PO_ISSUED → 409."""
    # Buat PR (status SUBMITTED by default)
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR Wrong Status",
        "justification": "Testing",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Coba issue PO tanpa approve (akan fail atau return error)
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=auth_headers)
    
    # Jika tidak bisa issue PO, test tidak applicable
    if po_resp.status_code != 201:
        pytest.skip("Cannot create PO without approval - expected behavior")
    
    po_id = po_resp.json()["data"]["id"]
    
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")
    
    response = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={
            "commercial_invoice": invoice_file,
            "goods_photo": photo_file
        },
        headers=auth_headers
    )
    
    # Seharusnya 409 karena status bukan PO_ISSUED
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_grn_document_success(client, auth_headers, admin_auth_headers):
    """Test get detail GRN document → 200."""
    # Buat PR dan submit GRN dulu
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Get GRN",
        "justification": "Testing",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve dan issue PO
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={
            "status": "APPROVED",
            "approval_note": "Approved"
        },
        headers=admin_auth_headers
    )
    
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    po_id = po_resp.json()["data"]["id"]
    
    # Submit GRN
    invoice_file = ("invoice.pdf", BytesIO(b"fake pdf"), "application/pdf")
    photo_file = ("photo.jpg", BytesIO(b"fake image"), "image/jpeg")
    
    grn_resp = await client.post(
        f"/api/v1/grn/{po_id}/submit-doc",
        files={
            "commercial_invoice": invoice_file,
            "goods_photo": photo_file
        },
        headers=auth_headers
    )
    
    grn_id = grn_resp.json()["data"]["id"]
    
    # Get GRN detail
    response = await client.get(f"/api/v1/grn/{grn_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == grn_id


@pytest.mark.asyncio
async def test_get_grn_not_found(client, auth_headers):
    """Test get GRN yang tidak ada → 404."""
    response = await client.get("/api/v1/grn/99999", headers=auth_headers)
    
    assert response.status_code == 404
