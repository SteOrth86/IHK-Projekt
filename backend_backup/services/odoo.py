# backend/services/odoo.py
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import config
from storage import Instance, InstanceStore
from utils.commands import run_script, ScriptError


def _now_iso() -> str:
    """Hilfsfunktion: aktueller Zeitpunkt als ISO-8601-String in UTC."""
    return datetime.now(timezone.utc).isoformat()


def _instance_exists_in_file(instance_id: str) -> bool:
    """
    Prüft direkt in der Instanz-Datei, ob eine Instanz-ID bereits existiert.
    Unabhängig vom aktuellen InstanceStore-Objekt.
    """
    path = Path(config.INSTANCES_FILE)
    if not path.exists():
        return False

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False

    if not isinstance(data, list):
        return False

    return any(item.get("id") == instance_id for item in data)


def _domain_exists_in_file(domain: str) -> bool:
    """
    Prüft, ob eine Domain bereits von einer Instanz (egal ob WP oder Odoo)
    verwendet wird.
    """
    path = Path(config.INSTANCES_FILE)
    if not path.exists():
        return False

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False

    if not isinstance(data, list):
        return False

    domain = domain.strip().lower()

    for item in data:
        if not isinstance(item, dict):
            continue
        existing = item.get("domain")
        if not isinstance(existing, str):
            continue
        if existing.strip().lower() == domain:
            return True

    return False


def create_odoo_instance(
    slug: str,
    domain: str,
    store: InstanceStore,
) -> Instance:
    """
    Erzeugt eine neue Odoo-Instanz.

    Schritte:
    - Validierung von slug/domain.
    - Prüfen, ob ID und Domain bereits existieren.
    - Instance-Objekt mit Status "creating" erzeugen und speichern.
    - provision_odoo.sh aufrufen.
    - Bei Erfolg: Status auf "running" setzen.
    - Bei Fehler: Status auf "error" setzen und ScriptError weiterwerfen.
    """
    if not slug:
        raise ValueError("slug must not be empty")
    if not domain:
        raise ValueError("domain must not be empty")

    namespace = f"odoo-{slug}"
    instance_id = f"odoo-{slug}"

    # 1. ID darf nicht doppelt sein
    if _instance_exists_in_file(instance_id):
        raise ValueError(f"Instance '{instance_id}' already exists")

    # 2. Domain darf systemweit nur einmal vorkommen (WP + Odoo)
    if _domain_exists_in_file(domain):
        raise ValueError(f"Domain '{domain}' wird bereits von einer anderen Instanz verwendet")

    instance = Instance(
        id=instance_id,
        type="odoo",
        namespace=namespace,
        domain=domain,
        created_at=_now_iso(),
        updated_at=_now_iso(),
        status="creating",
    )
    store.add(instance)

    try:
        # ./provision_odoo.sh <slug> <domain>
        run_script(str(config.ODOO_PROVISION_SCRIPT), slug, domain)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise
    else:
        instance.status = "running"
        instance.updated_at = _now_iso()
        store.update(instance)

    return instance


def delete_odoo_instance(
    instance: Instance,
    store: InstanceStore,
) -> None:
    """
    Löscht eine bestehende Odoo-Instanz.

    Schritte:
    - Status auf "deleting" setzen.
    - delete_odoo.sh aufrufen.
    - Bei Fehler: Status auf "error" und ScriptError weiterwerfen.
    - Bei Erfolg: Instanz aus dem Store entfernen.
    """
    instance.status = "deleting"
    instance.updated_at = _now_iso()
    store.update(instance)

    try:
        # ./delete_odoo.sh <namespace>
        run_script(str(config.ODOO_DELETE_SCRIPT), instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    store.remove(instance.id)
