# main.py
from datetime import datetime
from pathlib import Path

import subprocess
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from config import WP_PROVISION_SCRIPT, WP_DELETE_SCRIPT, INSTANCES_FILE
from storage import InstanceStore, Instance
from k8s_status import get_namespace_status
from auth import verify_api_key

# FastAPI-App
app = FastAPI(title="IHK-Projekt Backend – Provisionierung")

# Globale Instanz des Stores
store = InstanceStore(INSTANCES_FILE)

# ---------- Request/Response-Modelle ----------

class CreateWpRequest(BaseModel):
    slug: str   # z.B. "demo1"
    domain: str # z.B. "demo1.local"


class DeleteResponse(BaseModel):
    message: str


# ---------- Hilfsfunktionen ----------

def run_script(script_path: Path, args: list[str]) -> None:

    # 1. Existiert das Skript?
    if not script_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Script not found: {script_path}",
        )

    # 2. Skript ausführen (über bash)
    result = subprocess.run(
        ["bash", str(script_path)] + args,
        capture_output=True,
        text=True,
    )

    # 3. Rückgabecode prüfen
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        msg = stderr or stdout or "unknown error"
        raise HTTPException(
            status_code=500,
            detail=f"Script failed ({script_path.name}): {msg}",
        )



# ---------- Basis-Endpunkte ----------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------- WordPress-Endpunkte ----------

@app.post(
    "/instances/wp",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
)
async def create_wp_instance(req: CreateWpRequest):
    """
    Legt eine neue WordPress-Instanz an:
    - ruft provision_wp.sh auf
    - legt einen Eintrag in instances.json an
    """
    instance_id = f"wp-{req.slug}"
    namespace = instance_id  # wir nehmen an, dein Skript benutzt denselben Namespace

    # Prüfen, ob es die Instanz schon gibt
    if store.get_instance(instance_id) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Instance '{instance_id}' already exists.",
        )

    # Skript ausführen (z.B. ./provision_wp.sh demo1 demo1.local)
    run_script(WP_PROVISION_SCRIPT, [req.slug, req.domain])

    now = datetime.utcnow()
    instance = Instance(
        id=instance_id,
        type="wordpress",
        namespace=namespace,
        domain=req.domain,
        created_at=now,
        updated_at=now,
        status="creating",
    )

    store.add_instance(instance)
    return instance


@app.delete(
    "/instances/wp/{slug}",
    response_model=DeleteResponse,
    dependencies=[Depends(verify_api_key)],
)
async def delete_wp_instance(slug: str):
    """
    Löscht eine WordPress-Instanz:
    - ruft delete_wp.sh auf
    - entfernt Eintrag aus instances.json
    """
    instance_id = f"wp-{slug}"

    # Skript ausführen
    run_script(WP_DELETE_SCRIPT, [slug])

    # Aus JSON entfernen
    removed = store.remove_instance(instance_id)
    if not removed:
        # Instanz war in der JSON nicht drin (z.B. inkonsistenter Zustand)
        # Wir melden trotzdem Erfolg, damit API aus Sicht des Clients „idempotent“ ist
        return DeleteResponse(message=f"Instance '{instance_id}' deleted (not in JSON).")

    return DeleteResponse(message=f"Instance '{instance_id}' deleted.")


@app.get("/instances/wp", response_model=List[Instance])
async def list_wp_instances():
    """
    Listet alle WordPress-Instanzen und aktualisiert vorher den Status via kubectl.
    """
    instances = store.list_instances(type_filter="wordpress")
    updated_instances: List[Instance] = []

    for inst in instances:
        status = get_namespace_status(inst.namespace)
        inst.status = status
        inst.updated_at = datetime.utcnow()
        store.update_instance(inst)
        updated_instances.append(inst)

    return updated_instances


@app.get("/instances/wp/{slug}", response_model=Instance)
async def get_wp_instance(slug: str):
    """
    Holt eine einzelne WordPress-Instanz + Status.
    """
    instance_id = f"wp-{slug}"
    inst = store.get_instance(instance_id)
    if inst is None:
        raise HTTPException(status_code=404, detail="Instance not found.")

    inst.status = get_namespace_status(inst.namespace)
    inst.updated_at = datetime.utcnow()
    store.update_instance(inst)
    return inst


# ---------- Generische Endpunkte (Vorbereitung für Odoo) ----------

@app.get("/instances", response_model=List[Instance])
async def list_all_instances():
    """
    Listet alle Instanzen (WordPress + später Odoo, etc.).
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
