import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_order_returns_201_and_pending_status(client: TestClient):
    resp = client.post(
        "/orders",
        json={
            "product_type": "wordpress",
            "instance_slug": "wp-kunde1",
            "domain": "kunde1.example.com",
        },
    )

    assert resp.status_code == 201

    body = resp.json()
    assert body["product_type"] == "wordpress"
    assert body["instance_slug"] == "wp-kunde1"
    assert body["domain"] == "kunde1.example.com"
    assert body["status"] == "pending"
    assert "id" in body
    assert body["id"]

    # direkt danach per GET prüfen, ob sie abrufbar ist
    order_id = body["id"]
    resp_get = client.get(f"/orders/{order_id}")
    assert resp_get.status_code == 200
    body_get = resp_get.json()
    assert body_get["id"] == order_id
    assert body_get["status"] == "pending"


def test_get_unknown_order_returns_404(client: TestClient):
    resp = client.get("/orders/does-not-exist")
    assert resp.status_code == 404

    body = resp.json()
    assert body["detail"] == "Order not found"
