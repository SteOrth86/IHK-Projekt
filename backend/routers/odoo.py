from datetime import datetime
from pathlib import Path
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from config import ODOO_PROVISION_SCRIPT, ODOO_DELETE_SCRIPT
from storage import store, Instance
from k8s_status import get_namespace_status
from auth import verify_api_key

router = APIRouter()


class CreateOdooRequest(BaseModel):
    slug: str   # z.B. "kunde1"
    domain: str # z.B. "kunde1.odoo.local"


class DeleteResponse(BaseModel):
    message: str


def run_script(script_path: Path, args: list[str]) -> None:
    """
    Führt ein Shell-Skript aus und wirft eine saubere HTTP-Fehlermeldung,
    wenn etwas schiefgeht.
    """
    if not script_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Script not found: {script_path}",
        )

    result = subprocess.run(
        ["bash", str(script_path)] + args,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        msg = stderr or stdout or "unknown error"
        raise HTTPException(
            status_code=500,
            detail=f"Script failed ({script_path.name}): {msg}",
        )


@router.post(
    "/instances/odoo",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
)
async def create_odoo_instance(req: CreateOdooRequest):
    """
    Legt eine neue Odoo-Instanz an (architektonische Vorbereitung):
    - ruft provision_odoo.sh auf (aktuell Stub)
    - legt einen Eintrag in instances.json mit type="odoo" an
    """
    instance_id = f"odoo-{req.slug}"
    namespace = instance_id

    # Prüfen, ob Instanz schon existiert
    if store.get_instance(instance_id) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Instance '{instance_id}' already exists.",
        )

    # Skript ausführen (STUB -> bricht aktuell mit exit 1 ab)
    run_script(ODOO_PROVISION_SCRIPT, [req.slug, req.domain])

    now = datetime.utcnow()
    instance = Instance(
        id=instance_id,
        type="odoo",
        namespace=namespace,
        domain=req.domain,
        created_at=now,
        updated_at=now,
        status="creating",
    )
    store.add_instance(instance)
    return instance


@router.delete(
    "/instances/odoo/{slug}",
    response_model=DeleteResponse,
    dependencies=[Depends(verify_api_key)],
)
async def delete_odoo_instance(slug: str):
    """
    Löscht eine Odoo-Instanz.
    """
    instance_id = f"odoo-{slug}"

    run_script(ODOO_DELETE_SCRIPT, [slug])

    removed = store.remove_instance(instance_id)
    if not removed:
        return DeleteResponse(message=f"Instance '{instance_id}' deleted (not in JSON).")

    return DeleteResponse(message=f"Instance '{instance_id}' deleted.")


@router.get("/instances/odoo", response_model=List[Instance])
async def list_odoo_instances():
    """
    Listet alle Odoo-Instanzen und aktualisiert den Status via kubectl.
    """
    instances = store.list_instances(type_filter="odoo")
    updated_instances: List[Instance] = []

    for inst in instances:
        status = get_namespace_status(inst.namespace)
        inst.status = status
        inst.updated_at = datetime.utcnow()
        store.update_instance(inst)
        updated_instances.append(inst)

    return updated_instances


@router.get("/instances/odoo/{slug}", response_model=Instance)
async def get_odoo_instance(slug: str):
    """
    Holt eine einzelne Odoo-Instanz + Status.
    """
    instance_id = f"odoo-{slug}"
    inst = store.get_instance(instance_id)
    if inst is None:
        raise HTTPException(status_code=404, detail="Instance not found.")

    inst.status = get_namespace_status(inst.namespace)
    inst.updated_at = datetime.utcnow()
    store.update_instance(inst)
    return inst
