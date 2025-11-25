# backend/routers/odoo.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import verify_api_key
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.odoo import create_odoo_instance, delete_odoo_instance
from utils.commands import ScriptError
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
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def create_odoo_instance_endpoint(req: OdooCreateRequest) -> Instance:
    """
    Legt eine neue Odoo-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        return create_odoo_instance(store=store, slug=req.slug, domain=req.domain)

    except ValueError as exc:
        msg = str(exc)
        # Slug / Instanz-ID schon vergeben?
        if "already exists" in msg:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponse(
                    error="slug_already_exists",
                    detail=msg,
                ).model_dump(),
            )
        # Allgemeiner Validierungsfehler
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="invalid_request",
                detail=msg,
            ).model_dump(),
        )

    except ScriptError:
        raise http_500(
            "odoo_provisioning_failed",
            "Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
        )


@router.delete(
    "/{instance_id}",
    status_code=204,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def delete_odoo_instance_endpoint(instance_id: str) -> None:
    """
    Löscht eine Odoo-Instanz inkl. Namespace im Cluster.
    """
    # Instanz aus dem Store holen
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )

    try:
        # ⚠️ Wir gehen davon aus, dass services.odoo.delete_odoo_instance
        # dieselbe Signatur wie bei WordPress hat: (instance, store)
        delete_odoo_instance(instance=instance, store=store)
    except ScriptError:
        raise http_500(
            "odoo_delete_failed",
            f"Fehler beim Löschen der Odoo-Instanz '{instance_id}'. Details siehe Backend-Logs.",
        )

    return None
