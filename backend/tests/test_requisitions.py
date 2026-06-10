"""Test Purchase Requisition endpoints untuk SiCure."""
import asyncio
import pytest


@pytest.mark.asyncio
async def test_create_requisition(client, auth_headers):
    """Test membuat PR baru → 201."""
    pr_data = {
        "title": "Pengadaan Laptop untuk Tim Engineering",
        "justification": "Diperlukan untuk development project cloud computing",
        "items": [
            {
                "item_name": "Laptop Gaming",
                "quantity": 2,
                "unit_of_measure": "unit",
                "estimated_unit_price": 15000000
            },
            {
                "item_name": "Mouse Wireless",
                "quantity": 2,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 250000
            }
        ]
    }
    
    response = await client.post("/api/v1/requisitions/", json=pr_data, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Pengadaan Laptop untuk Tim Engineering"
    assert data["data"]["status"] == "SUBMITTED"
    assert "pr_number" in data["data"]
    assert data["data"]["pr_number"].startswith("PR-")
    assert len(data["data"]["line_items"]) == 2
    # Total harus dihitung otomatis: (2*15000000) + (2*250000) = 30500000
    assert float(data["data"]["total_amount"]) == 30500000.0


@pytest.mark.asyncio
async def test_create_requisition_unauthorized(client):
    """Test membuat PR tanpa login → 401."""
    pr_data = {
        "title": "Test PR",
        "justification": "Test",
        "items": [{
            "item_name": "Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }
    
    response = await client.post("/api/v1/requisitions/", json=pr_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_my_requisitions(client, auth_headers):
    """Test mengambil daftar PR milik sendiri → 200."""
    # Buat 2 PRs
    for i in range(2):
        await client.post("/api/v1/requisitions/", json={
            "title": f"Test PR {i+1}",
            "justification": "Justification",
            "items": [{
                "item_name": "Item",
                "quantity": 1,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 1000
            }]
        }, headers=auth_headers)
    
    response = await client.get("/api/v1/requisitions/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 2
    assert "pagination" in data


@pytest.mark.asyncio
async def test_get_requisition_detail(client, auth_headers):
    """Test mengambil detail PR."""
    # Buat PR dulu
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "Detail Test PR",
        "justification": "For detail test",
        "items": [{
            "item_name": "Test Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 5000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Ambil detail
    response = await client.get(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == pr_id
    assert data["data"]["title"] == "Detail Test PR"
    assert len(data["data"]["line_items"]) == 1


@pytest.mark.asyncio
async def test_get_requisition_not_found(client, auth_headers):
    """Test mengambil PR yang tidak ada → 404."""
    response = await client.get("/api/v1/requisitions/9999", headers=auth_headers)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_requisition(client, auth_headers):
    """Test update PR yang masih SUBMITTED."""
    # Buat PR
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "Original Title",
        "justification": "Original justification",
        "items": [{
            "item_name": "Item A",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 1000
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Update
    update_data = {
        "title": "Updated Title",
        "justification": "Updated justification",
        "items": [
            {
                "item_name": "Item A",
                "quantity": 2,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 1000
            },
            {
                "item_name": "Item B",
                "quantity": 1,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 2000
            }
        ]
    }
    
    response = await client.put(f"/api/v1/requisitions/{pr_id}", json=update_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated Title"
    assert len(data["data"]["line_items"]) == 2
    # New total: (2*1000) + (1*2000) = 4000
    assert float(data["data"]["total_amount"]) == 4000.0


@pytest.mark.asyncio
async def test_delete_requisition(client, auth_headers):
    """Test hapus PR yang masih SUBMITTED."""
    # Buat PR
    create_resp = await client.post("/api/v1/requisitions/", json={
        "title": "Temporary PR",
        "justification": "Will be deleted",
        "items": [{
            "item_name": "Temp Item",
            "quantity": 1,
            "unit_of_measure": "pcs",
            "estimated_unit_price": 100
        }]
    }, headers=auth_headers)
    
    pr_id = create_resp.json()["data"]["id"]
    
    # Hapus
    response = await client.delete(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verifikasi sudah tidak ada
    get_resp = await client.get(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_requisitions_by_status(client, auth_headers):
    """Test filter PR berdasarkan status."""
    import time
    
    # Buat beberapa PR dengan title unik untuk menghindari collision
    for i in range(3):
        await client.post("/api/v1/requisitions/", json={
            "title": f"Filter Test PR {i} - {int(time.time() * 1000)}",
            "justification": "Test",
            "items": [{
                "item_name": "Item",
                "quantity": 1,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 1000
            }]
        }, headers=auth_headers)
        # Small delay to ensure unique timestamps
        await asyncio.sleep(0.01)
    
    # Filter by status SUBMITTED
    response = await client.get("/api/v1/requisitions/?status=SUBMITTED", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert all(pr["status"] == "SUBMITTED" for pr in data["data"])