from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from config import (
    WP_PROVISION_SCRIPT,
    WP_DELETE_SCRIPT,
    ODOO_PROVISION_SCRIPT,
    ODOO_DELETE_SCRIPT,
)


def _check_binary(name: str) -> bool:
    """Prüft, ob ein Kommando im PATH verfügbar ist (z. B. kubectl, helm)."""
    return shutil.which(name) is not None


def _check_kubernetes() -> Dict[str, Any]:
    """
    Prüft, ob kubectl vorhanden ist und der Cluster erreichbar ist.

    Schnelltest: `kubectl get ns kube-system -o name`
    """
    if not _check_binary("kubectl"):
        return {"ok": False, "reason": "kubectl_not_found"}

    try:
        result = subprocess.run(
            ["kubectl", "get", "ns", "kube-system", "-o", "name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        return {"ok": False, "reason": f"kubectl_call_failed: {exc}"}

    if result.returncode != 0:
        return {
            "ok": False,
            "reason": result.stderr.strip() or "kubectl_get_ns_failed",
        }

    return {"ok": True, "reason": None}


def _file_exists(path_like: Any) -> bool:
    """Hilfsfunktion: robustes File-Exist-Check (Path oder str)."""
    return Path(path_like).is_file()


def _check_scripts() -> Dict[str, Any]:
    """
    Prüft, ob die erwarteten Provisionierungs-/Lösch-Skripte existieren.
    """
    return {
        "wp_provision_exists": _file_exists(WP_PROVISION_SCRIPT),
        "wp_delete_exists": _file_exists(WP_DELETE_SCRIPT),
        "odoo_provision_exists": _file_exists(ODOO_PROVISION_SCRIPT),
        "odoo_delete_exists": _file_exists(ODOO_DELETE_SCRIPT),
    }


def get_health_status() -> Dict[str, Any]:
    """
    Aggregierter Health-Status für das Backend.

    – backend: ob die App selbst läuft
    – kubernetes: Erreichbarkeit des Clusters
    – scripts: Existenz der Bash-Skripte
    """
    k8s = _check_kubernetes()
    scripts = _check_scripts()

    return {
        "backend": {"ok": True},
        "kubernetes": k8s,
        "scripts": scripts,
    }
