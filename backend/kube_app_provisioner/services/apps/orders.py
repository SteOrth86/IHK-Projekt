# services/orders.py

from kube_app_provisioner.common.audit import audit_event
from kube_app_provisioner.core.models import Order
from kube_app_provisioner.services.core.instance_utils import now_iso
from kube_app_provisioner.core.storage import Instance, store


def provision_wordpress_for_order(order: Order) -> Instance:
    """
    Legt eine neue WordPress-Instanz fuer die gegebene Order an.

    Aktuell:
    - erzeugt nur einen Instance-Eintrag im InstanceStore
    - spaeter kann hier der Aufruf des Shell-Skripts ergaenzt werden
    """

    instance_id = f"wp-{order.instance_slug}"
    namespace = f"wp-{order.instance_slug}"
    timestamp = now_iso()

    instance = Instance(
        id=instance_id,
        type="wordpress",
        namespace=namespace,
        domain=order.domain,
        created_at=timestamp,
        updated_at=timestamp,
        status="creating",
    )

    store.add(instance)

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

    # TODO: Provisionierungs-Skript aufrufen (z. B. run_script + config.WP_PROVISION_SCRIPT)

    return instance
