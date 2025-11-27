# backend/services/odoo.py
from __future__ import annotations

from kube_app_provisioner.core import config
from kube_app_provisioner.services.core.base_instance_service import BaseInstanceService
from kube_app_provisioner.core.storage import Instance, InstanceStore


def create_odoo_instance(
    slug: str,
    domain: str,
    store: InstanceStore,
) -> Instance:
    """
    Erzeugt eine neue Odoo-Instanz.
    """
    return odoo_service.create_instance(
        slug=slug,
        domain=domain,
        store=store,
    )


def delete_odoo_instance(
    instance: Instance,
    store: InstanceStore,
) -> None:
    """
    Loescht eine bestehende Odoo-Instanz.
    """
    odoo_service.delete_instance(instance=instance, store=store)


def suspend_odoo_instance(
    instance: Instance,
    store: InstanceStore,
    reason: str | None = None,
) -> Instance:
    """
    Sperrt eine Odoo-Instanz (aktuell nicht konfiguriert -> 501).
    """
    return odoo_service.suspend_instance(
        instance=instance,
        store=store,
        reason=reason,
    )


def resume_odoo_instance(
    instance: Instance,
    store: InstanceStore,
) -> Instance:
    """
    Hebt eine Sperre fuer eine Odoo-Instanz auf (aktuell nicht konfiguriert -> 501).
    """
    return odoo_service.resume_instance(
        instance=instance,
        store=store,
    )


odoo_service = BaseInstanceService(
    type_name="odoo",
    namespace_prefix="odoo-",
    provision_script=str(config.ODOO_PROVISION_SCRIPT),
    delete_script=str(config.ODOO_DELETE_SCRIPT),
    suspend_script=str(config.ODOO_SUSPEND_SCRIPT),
    resume_script=str(config.ODOO_RESUME_SCRIPT),
)
