# backend/services/wordpress.py
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

import config
from storage import Instance, InstanceStore
from utils.commands import run_script, ScriptError
from services.admin_instances import (
    suspend_instance as core_suspend_instance,
    resume_instance as core_resume_instance,
)

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

    # 1. ID darf nicht doppelt sein
    if _instance_exists_in_file(instance_id):
        raise ValueError(f"Instance '{instance_id}' already exists")

    # 2. Domain darf systemweit nur einmal vorkommen (WP + Odoo)
    if _domain_exists_in_file(domain):
        raise ValueError(f"Domain '{domain}' wird bereits von einer anderen Instanz verwendet")

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
        run_script(str(config.WP_PROVISION_SCRIPT), slug, domain)
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
        # ./delete_wp.sh <namespace>
        run_script(str(config.WP_DELETE_SCRIPT), instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    store.remove(instance.id)

def suspend_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
    reason: Optional[str] = None,
) -> Instance:
    """
    Sperrt eine bestehende WordPress-Instanz.

    Ablauf:
    - Wenn bereits suspendiert: nur Reason aktualisieren, kein Skript-Aufruf (idempotent).
    - Wenn noch nicht suspendiert:
      - suspend_wp.sh mit Namespace aufrufen
      - bei Erfolg: suspended-Flag + optionalen Grund setzen und speichern
      - bei ScriptError: Status auf "error", speichern, Fehler weiterwerfen.
    """
    # Bereits suspendiert? → idempotent, kein Skript
    if getattr(instance, "suspended", False):
        core_suspend_instance(instance, reason=reason)
        instance.updated_at = _now_iso()
        store.update(instance)
        return instance

    # Noch nicht suspendiert → Skript ausführen
    try:
        # ./suspend_wp.sh <namespace>
        run_script(str(config.WP_SUSPEND_SCRIPT), instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    # Wenn Skript erfolgreich war, Flag setzen
    core_suspend_instance(instance, reason=reason)
    instance.updated_at = _now_iso()
    store.update(instance)
    return instance


def resume_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
) -> Instance:
    """
    Hebt die Sperre einer WordPress-Instanz wieder auf.

    Ablauf:
    - Wenn nicht suspendiert: nichts tun (idempotent, kein Skript).
    - Wenn suspendiert:
      - resume_wp.sh mit Namespace aufrufen
      - bei Erfolg: suspended-Flag zurücksetzen und speichern
      - bei ScriptError: Status auf "error", speichern, Fehler weiterwerfen.
    """
    # Nicht suspendiert? → idempotent, kein Skript
    if not getattr(instance, "suspended", False):
        return instance

    try:
        # ./resume_wp.sh <namespace>
        run_script(str(config.WP_RESUME_SCRIPT), instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    # Wenn Skript erfolgreich, Flag zurücksetzen
    core_resume_instance(instance)
    instance.updated_at = _now_iso()
    store.update(instance)
    return instance
