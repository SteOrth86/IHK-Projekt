# backend/k8s_status.py
import subprocess
from typing import List

from kube_app_provisioner.core.status import InstanceStatus, map_pod_statuses_to_instance_status


def _get_pod_statuses_for_namespace(namespace: str) -> List[str]:
    """
    Liest die STATUS-Spalte aller Pods in einem Namespace aus.
    Nutzt: `kubectl get pods -n <ns> --no-headers`.
    """
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "--no-headers"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    statuses: List[str] = []
    for line in lines:
        # Format: NAME READY STATUS RESTARTS AGE
        parts = line.split()
        if len(parts) >= 3:
            statuses.append(parts[2])
    return statuses


def get_namespace_status(namespace: str) -> str:
    """
    Gibt einen vereinfachten Status-String für eine Instanz zurück:

    - "running"
    - "pending"
    - "error"
    - "unknown"
    """
    pod_statuses = _get_pod_statuses_for_namespace(namespace)
    instance_status = map_pod_statuses_to_instance_status(pod_statuses)
    return instance_status.value
