# backend/routers/wordpress.py
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from auth import verify_api_key
from schemas.health import InstanceHealth
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.wordpress import (
    create_wordpress_instance,
    delete_wordpress_instance,
    check_wordpress_health,
    suspend_wordpress_instance,
    resume_wordpress_instance,
)
from utils.commands import ScriptError
from http_errors import http_404, http_500


router = APIRouter(
    prefix="/instances/wp",
    tags=["wordpress"],
)


SLUG_RE = re.compile(r"^[a-z0-9-]+$")

DOMAIN_RE = re.compile(
    r"^(?=.{3,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")

class WordPressCreateRequest(BaseModel):
    slug: str = Field(min_length=3, max_length=30)
    domain: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError("slug darf nur Buchstaben(a-z), Ziffern(0-9) und '-' enthalten")
        if v.startswith(("wp-", "odoo-")):
            raise ValueError("slug darf nicht mit 'wp-' oder 'odoo-' beginnen")
        if len(f"wp-{v}") > 63:
            raise ValueError("slug ist zu lang für den Kubernetes-Namespace (max. 63 Zeichen)")
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not DOMAIN_RE.match(v):
            raise ValueError("domain ist ungültig (z. B. 'kunde1.example.test')")
        return v

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
    except ValueError as exc:
        msg = str(exc)

        # Doppelter Slug / Instanz-ID oder bereits verwendete Domain → 409 Conflict
        if "already exists" in msg or "wird bereits von einer anderen Instanz verwendet" in msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "wp_conflict",
                    "detail": msg,
                },
            )

        # Sonstige ValueError aus dem Service → 400 Bad Request
        raise HTTPException(
            status_code=400,
            detail={
                "error": "wp_invalid_request",
                "detail": msg,
            },
        )

    except ScriptError:
        # Skript-/Kubernetes-Fehler → 500
        raise http_500(
            "wp_provisioning_failed",
            "Fehler bei der WordPress-Provisionierung. Details siehe Backend-Logs.",
        )
    except Exception:
        # Fallback für wirklich unerwartete Fehler
        raise http_500(
            "wp_unexpected_error",
            "Unerwarteter Fehler bei der WordPress-Provisionierung.",
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
    Löscht eine WordPress-Instanz inkl. Namespace im Cluster.
    """
    # Instanz aus dem Store holen
    instance = store.get(instance_id)
    if instance is None:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    # Service korrekt aufrufen: instance + store (nicht instance_id=)
    try:
        delete_wordpress_instance(instance=instance, store=store)
    except ScriptError:
        raise http_500(
            "wp_delete_failed",
            f"Fehler beim Löschen der WordPress-Instanz '{instance_id}'. Details siehe Backend-Logs.",
        )

    # 204 No Content → kein Body
    return None

@router.get("/{instance_id}/health", response_model=InstanceHealth)
def get_wordpress_instance_health(
    instance_id: str,
    api_key: None = Depends(verify_api_key),
):
    """
    Health-/Smoke-Check für eine einzelne WordPress-Instanz.

    - nutzt die Domain der Instanz (instance.domain)
    - ruft https://<domain>/wp-login.php auf
    - gibt "ok" bei HTTP 200/302, sonst "error" zurück
    """
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
    """
    Sperrt eine bestehende WordPress-Instanz (setzt suspended + optionalen Grund).
    """
    # Instanz aus dem Store holen
    instance = store.get(instance_id)
    if instance is None:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )

    reason = body.reason if body is not None else None

    # WordPress-spezifischen Admin-Service aufrufen
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
    """
    Hebt die Sperre einer WordPress-Instanz auf (setzt suspended zurück).
    """
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
