from typing import Optional

from fastapi import Header, HTTPException, status

from kube_app_provisioner.config import API_KEY


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)):
    """
    Einfache API-Key Auth:
    - Wenn kein BACKEND_API_KEY in der Umgebung gesetzt ist, ist Auth deaktiviert.
    - Wenn BACKEND_API_KEY gesetzt ist, muss der Header X-API-Key übereinstimmen.
    """
    # Auth ausgeschaltet, wenn kein API_KEY konfiguriert ist
    if API_KEY is None:
        return

    # API-Key prüfen
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
