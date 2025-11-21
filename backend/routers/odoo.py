# backend/routers/odoo.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import verify_api_key
from storage import store, Instance
from services.odoo import (
    create_odoo_instance,
    delete_odoo_instance,
)
from schemas.errors import ErrorResponse
from utils.commands import ScriptError

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
    responses={
        400: {"model": ErrorResponse, "description": "Ungültige Eingabe"},
        500: {"model": ErrorResponse, "description": "Skript- oder Clusterfehler"},
    },
)
def create_odoo(
    payload: OdooCreateRequest,
    api_key: str = Depends(verify_api_key),
) -> Instance:
    """
    Legt eine neue Odoo-Instanz an und startet das Provisionierungs-Skript.
    """
    try:
        instance = create_odoo_instance(
            slug=payload.slug,
            domain=payload.domain,
            store=store,
        )
        return instance

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_input",
                "detail": str(exc),
            },
        )

    except ScriptError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "odoo_provisioning_failed",
                "detail": str(exc),
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
        )


@router.delete(
    "/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Instanz nicht gefunden"},
        500: {"model": ErrorResponse, "description": "Skript- oder Clusterfehler"},
    },
)
def delete_odoo(
    instance_id: str,
    api_key: str = Depends(verify_api_key),
) -> None:
    """
    Löscht eine bestehende Odoo-Instanz über das Delete-Skript.
    """
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "instance_not_found",
                "detail": f"Odoo-Instanz {instance_id!r} existiert nicht.",
            },
        )

    try:
        delete_odoo_instance(instance, store=store)

    except ScriptError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "odoo_delete_failed",
                "detail": str(exc),
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
        )
