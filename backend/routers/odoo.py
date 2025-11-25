# backend/routers/odoo.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import verify_api_key
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.odoo import create_odoo_instance, delete_odoo_instance
from http_errors import http_404, http_500


router = APIRouter(
    prefix="/instances/odoo",
    tags=["odoo"],
)


class OdooCreateRequest(BaseModel):
    slug: str
    domain: str


@router.post(
    "",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
    responses={500: {"model": ErrorResponse}},
)
def create_odoo(req: OdooCreateRequest) -> Instance:
    """
    Legt eine neue Odoo-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        return create_odoo_instance(store=store, slug=req.slug, domain=req.domain)
    except Exception:
        # Hinweis für die Doku:
        # Hier scheitert es aktuell z.B. an fehlenden Bitnami-Odoo-Images (ImagePullBackOff).
        raise http_500(
            "odoo_provisioning_failed",
            "Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
        )
@router.delete(
    "/{instance_id}",
    status_code=204,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
)
def delete_odoo(instance_id: str) -> None:
    """
    Löscht eine Odoo-Instanz inkl. Namespace im Cluster.
    """
    try:
        delete_odoo_instance(store=store, instance_id=instance_id)
    except KeyError:
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )
