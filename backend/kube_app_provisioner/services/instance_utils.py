from __future__ import annotations

from datetime import datetime, timezone

from kube_app_provisioner.storage import InstanceStore


def now_iso() -> str:
    """Aktueller Zeitpunkt als ISO-8601-String in UTC."""
    return datetime.now(timezone.utc).isoformat()


def ensure_instance_uniqueness(
    store: InstanceStore, instance_id: str, domain: str
) -> None:
    """
    Stellt sicher, dass Instanz-ID und Domain noch nicht vergeben sind.
    """
    if store.id_exists(instance_id):
        raise ValueError(f"Instance '{instance_id}' already exists")

    if store.domain_exists(domain):
        raise ValueError(
            f"Domain '{domain}' wird bereits von einer anderen Instanz verwendet"
        )
