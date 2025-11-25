from typing import Iterable, List

from storage import Instance, InstanceStore
from k8s_status import get_namespace_status


def refresh_instance_statuses(
    store: InstanceStore,
    instances: Iterable[Instance],
) -> List[Instance]:
    """
    Aktualisiert für alle übergebenen Instanzen den Kubernetes-Status
    und speichert die Änderungen im InstanceStore.

    Gibt die aktualisierte Instanzliste zurück.
    """
    updated: List[Instance] = []
    for inst in instances:
        try:
            inst.status = get_namespace_status(inst.namespace)
        except Exception:
            # Wenn der Cluster nicht erreichbar ist oder kubectl einen Fehler liefert,
            # markieren wir den Status als "unknown", speichern aber trotzdem.
            inst.status = "unknown"
        store.update(inst)
        updated.append(inst)
    return updated
