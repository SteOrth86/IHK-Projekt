# schemas/errors.py
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    # Optional für Debugging – kannst du bei Bedarf weglassen
    stdout: str | None = None
    stderr: str | None = None
