# backend/routers/odoo.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from kube_app_provisioner.auth import verify_api_key
from kube_app_provisioner.common.http_errors import http_404, http_500, map_service_error
from kube_app_provisioner.schemas.errors import ErrorResponse
from kube_app_provisioner.common.validators import validate_domain, validate_slug
from kube_app_provisioner.services.apps.odoo import (
    create_odoo_instance as create_odoo_service,
    delete_odoo_instance as delete_odoo_service,
    resume_odoo_instance,
    suspend_odoo_instance,
)
from kube_app_provisioner.core.storage import Instance, store


router = APIRouter(prefix="/instances/odoo", tags=["odoo"])


class OdooCreateRequest(BaseModel):
    slug: str = Field(min_length=3, max_length=30)
    domain: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return validate_slug(v, prefix="odoo-")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return validate_domain(v)


class SuspendRequest(BaseModel):
    reason: Optional[str] = None


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
    try:
        return create_odoo_service(store=store, slug=req.slug, domain=req.domain)

    except Exception as exc:
        raise map_service_error(
            exc,
            conflict_error="odoo_conflict",
            conflict_detail="Instance exists or Domain in use",
            invalid_error="odoo_invalid_request",
            invalid_detail="Ungueltige Anfrage",
            provisioning_error="odoo_provisioning_failed",
            provisioning_detail="Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
            unexpected_error="odoo_unexpected_error",
            unexpected_detail="Unerwarteter Fehler bei der Odoo-Provisionierung.",
            not_supported_error="odoo_not_supported",
            not_supported_detail="Operation fuer Odoo nicht konfiguriert",
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
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )

    try:
        delete_odoo_service(instance=instance, store=store)
    except Exception as exc:
        raise map_service_error(
            exc,
            conflict_error="odoo_conflict",
            conflict_detail="Instance exists or Domain in use",
            invalid_error="odoo_invalid_request",
            invalid_detail="Ungueltige Anfrage",
            provisioning_error="odoo_delete_failed",
            provisioning_detail=f"Fehler beim Loeschen der Odoo-Instanz '{instance_id}'. Details siehe Backend-Logs.",
            unexpected_error="odoo_unexpected_error",
            unexpected_detail="Unerwarteter Fehler beim Loeschen der Odoo-Instanz.",
            not_supported_error="odoo_not_supported",
            not_supported_detail="Operation fuer Odoo nicht konfiguriert",
        )


@router.post(
    "/{instance_id}/suspend",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {"model": ErrorResponse},
        501: {"model": ErrorResponse},
    },
)
def suspend_odoo(instance_id: str, body: SuspendRequest | None = None) -> Instance:
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )

    reason = body.reason if body is not None else None

    try:
        return suspend_odoo_instance(
            instance=instance,
            store=store,
            reason=reason,
        )
    except Exception as exc:
        raise map_service_error(
            exc,
            conflict_error="odoo_conflict",
            conflict_detail="Instance exists or Domain in use",
            invalid_error="odoo_invalid_request",
            invalid_detail="Ungueltige Anfrage",
            provisioning_error="odoo_provisioning_failed",
            provisioning_detail="Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
            unexpected_error="odoo_unexpected_error",
            unexpected_detail="Unerwarteter Fehler bei der Odoo-Provisionierung.",
            not_supported_error="odoo_not_supported",
            not_supported_detail="Suspend fuer Odoo nicht konfiguriert",
        )


@router.post(
    "/{instance_id}/resume",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {"model": ErrorResponse},
        501: {"model": ErrorResponse},
    },
)
def resume_odoo(instance_id: str) -> Instance:
    instance = store.get(instance_id)
    if instance is None or instance.type != "odoo":
        raise http_404(
            "instance_not_found",
            f"Odoo-Instanz '{instance_id}' existiert nicht.",
        )

    try:
        return resume_odoo_instance(
            instance=instance,
            store=store,
        )
    except Exception as exc:
        raise map_service_error(
            exc,
            conflict_error="odoo_conflict",
            conflict_detail="Instance exists or Domain in use",
            invalid_error="odoo_invalid_request",
            invalid_detail="Ungueltige Anfrage",
            provisioning_error="odoo_provisioning_failed",
            provisioning_detail="Fehler bei der Odoo-Provisionierung. Details siehe Backend-Logs.",
            unexpected_error="odoo_unexpected_error",
            unexpected_detail="Unerwarteter Fehler bei der Odoo-Provisionierung.",
            not_supported_error="odoo_not_supported",
            not_supported_detail="Resume fuer Odoo nicht konfiguriert",
        )
