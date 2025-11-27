# request_id.py
from __future__ import annotations

import contextvars
from typing import Optional

# ContextVar, in dem pro Request die request_id gespeichert wird.
# Default ist None, damit Hintergrundjobs / Skripte nicht crashen.
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> Optional[str]:
    """
    Hilfsfunktion, um die aktuelle request_id zu holen.
    Gibt None zurück, wenn kein Request-Kontext existiert.
    """
    return request_id_var.get()
