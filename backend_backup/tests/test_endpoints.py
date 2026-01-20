# backend/tests/test_endpoints.py

import sys
from pathlib import Path

# Projekt-Root (backend-Ordner) auf sys.path legen
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

import config
import storage
from storage import InstanceStore
from routers import wordpress as wp_router
from routers import odoo as odoo_router
from services import wordpress as wp_service
from services import odoo as odoo_service
from services import status as status_service
from services import email as email_service

import main
import httpx

@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """
    Stellt für jeden Test eine isolierte Testumgebung bereit:

    - eigene instances.json im tmp_path
    - eigener InstanceStore
    - globaler store + Router-Store auf Test-Store umgebogen
    - run_script in den Services gemockt (keine echten Skripte)
    - refresh_instance_statuses gemockt (kein kubectl)
    - API_KEY auf Test-Wert gesetzt
    """
    # Eigene Instanz-Datei für diesen Testlauf
    instances_file = tmp_path / "instances.json"
    monkeypatch.setattr(config, "INSTANCES_FILE", instances_file, raising=False)

    # Test-Store anlegen und globalen store patchen
    test_store = InstanceStore(instances_file)
    monkeypatch.setattr(storage, "store", test_store, raising=False)
    monkeypatch.setattr(wp_router, "store", test_store, raising=False)
    monkeypatch.setattr(odoo_router, "store", test_store, raising=False)
    monkeypatch.setattr(main, "store", test_store, raising=False)

    # Test-API-Key konfigurieren
    monkeypatch.setattr(config, "API_KEY", "test-key", raising=False)

    # Skriptausführung mocken (kein Helm/kubectl)
    monkeypatch.setattr(wp_service, "run_script", lambda *a, **k: "", raising=False)
    monkeypatch.setattr(odoo_service, "run_script", lambda *a, **k: "", raising=False)

    # Kubernetes-Status-Refresh mocken (macht einfach nichts)
    def fake_refresh(store, instances):
        return instances

    monkeypatch.setattr(status_service, "refresh_instance_statuses", fake_refresh, raising=False)
    monkeypatch.setattr(main, "refresh_instance_statuses", fake_refresh, raising=False)
    # Standard-Empfänger für Zugangsdaten-Mails in Tests

    return TestClient(main.app)


# -------------------------------------------------------------------
# WordPress: End-to-End über HTTP
# -------------------------------------------------------------------

