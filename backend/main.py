from datetime import datetime
from typing import List

from fastapi import FastAPI

from storage import store, Instance
from k8s_status import get_namespace_status

from routers.wordpress import router as wp_router
# Odoo-Router kommt später dazu: from routers.odoo import router as odoo_router


app = FastAPI(
    title="IHK-Projekt Backend",
    version="0.1.0",
)


# Router registrieren
app.include_router(wp_router, tags=["wordpress"])
# app.include_router(odoo_router, tags=["odoo"])  # später


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/instances", response_model=List[Instance])
async def list_all_instances():
    """
    Listet alle Instanzen (WordPress + später Odoo) mit aktualisiertem Status.
    """
    instances = store.list_instances()
    updated_instances: List[Instance] = []

    for inst in instances:
        status = get_namespace_status(inst.namespace)
        inst.status = status
        inst.updated_at = datetime.utcnow()
        store.update_instance(inst)
        updated_instances.append(inst)

    return updated_instances
