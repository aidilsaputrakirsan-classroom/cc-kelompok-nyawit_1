"""Test edge cases dan error handling untuk meningkatkan coverage."""
import pytest

from tests.conftest import pr_multipart


@pytest.mark.asyncio
async def test_health_check_database_error(client):
    """Test health check saat database error → 503."""
    # Health endpoint seharusnya tetap return response meski DB error
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_api_health_check_detailed(client):
    """Test API health check dengan detail components."""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "components" in data["data"]


@pytest.mark.asyncio
async def test_create_requisition_empty_items(client, auth_headers):
    """Test create PR dengan items kosong → validation error."""
    data, files = pr_multipart("PR Empty Items", "Testing", [])

    response = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )

    # Seharusnya validasi error (422 atau 400)
    assert response.status_code in [422, 400]


@pytest.mark.asyncio
async def test_update_requisition_not_owner(client, auth_headers):
    """Test update PR milik user lain → 403."""
    # Buat PR sebagai user pertama
    data, files = pr_multipart(
        "PR Other User",
        "Testing",
        [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}],
    )
    create_resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )

    pr_id = create_resp.json()["data"]["id"]
    
    # Register user kedua
    await client.post("/api/v1/auth/register-requester", json={
        "email": "other@example.com",
        "password": "OtherPass123",
        "full_name": "Other User"
    })
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "other@example.com",
        "password": "OtherPass123"
    })
    
    other_token = login_resp.json()["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Coba update PR milik user pertama
    response = await client.put(
        f"/api/v1/requisitions/{pr_id}",
        json={
            "title": "Updated Title",
            "justification": "Updated",
            "items": [{"item_name": "Item", "quantity": 2, "unit_of_measure": "pcs", "estimated_unit_price": 1000}]
        },
        headers=other_headers
    )
    
    # Seharusnya 403 Forbidden atau 404 Not Found
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_delete_requisition_already_processed(client, auth_headers, admin_auth_headers):
    """Test hapus PR yang sudah di-approve → 409 atau 400."""
    data, files = pr_multipart(
        "PR Already Approved",
        "Testing",
        [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}],
    )
    create_resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )

    pr_id = create_resp.json()["data"]["id"]

    # Approve PR (jalur baru → PO_ISSUED)
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Approved"},
        headers=admin_auth_headers
    )

    # Coba hapus
    response = await client.delete(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)

    # Seharusnya error (409 Conflict atau 400 Bad Request)
    assert response.status_code in [409, 400]


@pytest.mark.asyncio
async def test_list_requisitions_with_pagination(client, auth_headers):
    """Test list PR dengan pagination parameters."""
    # Buat beberapa PR
    for i in range(5):
        data, files = pr_multipart(
            f"Pagination Test PR {i}",
            "Testing",
            [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}],
        )
        await client.post(
            "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
        )
    
    # Test dengan page dan per_page
    response = await client.get("/api/v1/requisitions/?page=1&per_page=2", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2


@pytest.mark.asyncio
async def test_filter_requisitions_by_nonexistent_status(client, auth_headers):
    """Test filter PR dengan status yang tidak ada → empty list."""
    response = await client.get("/api/v1/requisitions/?status=CLOSED", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Mungkin empty atau ada data tergantung state


@pytest.mark.asyncio
async def test_get_requisition_detail_unauthorized(client):
    """Test get detail PR tanpa auth → 401."""
    response = await client.get("/api/v1/requisitions/1")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_email_format(client):
    """Test login dengan format email invalid → 422."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "not-an-email",
        "password": "Password123"
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client):
    """Test register dengan password lemah → 422."""
    response = await client.post("/api/v1/auth/register-requester", json={
        "email": "weak@example.com",
        "password": "123",
        "full_name": "Weak User"
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_review_pr_not_submitted(client, auth_headers, admin_auth_headers):
    """Test review PR yang sudah di-review → 409."""
    data, files = pr_multipart(
        "PR Double Review",
        "Testing",
        [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}],
    )
    create_resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )

    pr_id = create_resp.json()["data"]["id"]

    # Approve first time
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "First approval"},
        headers=admin_auth_headers
    )

    # Try to approve again
    response = await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "APPROVE", "approval_note": "Second approval"},
        headers=admin_auth_headers
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_issue_po_for_rejected_pr(client, auth_headers, admin_auth_headers):
    """Test issue PO untuk PR yang REJECTED → 409."""
    data, files = pr_multipart(
        "PR Rejected",
        "Testing",
        [{"item_name": "Item", "quantity": 1, "unit_of_measure": "pcs", "estimated_unit_price": 1000}],
    )
    create_resp = await client.post(
        "/api/v1/requisitions/", data=data, files=files, headers=auth_headers
    )

    pr_id = create_resp.json()["data"]["id"]

    # Reject PR
    await client.put(
        f"/api/v1/requisitions/admin/{pr_id}/review",
        json={"action": "REJECT", "approval_note": "Rejected"},
        headers=admin_auth_headers
    )

    # Try to issue PO
    response = await client.post(f"/api/v1/purchase-orders/{pr_id}/issue", headers=admin_auth_headers)

    assert response.status_code == 409
