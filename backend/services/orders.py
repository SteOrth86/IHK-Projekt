# services/orders.py

from datetime import datetime

from audit import audit_event

from models import Order
from storage import Instance, store


def provision_wordpress_for_order(order: Order) -> Instance:
    """
    Legt eine neue WordPress-Instanz für die gegebene Order an.

    Aktuell:
    – erzeugt nur einen Instance-Eintrag im InstanceStore
    – später kann hier der Aufruf des Shell-Skripts ergänzt werden
    """

    now = datetime.utcnow().isoformat()

    instance = Instance(
        id=instance_id,
        type="wordpress",
        namespace=order.instance_slug,
        domain=order.domain,
        created_at=now,
        updated_at=now,
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

    # TODO: hier später das eigentliche Provisionierungs-Skript aufrufen
    # (z. B. via run_script und config.WP_PROVISION_SCRIPT)

    return instance
