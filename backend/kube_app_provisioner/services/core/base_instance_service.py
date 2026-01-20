from __future__ import annotations

from typing import Callable, Optional

from kube_app_provisioner.services.core.admin_instances import resume_instance, suspend_instance
from kube_app_provisioner.services.core.instance_utils import ensure_instance_uniqueness, now_iso
from kube_app_provisioner.core.storage import Instance, InstanceStore
from kube_app_provisioner.utils.commands import ScriptError, run_script


PostProvisionHook = Callable[[Instance], None]


class UnsupportedOperationError(Exception):
    """Wird geworfen, wenn eine Operation (z. B. suspend/resume) nicht konfiguriert ist."""


class BaseInstanceService:
    """
    Gemeinsamer Lifecycle für Instanz-Typen (create/delete/suspend/resume).
    Konkrete Services liefern nur noch ihre Skripte und können Hooks setzen.
    """

    def __init__(
        self,
        *,
        type_name: str,
        namespace_prefix: str,
        provision_script: str,
        delete_script: str,
        suspend_script: Optional[str] = None,
        resume_script: Optional[str] = None,
    ) -> None:
        self.type_name = type_name
        self.namespace_prefix = namespace_prefix
        self.provision_script = provision_script
        self.delete_script = delete_script
        self.suspend_script = suspend_script
        self.resume_script = resume_script

    def _build_ids(self, slug: str) -> tuple[str, str]:
        namespace = f"{self.namespace_prefix}{slug}"
        instance_id = namespace
        return instance_id, namespace

    def create_instance(
        self,
        *,
        slug: str,
        domain: str,
        store: InstanceStore,
        post_provision: Optional[PostProvisionHook] = None,
    ) -> Instance:
        if not slug:
            raise ValueError("slug must not be empty")
        if not domain:
            raise ValueError("domain must not be empty")

        instance_id, namespace = self._build_ids(slug)
        ensure_instance_uniqueness(store, instance_id, domain)

        instance = Instance(
            id=instance_id,
            type=self.type_name,
            namespace=namespace,
            domain=domain,
            created_at=now_iso(),
            updated_at=now_iso(),
            status="creating",
        )
        store.add(instance)

        try:
            run_script(self.provision_script, slug, domain)
        except ScriptError:
            instance.status = "error"
            instance.updated_at = now_iso()
            store.update(instance)
            raise
        else:
            instance.status = "running"
            instance.updated_at = now_iso()
            store.update(instance)

            if post_provision:
                post_provision(instance)

        return instance

    def delete_instance(self, *, instance: Instance, store: InstanceStore) -> None:
        instance.status = "deleting"
        instance.updated_at = now_iso()
        store.update(instance)

        try:
            run_script(self.delete_script, instance.namespace)
        except ScriptError:
            instance.status = "error"
            instance.updated_at = now_iso()
            store.update(instance)
            raise

        store.remove(instance.id)

    def suspend_instance(
        self,
        *,
        instance: Instance,
        store: InstanceStore,
        reason: Optional[str] = None,
    ) -> Instance:
        if self.suspend_script is None:
            raise UnsupportedOperationError(
                f"Suspend fuer {self.type_name} nicht konfiguriert"
            )

        if getattr(instance, "suspended", False):
            suspend_instance(instance, reason=reason)
            instance.updated_at = now_iso()
            store.update(instance)
            return instance

        try:
            run_script(self.suspend_script, instance.namespace)
        except ScriptError:
            instance.status = "error"
            instance.updated_at = now_iso()
            store.update(instance)
            raise

        suspend_instance(instance, reason=reason)
        instance.updated_at = now_iso()
        store.update(instance)
        return instance

    def resume_instance(self, *, instance: Instance, store: InstanceStore) -> Instance:
        if self.resume_script is None:
            raise UnsupportedOperationError(
                f"Resume fuer {self.type_name} nicht konfiguriert"
            )

        if not getattr(instance, "suspended", False):
            return instance

        try:
            run_script(self.resume_script, instance.namespace)
        except ScriptError:
            instance.status = "error"
            instance.updated_at = now_iso()
            store.update(instance)
            raise

        resume_instance(instance)
        instance.updated_at = now_iso()
        store.update(instance)
        return instance
