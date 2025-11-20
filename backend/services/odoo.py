# backend/services/odoo.py
from __future__ import annotations

from datetime import datetime, timezone

from .. import config
from ..storage import Instance, InstanceStore
from ..utils.commands import run_script, ScriptError


def _now_iso() -> str:
    """Hilfsfunktion: aktueller Zeitpunkt als ISO-8601-String in UTC."""
    return datetime.now(timezone.utc).isoformat()


def create_odoo_instance(
    slug: str,
    domain: str,
    store: InstanceStore,
) -> Instance:
    """
    Erzeugt eine neue Odoo-Instanz.

    Schritte:
    - Validierung von slug/domain.
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
        # ⚠️ Falls dein Script andere Argumente erwartet, hier anpassen.
        # Typisch wäre z.B.: ./provision_odoo.sh <slug> <domain>
        run_script(config.ODOO_PROVISION_SCRIPT, slug, domain)
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
        # ⚠️ Argumente an dein reales Skript anpassen.
        # Beispiel: ./delete_odoo.sh <namespace>
        run_script(config.ODOO_DELETE_SCRIPT, instance.namespace)
    except ScriptError:
        instance.status = "error"
        instance.updated_at = _now_iso()
        store.update(instance)
        raise

    store.remove(instance.id)
