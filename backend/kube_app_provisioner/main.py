import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="TrendTec Provisioning API",
    version="1.0",
    description="API zur automatisierten Bereitstellung und Verwaltung von WordPress-Instanzen.",
    docs_url="/docs",
    redoc_url="/redoc"
)

from kube_app_provisioner.common.request_id import request_id_var
from kube_app_provisioner.common.request_id_middleware import RequestIdMiddleware
from kube_app_provisioner.core.storage import Instance, store
from kube_app_provisioner.services.apps.status import refresh_instance_statuses
from kube_app_provisioner.services.apps.health import get_health_status
from kube_app_provisioner.routers.wordpress import router as wp_router
from kube_app_provisioner.routers.odoo import router as odoo_router
from kube_app_provisioner.routers.orders import router as orders_router
from kube_app_provisioner.routers.stripe_webhooks import router as stripe_webhooks_router

# Zentrales Logging-Setup für das Backend (mit request_id)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
)


class RequestIdFilter(logging.Filter):
    """
    Logging-Filter, der jeder Log-Nachricht eine request_id hinzufügt.

    Hintergrund:
    - Unser Format nutzt %(request_id)s.
    - Ohne diesen Filter würden Logs ohne request_id (z. B. in Background-Jobs)
      einen KeyError auslösen.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rid = request_id_var.get()
        except LookupError:
            rid = None

        # Default "-", wenn kein Request-Kontext vorhanden ist
        record.request_id = rid or "-"
        return True


# Filter global am Root-Logger registrieren,
# damit alle Logs (auch aus utils.commands etc.) eine request_id bekommen.
logging.getLogger().addFilter(RequestIdFilter())

logger = logging.getLogger("kube_app_provisioner")



# request_id-Middleware aktivieren
app.add_middleware(RequestIdMiddleware)

# Router registrieren
app.include_router(wp_router, tags=["wordpress"])
app.include_router(odoo_router, tags=["odoo"])
app.include_router(orders_router, tags=["orders"])
app.include_router(stripe_webhooks_router, tags=["stripe"])

@app.get("/health")
def health():
    logger.info("Health-Check aufgerufen")
    return {"status": "ok"}


@app.get("/instances", response_model=List[Instance])
def list_all_instances(type: Optional[str] = None) -> List[Instance]:
    """
    Liefert alle Instanzen (optional nach type gefiltert)
    und aktualisiert vorher deren Kubernetes-Status.
    """
    instances = store.list()

    if type:
        instances = [inst for inst in instances if inst.type == type]

    return refresh_instance_statuses(store=store, instances=instances)

@app.get("/instances/{instance_id}", response_model=Instance)
def get_instance_by_id(instance_id: str):
    """
    Eine einzelne Instanz (WordPress oder Odoo) anhand ihrer ID zurückgeben.

    - aktualisiert vor der Rückgabe den Status aus dem Kubernetes-Cluster
    - liefert 404, wenn es die Instanz nicht gibt
    """
    instance = store.get(instance_id)

    if instance is None:
        raise HTTPException(
            status_code=404,
            detail=f"Instance '{instance_id}' not found",
        )

    refresh_instance_statuses(store,[instance])

    return instance
