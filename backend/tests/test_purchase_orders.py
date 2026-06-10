"""Test Purchase Order endpoints untuk SiCure."""
import pytest


@pytest.mark.asyncio
async def test_issue_purchase_order_success(client, admin_auth_headers):
    """Test issue PO dari PR yang APPROVED → 201."""
    # Buat PR (gunakan admin headers untuk consistency)
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Issue PO",
        "justification": "Testing PO issuance",
        "items": [{
            "item_name": "Test Item",
            "quantity": 2,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 5000
        }]
    }, headers=admin_auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve PR
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={
            "status": "APPROVED",
            "approval_note": "Approved for testing"
        },
        headers=admin_auth_headers
    )
    
    # Issue PO
    response = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "po_number" in data["data"]
    assert data["data"]["po_number"].startswith("PO-")
    assert float(data["data"]["allocated_budget"]) == 10000.0


@pytest.mark.asyncio
async def test_issue_po_pr_not_found(client, admin_auth_headers):
    """Test issue PO dengan PR yang tidak ada → 404."""
    response = await client.post("/api/v1/purchase-orders/99999/issue", headers=admin_auth_headers)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_issue_po_wrong_status(client, admin_auth_headers):
    """Test issue PO saat status PR bukan APPROVED → 409."""
    # Buat PR (status SUBMITTED by default)
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR Wrong Status for PO",
        "justification": "Testing",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=admin_auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    response = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_issue_po_duplicate(client, admin_auth_headers):
    """Test issue PO dua kali untuk PR yang sama → 409."""
    # Buat PR dan approve
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR Duplicate PO",
        "justification": "Testing duplicate",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=admin_auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve PR
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={
            "status": "APPROVED",
            "approval_note": "Approved"
        },
        headers=admin_auth_headers
    )
    
    # Issue PO pertama
    await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    # Issue PO kedua (should fail)
    response = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_my_po_for_pr_success(client, auth_headers, admin_auth_headers):
    """Test requester melihat PO untuk PR miliknya → 200."""
    # Buat PR sebagai requester
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR untuk Get My PO",
        "justification": "Testing",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Approve dan issue PO sebagai admin
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={
            "status": "APPROVED",
            "approval_note": "Approved"
        },
        headers=admin_auth_headers
    )
    
    await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)
    
    # Get PO sebagai requester
    response = await client.get(f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "po_number" in data["data"]


@pytest.mark.asyncio
async def test_get_my_po_pr_not_found(client, auth_headers):
    """Test get PO untuk PR yang tidak ada/bukan milik user → 404."""
    response = await client.get("/api/v1/purchase-orders/99999/my-po", headers=auth_headers)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_po_not_issued(client, auth_headers):
    """Test get PO untuk PR yang belum di-issue → 404."""
    # Buat PR tapi tidak issue PO
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "PR Tanpa PO",
        "justification": "Testing",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    response = await client.get(f"/api/v1/purchase-orders/{pr_id}/my-po", headers=auth_headers)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_purchase_orders_empty(client, admin_auth_headers):
    """Test list PO (empty) → 200."""
    response = await client.get("/api/v1/purchase-orders/", headers=admin_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data
