import pytest
from fastapi.testclient import TestClient

from kube_app_provisioner.main import app
from kube_app_provisioner.core.models import Order
from kube_app_provisioner.core.storage import orders_store, Instance
from kube_app_provisioner.services.apps import wordpress as wp_service
from kube_app_provisioner.services.apps import odoo as odoo_service
from kube_app_provisioner.routers import stripe_webhooks

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_stripe_webhook_accepts_request_when_secret_missing(client: TestClient):
    # In der Testumgebung ist STRIPE_WEBHOOK_SECRET leer,
    # daher sollte der Endpoint die Signaturprüfung überspringen.
    resp = client.post(
        "/webhooks/stripe",
        json={"test": "value"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["verification"] == "skipped"

def test_checkout_session_completed_provisions_wordpress_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):

    order = Order(
        product_type="wordpress",
        instance_slug="wp-stripe-test",
        domain="stripe-test.example.com",
    )
    orders_store.add(order)

    calls: dict[str, bool] = {}

    def fake_create_wp(slug: str, domain: str, store):
        calls["called"] = True
        assert slug == order.instance_slug
        assert domain == order.domain
        return Instance(
            id="instance-123",
            type="wordpress",
            namespace=f"wp-{slug}",
            domain=domain,
            created_at="now",
            updated_at="now",
            status="running",
        )

    # Provisionierung mocken, damit keine echten Skripte laufen
    monkeypatch.setattr(stripe_webhooks, "create_wordpress_instance", fake_create_wp, raising=False)

    payload = {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "client_reference_id": order.id,
                "payment_intent": "pi_123",
            }
        },
    }

    resp = client.post("/webhooks/stripe", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "checkout.session.completed"

    updated = orders_store.get(order.id)
    assert updated is not None
    assert updated.status == "provisioned"
    assert updated.instance_id == "instance-123"
    assert updated.stripe_session_id == "cs_test_123"
    assert updated.stripe_payment_intent == "pi_123"
    assert calls.get("called") is True


def test_checkout_session_completed_provisions_odoo_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    order = Order(
        product_type="odoo",
        instance_slug="odoo-stripe-test",
        domain="odoo-test.example.com",
    )
    orders_store.add(order)

    calls: dict[str, bool] = {}

    def fake_create_odoo(slug: str, domain: str, store):
        calls["called"] = True
        assert slug == order.instance_slug
        assert domain == order.domain
        return Instance(
            id="instance-456",
            type="odoo",
            namespace=f"odoo-{slug}",
            domain=domain,
            created_at="now",
            updated_at="now",
            status="running",
        )

    monkeypatch.setattr(stripe_webhooks, "create_odoo_instance", fake_create_odoo, raising=False)

    payload = {
        "id": "evt_456",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_456",
                "client_reference_id": order.id,
                "payment_intent": "pi_456",
            }
        },
    }

    resp = client.post("/webhooks/stripe", json=payload)
    assert resp.status_code == 200

    updated = orders_store.get(order.id)
    assert updated is not None
    assert updated.status == "provisioned"
    assert updated.instance_id == "instance-456"
    assert updated.stripe_session_id == "cs_test_456"
    assert updated.stripe_payment_intent == "pi_456"
    assert calls.get("called") is True
