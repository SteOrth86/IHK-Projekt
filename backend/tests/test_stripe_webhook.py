import pytest
from fastapi.testclient import TestClient
from main import app


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
