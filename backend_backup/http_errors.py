from fastapi import HTTPException
from schemas.errors import ErrorResponse


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
