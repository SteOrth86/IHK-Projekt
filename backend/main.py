from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI

from storage import store, Instance
from k8s_status import get_namespace_status
from config import INSTANCES_FILE
from services.status import refresh_instance_statuses
from routers.wordpress import router as wp_router
from routers.odoo import router as odoo_router

app = FastAPI(
    title="IHK-Projekt Backend",
    version="0.1.0",
)


# Router registrieren
app.include_router(wp_router, tags=["wordpress"])
app.include_router(odoo_router, tags=["odoo"])


@app.get("/health")
async def health():
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

