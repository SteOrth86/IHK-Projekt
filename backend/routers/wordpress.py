# backend/routers/wordpress.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import verify_api_key
from schemas.errors import ErrorResponse
from storage import Instance, store
from services.wordpress import create_wordpress_instance, delete_wordpress_instance
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
    responses={500: {"model": ErrorResponse}},
)
def create_wp_instance(req: WordPressCreateRequest) -> Instance:
    """
    Legt eine neue WordPress-Instanz an (Service-Layer + Provisionierungs-Skript).
    """
    try:
        return create_wordpress_instance(store=store, slug=req.slug, domain=req.domain)
    except Exception:
        # Für die Doku: hier könntest du später ScriptError/StoreError unterscheiden
        raise http_500(
            "wp_provisioning_failed",
            "Fehler bei der WordPress-Provisionierung. Details siehe Backend-Logs.",
        )
@router.delete(
    "/{instance_id}",
    status_code=204,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
)
def delete_wp_instance(instance_id: str) -> None:
    """
    Löscht eine WordPress-Instanz inkl. Namespace im Cluster.
    """
    try:
        delete_wordpress_instance(store=store, instance_id=instance_id)
    except KeyError:
        raise http_404(
            "instance_not_found",
            f"WordPress-Instanz '{instance_id}' existiert nicht.",
        )
