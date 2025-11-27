import pytest
from fastapi.testclient import TestClient

from kube_app_provisioner.main import app
from kube_app_provisioner.core.models import Order
from kube_app_provisioner.core.storage import orders_store, Instance
from kube_app_provisioner.services.apps import orders as orders_service

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
    # Ausgangszustand: eine pending-Order
    order = Order(
        product_type="wordpress",
        instance_slug="wp-stripe-test",
        domain="stripe-test.example.com",
    )
    orders_store.add(order)

    calls: dict[str, bool] = {}

    def fake_provision_wordpress_for_order(order_arg: Order) -> Instance:
        calls["called"] = True
        assert order_arg.id == order.id
        return Instance(
            id="instance-123",
            type="wordpress",
            namespace="wp-stripe-test",
            domain=order_arg.domain,
            created_at="now",
            updated_at="now",
            status="creating",
        )

    # Provisionierungsfunktion mocken, damit keine echte Provisionierung läuft
    monkeypatch.setattr(
        orders_service,
        "provision_wordpress_for_order",
        fake_provision_wordpress_for_order,
    )

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
