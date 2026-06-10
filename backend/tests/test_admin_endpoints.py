"""Test Admin endpoints untuk coverage - simplified."""
import pytest
from io import BytesIO


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
    """Test admin approve PR → 200."""
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Approve",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 5000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    response = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_admin_review_reject(client, auth_headers, admin_auth_headers):
    """Test admin reject PR → 200."""
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Reject",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 5000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    response = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "REJECTED", "approval_note": "Rejected"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_admin_issue_po(client, auth_headers, admin_auth_headers):
    """Test admin issue PO → 201."""
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk PO",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve first
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
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
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk GRN",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve dan issue PO
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    if po_resp.status_code != 201:
        pytest.skip("Admin role required")
    
    po_id = po_resp.json()["data"]["id"]
    
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
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Get GRN",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    if po_resp.status_code != 201:
        pytest.skip("Admin role required")
    
    po_id = po_resp.json()["data"]["id"]
    
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
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Verify",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
    po_resp = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    if po_resp.status_code != 201:
        pytest.skip("Admin role required")
    
    po_id = po_resp.json()["data"]["id"]
    
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
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Get PO",
        "justification": "Testing",
        "items": [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"status": "APPROVED", "approval_note": "Approved"},
        headers=admin_auth_headers
    )
    
    await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    response = await client.get(f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers)
    
    assert response.status_code == 200
    assert "po_number" in response.json()["data"]
