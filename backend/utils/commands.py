# backend/utils/commands.py
from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Union


class ScriptError(RuntimeError):
    """
    Wird geworfen, wenn ein Provisionierungs- oder Delete-Skript fehlschlägt.
    Enthält zusätzlich stdout/stderr und den Rückgabecode.
    """

    def __init__(self, script: str, returncode: int, stdout: str, stderr: str) -> None:
        msg = f"Script {script!r} failed with exit code {returncode}"
        super().__init__(msg)
        self.script = script
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_script(script_path: Union[str, Path], *args: str) -> CompletedProcess[str]:
    """
    Führt ein Shell-Skript aus.

    - script_path: Pfad zum Skript (z. B. config.WP_PROVISION_SCRIPT)
    - *args: zusätzliche Argumente für das Skript

    Rückgabe:
        CompletedProcess-Objekt mit stdout/stderr als Text.

    Verhalten:
        - Bei returncode != 0 wird ScriptError geworfen.
    """
    script = str(script_path)

    proc = run([script, *args], capture_output=True, text=True)

    if proc.returncode != 0:
        raise ScriptError(script, proc.returncode, proc.stdout, proc.stderr)

    return proc
