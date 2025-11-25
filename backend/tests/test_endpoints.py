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
import main


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

