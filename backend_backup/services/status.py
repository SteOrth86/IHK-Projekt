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

def list_instances_with_status(
    store: InstanceStore,
    type_filter: str | None = None,
) -> List[Instance]:
    """
    Lädt alle Instanzen aus dem Store, filtert optional nach type
    (z. B. 'wordpress' oder 'odoo'), aktualisiert deren Status über Kubernetes
    und speichert die aktualisierten Instanzen wieder im Store.
    """
    instances = store.list()

    if type_filter:
        instances = [inst for inst in instances if inst.type == type_filter]

    return refresh_instance_statuses(store=store, instances=instances)
