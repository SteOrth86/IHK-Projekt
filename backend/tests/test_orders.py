import pytest
from fastapi.testclient import TestClient

from kube_app_provisioner.main import app
from kube_app_provisioner.core.models import Order
from kube_app_provisioner.core.storage import orders_store

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

def test_cancel_pending_order_sets_status_canceled(client: TestClient):
    # Zuerst eine Order normal anlegen
    resp = client.post(
        "/orders",
        json={
            "product_type": "wordpress",
            "instance_slug": "wp-cancel-test",
            "domain": "cancel-test.example.com",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    order_id = body["id"]
    assert body["status"] == "pending"

    # Jetzt cancel aufrufen
    resp_cancel = client.post(f"/orders/{order_id}/cancel")
    assert resp_cancel.status_code == 200
    canceled_body = resp_cancel.json()
    assert canceled_body["status"] == "canceled"

    # Per GET prüfen, ob Zustand persistiert ist
    resp_get = client.get(f"/orders/{order_id}")
    assert resp_get.status_code == 200
    body_get = resp_get.json()
    assert body_get["status"] == "canceled"

def test_cancel_provisioned_order_returns_409(client: TestClient):
    # Direkt eine Order im Store anlegen und als 'provisioned' markieren
    order = Order(
        product_type="wordpress",
        instance_slug="wp-prov-test",
        domain="prov-test.example.com",
    )
    orders_store.add(order)

    order.status = "provisioned"
    orders_store.update(order)

    resp = client.post(f"/orders/{order.id}/cancel")
    assert resp.status_code == 409

    body = resp.json()
    assert body["detail"] == "Order already provisioned"
