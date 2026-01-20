# backend/status.py
from enum import Enum
from typing import Iterable


class InstanceStatus(str, Enum):
    RUNNING = "running"
    PENDING = "pending"
    ERROR = "error"
    UNKNOWN = "unknown"


def map_pod_statuses_to_instance_status(pod_statuses: Iterable[str]) -> InstanceStatus:
    """
    Mappt eine Liste von STATUS-Werten aus `kubectl get pods` auf einen
    vereinfachten Instanzstatus für das Backend.
    """
    statuses = [s.strip() for s in pod_statuses if s and s.strip()]
    if not statuses:
        # Keine Pods gefunden (Namespace frisch angelegt oder Fehler)
        return InstanceStatus.UNKNOWN

    # 🔴 Fehlerzustände haben Priorität
    error_markers = {"CrashLoopBackOff", "ImagePullBackOff", "Error", "OOMKilled"}
    if any(s in error_markers for s in statuses):
        return InstanceStatus.ERROR

    # ✅ Alle Pods laufen
    if all(s == "Running" for s in statuses):
        return InstanceStatus.RUNNING

    # 🟡 Noch im Aufbau (Pending / Init / ContainerCreating)
    pending_prefixes = ("Pending", "ContainerCreating", "Init:")
    if any(s.startswith(pending_prefixes) for s in statuses):
        return InstanceStatus.PENDING

    # Fallback
    return InstanceStatus.UNKNOWN
