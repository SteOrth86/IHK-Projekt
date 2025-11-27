from fastapi import HTTPException

from kube_app_provisioner.schemas.errors import ErrorResponse
from kube_app_provisioner.services.base_instance_service import UnsupportedOperationError
from kube_app_provisioner.utils.commands import ScriptError


def http_404(error: str, detail: str) -> HTTPException:
    """
    Erzeugt eine einheitliche 404-Fehlermeldung im ErrorResponse-Format.
    """
    return HTTPException(
        status_code=404,
        detail=ErrorResponse(error=error, detail=detail).model_dump(),
    )


def http_500(error: str, detail: str) -> HTTPException:
    """
    Erzeugt eine einheitliche 500-Fehlermeldung im ErrorResponse-Format.
    """
    return HTTPException(
        status_code=500,
        detail=ErrorResponse(error=error, detail=detail).model_dump(),
    )


def map_service_error(
    exc: Exception,
    *,
    conflict_error: str,
    conflict_detail: str,
    invalid_error: str,
    invalid_detail: str,
    provisioning_error: str,
    provisioning_detail: str,
    unexpected_error: str,
    unexpected_detail: str,
    not_supported_error: str | None = None,
    not_supported_detail: str | None = None,
) -> HTTPException:
    """
    Vereinheitlichtes Error-Mapping fuer Router: ValueError -> 400/409,
    ScriptError -> 500 (provisioning), nicht unterstützte Operation -> 501,
    Rest -> 500 (unexpected).
    """
    if isinstance(exc, UnsupportedOperationError) and not_supported_error:
        return HTTPException(
            status_code=501,
            detail={
                "error": not_supported_error,
                "detail": not_supported_detail or str(exc),
            },
        )

    if isinstance(exc, ValueError):
        msg = str(exc)
        if "already exists" in msg or "wird bereits von einer anderen Instanz verwendet" in msg:
            return HTTPException(
                status_code=409,
                detail={
                    "error": conflict_error,
                    "detail": msg or conflict_detail,
                },
            )
        return HTTPException(
            status_code=400,
            detail={
                "error": invalid_error,
                "detail": msg or invalid_detail,
            },
        )

    if isinstance(exc, ScriptError):
        return http_500(provisioning_error, provisioning_detail)

    return http_500(unexpected_error, unexpected_detail)
