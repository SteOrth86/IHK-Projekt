# backend/tests/test_instances_conflicts.py

import sys
from pathlib import Path

# Projekt-Root (backend-Ordner) auf sys.path legen,
# damit "import config", "from routers import wordpress" etc. funktionieren.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi import HTTPException

from kube_app_provisioner import config
from kube_app_provisioner import storage
from kube_app_provisioner.storage import InstanceStore
from kube_app_provisioner.routers import wordpress as wp_router
from kube_app_provisioner.routers import odoo as odoo_router
from kube_app_provisioner.services import wordpress as wp_service
from kube_app_provisioner.services import odoo as odoo_service


def setup_isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> InstanceStore:
    """
    Richtet für Tests eine eigene Instanz-Datei und einen eigenen InstanceStore ein,
    damit wir nicht mit echten Daten arbeiten.
    """
    instances_file = tmp_path / "instances.json"

    # config so patchen, dass Services/Helper auf die Test-Datei zeigen
    monkeypatch.setattr(config, "INSTANCES_FILE", instances_file)

    # Eigenen Store auf Basis der Test-Datei anlegen
    test_store = InstanceStore(instances_file)

    # Globalen Store in storage + Routern auf unseren Test-Store umbiegen
    monkeypatch.setattr(storage, "store", test_store, raising=False)
    monkeypatch.setattr(wp_router, "store", test_store, raising=False)
    monkeypatch.setattr(odoo_router, "store", test_store, raising=False)

    # run_script in den Services durch einen Dummy ersetzen (kein echtes Skript-Call)
    monkeypatch.setattr(wp_service, "run_script", lambda *a, **k: "", raising=False)
    monkeypatch.setattr(odoo_service, "run_script", lambda *a, **k: "", raising=False)

    return test_store


# -------------------------------------------------------------------
# WordPress: Domain-Konflikt → HTTP 409
# -------------------------------------------------------------------

def test_wp_domain_conflict_results_in_http_409(tmp_path, monkeypatch):
    setup_isolated_store(tmp_path, monkeypatch)

    # Import nach dem Setup, damit der Router den gepatchten Store nutzt
    from kube_app_provisioner.routers.wordpress import WordPressCreateRequest, create_wp_instance

    # 1. Instanz mit Domain anlegen → sollte funktionieren
    req1 = WordPressCreateRequest(
        slug="kunde-api-1",
        domain="dup-domain.example.test",
    )
    inst1 = create_wp_instance(req1)
    assert inst1.domain == "dup-domain.example.test"

    # 2. zweite Instanz mit anderer slug aber gleicher Domain → 409 erwartet
    req2 = WordPressCreateRequest(
        slug="kunde-api-2",
        domain="dup-domain.example.test",
    )

    with pytest.raises(HTTPException) as excinfo:
        create_wp_instance(req2)

    err = excinfo.value
    assert err.status_code == 409

    detail = err.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "wp_conflict"
    assert "wird bereits von einer anderen Instanz verwendet" in detail.get("detail", "")


# -------------------------------------------------------------------
# Odoo: Domain-Konflikt → HTTP 409
# -------------------------------------------------------------------

def test_odoo_domain_conflict_results_in_http_409(tmp_path, monkeypatch):
    setup_isolated_store(tmp_path, monkeypatch)

    from kube_app_provisioner.routers.odoo import OdooCreateRequest, create_odoo_instance

    # 1. Odoo-Instanz mit Domain anlegen
    req1 = OdooCreateRequest(
        slug="kunde-odoo-api-1",
        domain="dup-domain-odoo.example.test",
    )
    inst1 = create_odoo_instance(req1)
    assert inst1.domain == "dup-domain-odoo.example.test"

    # 2. zweite Odoo-Instanz mit anderer slug aber gleicher Domain → 409
    req2 = OdooCreateRequest(
        slug="kunde-odoo-api-2",
        domain="dup-domain-odoo.example.test",
    )

    with pytest.raises(HTTPException) as excinfo:
        create_odoo_instance(req2)

    err = excinfo.value
    assert err.status_code == 409

    detail = err.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "odoo_conflict"
    assert "wird bereits von einer anderen Instanz verwendet" in detail.get("detail", "")
