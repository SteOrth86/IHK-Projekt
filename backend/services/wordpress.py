# backend/services/wordpress.py
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
        # Wenn die Datei kaputt ist, behandeln wir es wie "keine Instanz"
        return False

    if not isinstance(data, list):
        return False

    return any(item.get("id") == instance_id for item in data)


def create_wordpress_instance(
    slug: str,
    domain: str,
    store: InstanceStore,
) -> Instance:
    """
    Erzeugt eine neue WordPress-Instanz.
    """
    if not slug:
        raise ValueError("slug must not be empty")
    if not domain:
        raise ValueError("domain must not be empty")

    namespace = f"wp-{slug}"
    instance_id = f"wp-{slug}"

    if _instance_exists_in_file(instance_id):
        raise ValueError(f"Instance '{instance_id}' already exists")
    instance = Instance(
        id=instance_id,
        type="wordpress",
        namespace=namespace,
        domain=domain,
        created_at=_now_iso(),
        updated_at=_now_iso(),
        status="creating",
    )
    store.add(instance)

    try:
        run_script(config.WP_PROVISION_SCRIPT, slug, domain)
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


def delete_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
) -> None:
    """
    Löscht eine bestehende WordPress-Instanz.

    Schritte:
    - Status auf "deleting" setzen.
    - delete_wp.sh aufrufen.
    - Bei Fehler: Status auf "error" und ScriptError weiterwerfen.
    - Bei Erfolg: Instanz aus dem Store entfernen.
    """
    instance.status = "deleting"
    instance.updated_at = _now_iso()
    store.update(instance)

    try:
        # ⚠️ Argumente an dein reales Skript anpassen.
        # Beispiel: ./delete_wp.sh <namespace>
        run_script(config.WP_DELETE_SCRIPT, instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    store.remove(instance.id)
