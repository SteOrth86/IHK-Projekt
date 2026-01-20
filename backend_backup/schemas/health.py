# backend/schemas/health.py
from pydantic import BaseModel


class InstanceHealth(BaseModel):
    status: str                 # "ok" oder "error"
    http_status: int | None = None
    detail: str | None = None
