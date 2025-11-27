# backend/services/wordpress.py
from __future__ import annotations

from typing import Optional

import httpx

from kube_app_provisioner.core import config
from kube_app_provisioner.schemas.health import InstanceHealth
from kube_app_provisioner.services.apps import email as email_service
from kube_app_provisioner.services.core.base_instance_service import BaseInstanceService
from kube_app_provisioner.core.storage import Instance, InstanceStore


wp_service = BaseInstanceService(
    type_name="wordpress",
    namespace_prefix="wp-",
    provision_script=str(config.WP_PROVISION_SCRIPT),
    delete_script=str(config.WP_DELETE_SCRIPT),
    suspend_script=str(config.WP_SUSPEND_SCRIPT),
    resume_script=str(config.WP_RESUME_SCRIPT),
)


def create_wordpress_instance(
    slug: str,
    domain: str,
    store: InstanceStore,
) -> Instance:
    return wp_service.create_instance(
        slug=slug,
        domain=domain,
        store=store,
        post_provision=email_service.send_wordpress_access_email,
    )


def delete_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
) -> None:
    """
    Loescht eine bestehende WordPress-Instanz.
    """
    wp_service.delete_instance(instance=instance, store=store)


def check_wordpress_health(instance: Instance) -> InstanceHealth:
    """
    Einfache Health-/Smoke-Pruefung fuer eine WordPress-Instanz.
    """
    url = f"https://{instance.domain}/wp-login.php"

    try:
        resp = httpx.get(url, verify=False, timeout=5.0)
    except httpx.RequestError as exc:
        return InstanceHealth(
            status="error",
            http_status=None,
            detail=f"RequestError for {url}: {exc}",
        )

    if resp.status_code in (200, 302):
        return InstanceHealth(
            status="ok",
            http_status=resp.status_code,
            detail=None,
        )

    return InstanceHealth(
        status="error",
        http_status=resp.status_code,
        detail=f"Unexpected status code {resp.status_code} for {url}",
    )


def suspend_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
    reason: Optional[str] = None,
) -> Instance:
    """
    Sperrt eine bestehende WordPress-Instanz.
    """
    return wp_service.suspend_instance(
        instance=instance,
        store=store,
        reason=reason,
    )


def resume_wordpress_instance(
    instance: Instance,
    store: InstanceStore,
) -> Instance:
    """
    Hebt die Sperre einer WordPress-Instanz auf.
    """
    return wp_service.resume_instance(
        instance=instance,
        store=store,
    )
