# backend/routers/odoo.py
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from auth import verify_api_key
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.odoo import (
    create_odoo_instance as create_odoo_service,
    delete_odoo_instance as delete_odoo_service,
)
from utils.commands import ScriptError
from http_errors import http_404, http_500


router = APIRouter(
    prefix="/instances/odoo",
    tags=["odoo"],
)

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

DOMAIN_RE = re.compile(
    r"^(?=.{3,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$"
)


class OdooCreateRequest(BaseModel):
    slug: str = Field(min_length=3, max_length=30)
    domain: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError("slug darf nur Kleinbuchstaben, Ziffern und '-' enthalten")
        if v.startswith(("wp-", "odoo-")):
            raise ValueError("slug darf nicht mit 'wp-' oder 'odoo-' beginnen")
        if len(f"odoo-{v}") > 63:
            raise ValueError("slug ist zu lang für den Kubernetes-Namespace (max. 63 Zeichen)")
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not DOMAIN_RE.match(v):
            raise ValueError("domain ist ungültig (z. B. 'kunde1.example.test')")
        return v


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
def create_odoo_instance(req: OdooCreateRequest) -> Instance:
    """
    Legt eine neue Odoo-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        return create_odoo_service(store=store, slug=req.slug, domain=req.domain)

    except ValueError as exc:
        msg = str(exc)

        # Doppelter Slug / Instanz-ID oder bereits verwendete Domain → 409 Conflict
        if "already exists" in msg or "wird bereits von einer anderen Instanz verwendet" in msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "odoo_conflict",
                    "detail": msg,
                },
            )

        # Sonstige ValueError aus dem Service → 400 Bad Request
        raise HTTPException(
            status_code=400,
            detail={
                "error": "odoo_invalid_request",
                "detail": msg,
            },
        )

    except ScriptError:
        # Skript-/Kubernetes-Fehler → 500
        raise http_500(
            "odoo_provisioning_failed",
            "Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
        )
    except Exception:
        # Fallback für wirklich unerwartete Fehler
        raise http_500(
            "odoo_unexpected_error",
            "Unerwarteter Fehler bei der Odoo-Provisionierung.",
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
def delete_odoo_instance(instance_id: str) -> None:
    """
    Löscht eine Odoo-Instanz inkl. Namespace im Cluster.
    """
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )

    try:
        delete_odoo_service(instance=instance, store=store)
    except ScriptError:
        raise http_500(
            "odoo_delete_failed",
            f"Fehler beim Löschen der Odoo-Instanz '{instance_id}'. Details siehe Backend-Logs.",
        )
