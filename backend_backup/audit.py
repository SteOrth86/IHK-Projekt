# audit.py
from __future__ import annotations

import json
import logging
from typing import Any

# Eigener Logger-Namespace für Audit-Einträge
logger = logging.getLogger("ihk_backend.audit")


def audit_event(action: str, **fields: Any) -> None:
    """
    Schreibt einen strukturierten Audit-Log-Eintrag.

    action:
        Kurze Bezeichnung des Ereignisses, z. B. "instance_suspended".
    fields:
        Zusatzinfos wie instance_id, suspended_before, suspended_after, reason, ...
    """
    payload = {"action": action, **fields}
    # request_id hängt durch den RequestIdFilter schon am LogRecord dran
    logger.info("AUDIT %s", json.dumps(payload, sort_keys=True, default=str))
