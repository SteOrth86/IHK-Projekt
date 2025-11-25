# backend/routers/wordpress.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import verify_api_key
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.wordpress import create_wordpress_instance, delete_wordpress_instance
from utils.commands import ScriptError
from http_errors import http_404, http_500


router = APIRouter(
    prefix="/instances/wp",
    tags=["wordpress"],
)


class WordPressCreateRequest(BaseModel):
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
def create_wp_instance(req: WordPressCreateRequest) -> Instance:
    """
    Legt eine neue WordPress-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        # Service aufrufen – hier steckt auch dein Duplicate-Check drin
        return create_wordpress_instance(store=store, slug=req.slug, domain=req.domain)

    except ValueError as exc:
        # Validierungs-/Businessfehler aus dem Service (z. B. slug leer oder already exists)
        msg = str(exc)

        # Slug/Instanz-ID bereits vergeben → 409 Conflict
        if "already exists" in msg:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponse(
                    error="slug_already_exists",
                    detail=msg,
                ).model_dump(),
            )

        # allgemeiner ValueError → 400 Bad Request
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="invalid_request",
                detail=msg,
            ).model_dump(),
        )

    except ScriptError:
        # Skript-/Helm-/kubectl-Fehler → wie bisher 500 mit wp_provisioning_failed
        raise http_500(
            "wp_provisioning_failed",
            "Fehler bei der WordPress-Provisionierung. Details siehe Backend-Logs.",
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
