# backend/routers/wordpress.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from kube_app_provisioner.auth import verify_api_key
from kube_app_provisioner.http_errors import http_404, http_500, map_service_error
from kube_app_provisioner.schemas.errors import ErrorResponse
from kube_app_provisioner.schemas.health import InstanceHealth
from kube_app_provisioner.schemas.validators import validate_domain, validate_slug
from kube_app_provisioner.services.wordpress import (
    check_wordpress_health,
    create_wordpress_instance,
    delete_wordpress_instance,
    resume_wordpress_instance,
    suspend_wordpress_instance,
)
from kube_app_provisioner.storage import Instance, store


router = APIRouter(prefix="/instances/wp", tags=["wordpress"])


class WordPressCreateRequest(BaseModel):
    slug: str = Field(min_length=3, max_length=30)
    domain: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return validate_slug(v, prefix="wp-")

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
def create_wp_instance(req: WordPressCreateRequest) -> Instance:
    """
    Legt eine neue WordPress-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        return create_wordpress_instance(store=store, slug=req.slug, domain=req.domain)
    except Exception as exc:
        raise map_service_error(
            exc,
            conflict_error="wp_conflict",
            conflict_detail="Instance exists or Domain in use",
            invalid_error="wp_invalid_request",
            invalid_detail="Ungueltige Anfrage",
            provisioning_error="wp_provisioning_failed",
            provisioning_detail="Fehler bei der WordPress-Provisionierung. Details siehe Backend-Logs.",
            unexpected_error="wp_unexpected_error",
            unexpected_detail="Unerwarteter Fehler bei der WordPress-Provisionierung.",
            not_supported_error="wp_not_supported",
            not_supported_detail="Operation fuer WordPress nicht konfiguriert",
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
def delete_wp_instance(instance_id: str) -> None:
    """
    Loescht eine WordPress-Instanz inkl. Namespace im Cluster.
    """
    instance = store.get(instance_id)
    if instance is None:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    try:
        delete_wordpress_instance(instance=instance, store=store)
    except ScriptError:
        raise http_500(
            "wp_delete_failed",
            f"Fehler beim Loeschen der WordPress-Instanz '{instance_id}'. Details siehe Backend-Logs.",
        )

    return None


@router.get("/{instance_id}/health", response_model=InstanceHealth)
def get_wordpress_instance_health(
    instance_id: str,
    api_key: None = Depends(verify_api_key),
):
    instance = store.get(instance_id)

    if instance is None or instance.type != "wordpress":
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    return check_wordpress_health(instance)


@router.post(
    "/{instance_id}/suspend",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {"model": ErrorResponse},
    },
)
def suspend_wp_instance(instance_id: str, body: SuspendRequest | None = None) -> Instance:
    instance = store.get(instance_id)
    if instance is None:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    reason = body.reason if body is not None else None

    updated = suspend_wordpress_instance(
        instance=instance,
        store=store,
        reason=reason,
    )

    return updated


@router.post(
    "/{instance_id}/resume",
    response_model=Instance,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {"model": ErrorResponse},
    },
)
def resume_wp_instance(instance_id: str) -> Instance:
    instance = store.get(instance_id)
    if instance is None:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    updated = resume_wordpress_instance(
        instance=instance,
        store=store,
    )

    return updated
