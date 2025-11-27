from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional

from kube_app_provisioner.storage import Instance
from kube_app_provisioner.audit import audit_event


def suspend_instance(instance: Instance, reason: Optional[str] = None) -> Instance:
    """
    Setzt eine Instanz auf 'suspended' und optional einen Sperrgrund.
    Idempotent: Wenn die Instanz bereits suspendiert ist, wird kein zweites Mal
    "scharf" gesperrt – nur der Grund kann aktualisiert werden.
    """
    if instance.suspended:
        # Idempotent: optional Grund aktualisieren, aber keinen zweiten Statuswechsel
        if reason is not None and reason != instance.suspend_reason:
            previous_reason = instance.suspend_reason
            instance.suspend_reason = reason
            instance.updated_at = datetime.now(UTC)

            audit_event(
                "instance_suspend_reason_updated",
                instance_id=instance.id,
                namespace=instance.namespace,
                type=instance.type,
                suspended_before=True,
                suspended_after=True,
                previous_reason=previous_reason,
                new_reason=reason,
            )
        return instance

    # Instanz zum ersten Mal sperren
    instance.suspended = True
    instance.suspend_reason = reason
    instance.updated_at = datetime.now(UTC)

    audit_event(
        "instance_suspended",
        instance_id=instance.id,
        namespace=instance.namespace,
        type=instance.type,
        suspended_before=False,
        suspended_after=True,
        suspend_reason=reason,
    )

    return instance


def resume_instance(instance: Instance) -> Instance:
    """
    Hebt eine Sperre wieder auf.
    Idempotent: Wenn die Instanz nicht suspendiert ist, passiert nichts.
    """
    if not instance.suspended:
        return instance

    previous_reason = instance.suspend_reason

    instance.suspended = False
    instance.suspend_reason = None
    instance.updated_at = datetime.now(UTC)

    audit_event(
        "instance_resumed",
        instance_id=instance.id,
        namespace=instance.namespace,
        type=instance.type,
        suspended_before=True,
        suspended_after=False,
        previous_reason=previous_reason,
    )

    return instance