def test_create_and_get_wordpress_instance_via_http(client: TestClient):
    headers = {"X-API-Key": "test-key"}

    # 1. Instanz anlegen
    resp = client.post(
        "/instances/wp",
        headers=headers,
        json={
            "slug": "kunde-http-wp",
            "domain": "kunde-http-wp.example.test",
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == "wp-kunde-http-wp"
    assert data["type"] == "wordpress"
    assert data["namespace"] == "wp-kunde-http-wp"
    assert data["domain"] == "kunde-http-wp.example.test"
    assert data["status"] == "running"

    instance_id = data["id"]

    # 2. GET /instances/{id}
    resp2 = client.get(f"/instances/{instance_id}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["id"] == instance_id
    assert data2["type"] == "wordpress"

    # 3. GET /instances (Liste)
    resp3 = client.get("/instances")
    assert resp3.status_code == 200
    items = resp3.json()
    assert isinstance(items, list)
    assert any(item["id"] == instance_id for item in items)

    # 4. Optional: Filter nach type=wordpress
    resp4 = client.get("/instances?type=wordpress")
    assert resp4.status_code == 200
    items_filtered = resp4.json()
    assert all(item["type"] == "wordpress" for item in items_filtered)
    assert any(item["id"] == instance_id for item in items_filtered)

def test_create_wordpress_instance_sends_access_email(
    client: TestClient,
    monkeypatch,
):
    calls = []

    def fake_send(instance, to_address=None):
        calls.append({"instance_id": instance.id, "to": to_address})

    # Wir patchen direkt den Service-Eintrittspunkt, NICHT den SMTP-Layer
    monkeypatch.setattr(
        email_service,
        "send_wordpress_access_email",
        fake_send,
        raising=False,
    )

    headers = {"X-API-Key": "test-key"}

    resp = client.post(
        "/instances/wp",
        headers=headers,
        json={
            "slug": "kunde-email-test",
            "domain": "kunde-email-test.example.test",
        },
    )
    assert resp.status_code == 200

    # Jetzt muss genau ein Aufruf erfolgt sein
    assert len(calls) == 1
    assert calls[0]["instance_id"] == "wp-kunde-email-test"


# -------------------------------------------------------------------
# Odoo: End-to-End über HTTP
# -------------------------------------------------------------------

def test_create_and_get_odoo_instance_via_http(client: TestClient):
    headers = {"X-API-Key": "test-key"}

    # 1. Odoo-Instanz anlegen
    resp = client.post(
        "/instances/odoo",
        headers=headers,
        json={
            "slug": "kunde-http-odoo",
            "domain": "kunde-http-odoo.example.test",
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == "odoo-kunde-http-odoo"
    assert data["type"] == "odoo"
    assert data["namespace"] == "odoo-kunde-http-odoo"
    assert data["domain"] == "kunde-http-odoo.example.test"
    assert data["status"] == "running"

    instance_id = data["id"]

    # 2. GET /instances/{id}
    resp2 = client.get(f"/instances/{instance_id}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["id"] == instance_id
    assert data2["type"] == "odoo"


# -------------------------------------------------------------------
# GET /instances/{id} mit unbekannter ID → 404
# -------------------------------------------------------------------

def test_get_unknown_instance_returns_404(client: TestClient):
    resp = client.get("/instances/does-not-exist")
    assert resp.status_code == 404

    body = resp.json()
    detail = body.get("detail")

    # Wir erwarten, dass detail ein Dict mit error-Code ist
    if isinstance(detail, dict):
        assert detail.get("error") == "instance_not_found"
    else:
        # Falls sich das Format mal ändert, prüfen wir auf sinnvollen Text
        text = str(detail).lower()
        assert "not found" in text or ("nicht" in text and "existiert" in text)

# -------------------------------------------------------------------
# WordPress: suspend/resume – Fehlerfall (404)
# -------------------------------------------------------------------

def test_suspend_unknown_wp_instance_returns_404(client: TestClient):
    headers = {"X-API-Key": "test-key"}

    resp = client.post(
        "/instances/wp/does-not-exist/suspend",
        headers=headers,
        json={"reason": "Test"},
    )

    assert resp.status_code == 404
    body = resp.json()
    detail = body.get("detail")
    if isinstance(detail, dict):
        assert detail.get("error") == "instance_not_found"
    else:
        text = str(detail).lower()
        assert "not found" in text or ("nicht" in text and "existiert" in text)

# -------------------------------------------------------------------
# WordPress: suspend/resume – Erfolg & Idempotenz
# -------------------------------------------------------------------

def test_suspend_and_resume_wordpress_instance_via_http(client: TestClient):
    headers = {"X-API-Key": "test-key"}

    # 1. Instanz anlegen
    resp_create = client.post(
        "/instances/wp",
        headers=headers,
        json={
            "slug": "kunde-suspend",
            "domain": "kunde-suspend.example.test",
        },
    )
    assert resp_create.status_code == 200
    data = resp_create.json()
    instance_id = data["id"]

    # Direkt nach dem Anlegen sollte suspended False sein
    assert data.get("suspended") is False
    assert data.get("suspend_reason") is None

    # 2. Suspend mit Grund
    resp_suspend = client.post(
        f"/instances/wp/{instance_id}/suspend",
        headers=headers,
        json={"reason": "Nicht bezahlt"},
    )
    assert resp_suspend.status_code == 200
    suspended_data = resp_suspend.json()
    assert suspended_data["id"] == instance_id
    assert suspended_data.get("suspended") is True
    assert suspended_data.get("suspend_reason") == "Nicht bezahlt"

    # 3. GET /instances/{id} → sollte auch suspended=True zeigen
    resp_get = client.get(f"/instances/{instance_id}")
    assert resp_get.status_code == 200
    got = resp_get.json()
    assert got["id"] == instance_id
    assert got.get("suspended") is True
    assert got.get("suspend_reason") == "Nicht bezahlt"

    # 4. Resume aufrufen
    resp_resume = client.post(
        f"/instances/wp/{instance_id}/resume",
        headers=headers,
    )
    assert resp_resume.status_code == 200
    resumed_data = resp_resume.json()
    assert resumed_data["id"] == instance_id
    assert resumed_data.get("suspended") is False
    assert resumed_data.get("suspend_reason") is None

    # 5. Idempotenz: zweites Resume darf nichts kaputt machen
    resp_resume_again = client.post(
        f"/instances/wp/{instance_id}/resume",
        headers=headers,
    )
    assert resp_resume_again.status_code == 200
    resumed_again_data = resp_resume_again.json()
    assert resumed_again_data["id"] == instance_id
    assert resumed_again_data.get("suspended") is False
    assert resumed_again_data.get("suspend_reason") is None

    # 6. Idempotenz: zweites Suspend mit anderem Grund aktualisiert nur den Grund
    resp_suspend_again = client.post(
        f"/instances/wp/{instance_id}/suspend",
        headers=headers,
        json={"reason": "Zweiter Grund"},
    )
    assert resp_suspend_again.status_code == 200
    suspended_again_data = resp_suspend_again.json()
    assert suspended_again_data["id"] == instance_id
    assert suspended_again_data.get("suspended") is True
    assert suspended_again_data.get("suspend_reason") == "Zweiter Grund"

def test_wordpress_health_ok(client: TestClient, monkeypatch):
    headers = {"X-API-Key": "test-key"}

    # 1. Instanz anlegen
    resp = client.post(
        "/instances/wp",
        headers=headers,
        json={
            "slug": "health-ok",
            "domain": "health-ok.local",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    instance_id = data["id"]

    # 2. httpx.get mocken → 200 OK
    class DummyResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    def fake_get(url, verify=False, timeout=5.0):
        # Optional: prüfen, ob die Domain stimmt
        assert "health-ok.local" in url
        return DummyResponse(200)

    monkeypatch.setattr(httpx, "get", fake_get, raising=False)

    # 3. Health-Endpoint aufrufen
    resp = client.get(f"/instances/wp/{instance_id}/health", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["http_status"] == 200

def test_wordpress_health_error_on_unexpected_status(client: TestClient, monkeypatch):
    headers = {"X-API-Key": "test-key"}

    # 1. Instanz anlegen
    resp = client.post(
        "/instances/wp",
        headers=headers,
        json={
            "slug": "health-error",
            "domain": "health-error.local",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    instance_id = data["id"]

    # 2. httpx.get mocken → 500 Internal Server Error
    class DummyResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    def fake_get(url, verify=False, timeout=5.0):
        return DummyResponse(500)

    monkeypatch.setattr(httpx, "get", fake_get, raising=False)

    # 3. Health-Endpoint aufrufen
    resp = client.get(f"/instances/wp/{instance_id}/health", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert body["http_status"] == 500
    assert "Unexpected status code" in body.get("detail", "")

def test_wordpress_health_unknown_instance_returns_404(client: TestClient):
    headers = {"X-API-Key": "test-key"}

    resp = client.get(
        "/instances/wp/does-not-exist/health",
        headers=headers,
    )
    assert resp.status_code == 404

def test_request_id_header_is_returned():
    client = TestClient(main.app)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Request-ID"]  # nicht leer


def test_request_id_header_is_preserved_if_sent():
    client = TestClient(main.app)

    custom_id = "test-request-id-123"
    resp = client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == custom_id
