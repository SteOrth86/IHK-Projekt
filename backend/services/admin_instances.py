from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional

from storage import Instance


def suspend_instance(instance: Instance, reason: Optional[str] = None) -> Instance:
    """
    Setzt eine Instanz auf 'suspended' und optional einen Sperrgrund.
    Idempotent: Wenn die Instanz bereits suspendiert ist, wird kein zweites Mal
    "scharf" gesperrt – nur der Grund kann aktualisiert werden.
    """
    if instance.suspended:
        # Idempotent: optional Grund aktualisieren, aber keinen zweiten Statuswechsel
        if reason is not None:
            instance.suspend_reason = reason
        return instance

    instance.suspended = True
    instance.suspend_reason = reason
    instance.updated_at = datetime.now(UTC)
    return instance


def resume_instance(instance: Instance) -> Instance:
    """
    Hebt eine Sperre wieder auf.
    Idempotent: Wenn die Instanz nicht suspendiert ist, passiert nichts.
    """
    if not instance.suspended:
        return instance

    instance.suspended = False
    instance.suspend_reason = None
    instance.updated_at = datetime.now(UTC)
    return instance
