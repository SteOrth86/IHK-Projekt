# services/orders.py

from kube_app_provisioner.common.audit import audit_event
from kube_app_provisioner.core.models import Order
from kube_app_provisioner.core.storage import Instance, InstanceStore, store
from kube_app_provisioner.services.apps.wordpress import create_wordpress_instance


def provision_wordpress_for_order(
    order: Order,
    instance_store: InstanceStore | None = None,
) -> Instance:
    """
    Legt eine neue WordPress-Instanz fuer die gegebene Order an (voller Lifecycle).
    """
    target_store = instance_store or store

    instance = create_wordpress_instance(
        slug=order.instance_slug,
        domain=order.domain,
        store=target_store,
    )

    audit_event(
        "wordpress_instance_created_for_order",
        order_id=order.id,
        product_type=order.product_type,
        instance_id=instance.id,
        namespace=instance.namespace,
        domain=instance.domain,
        order_status=order.status,
        instance_status=instance.status,
    )

    return instance
