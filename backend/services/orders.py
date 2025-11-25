# services/orders.py

from datetime import datetime

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
        id=order.instance_slug,
        type="wordpress",
        namespace=order.instance_slug,
        domain=order.domain,
        created_at=now,
        updated_at=now,
        status="creating",
    )

    store.add(instance)

    # TODO: hier später das eigentliche Provisionierungs-Skript aufrufen
    # (z. B. via run_script und config.WP_PROVISION_SCRIPT)

    return instance
