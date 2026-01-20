import logging

from typing import List, Optional

from fastapi import FastAPI, HTTPException

from request_id import request_id_var
from request_id_middleware import RequestIdMiddleware

from storage import store, Instance
from services.status import refresh_instance_statuses
from services.health import get_health_status
from routers.wordpress import router as wp_router
from routers.odoo import router as odoo_router
from routers.orders import router as orders_router
from routers.stripe_webhooks import router as stripe_webhooks_router

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

logger = logging.getLogger("ihk_backend")


app = FastAPI(
    title="IHK-Projekt Backend",
    version="0.1.0",
)

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
        # Später können wir das auf ErrorResponse umstellen
        raise HTTPException(
            status_code=404,
            detail=f"Instance '{instance_id}' not found",
        )

    refresh_instance_statuses(store,[instance])

    return instance
