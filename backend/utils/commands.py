# backend/utils/commands.py
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


logger = logging.getLogger(__name__)


@dataclass
class ScriptError(Exception):
    """
    Fehler beim Aufruf eines Shell-Skripts.

    Attributes:
        cmd: Liste der aufgerufenen Kommando-/Argument-Strings.
        returncode: Exit-Code des Prozesses (None, wenn Timeout).
        stdout: Standard-Ausgabe des Skripts (falls vorhanden).
        stderr: Fehler-Ausgabe des Skripts (falls vorhanden).
        timeout: True, wenn der Prozess per Timeout abgebrochen wurde.
    """
    cmd: list[str]
    returncode: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    timeout: bool = False

    def __str__(self) -> str:
        base = f"ScriptError(cmd={self.cmd!r}, returncode={self.returncode}, timeout={self.timeout})"
        if self.stderr:
            return base + f" stderr={self.stderr!r}"
        return base


def run_script(script_path: Path | str, *args: str, timeout: int = 120) -> str:
    """
    Führt ein Shell-Skript aus.

    - script_path: Pfad zum Skript (Path oder str).
    - *args: Argumente für das Skript (werden nicht durch die Shell geparst).
    - timeout: Timeout in Sekunden (Standard: 120).

    Rückgabe:
        stdout (als String) bei Erfolg.

    Raises:
        ScriptError: wenn Exit-Code != 0 oder Timeout erreicht ist.
    """
    script_str = str(script_path)
    cmd: list[str] = [script_str, *[str(a) for a in args]]

    logger.info("Starte Skript: %s", cmd)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("Skript-Timeout nach %s Sekunden: %s", timeout, cmd)
        raise ScriptError(
            cmd=cmd,
            returncode=None,
            stdout=exc.stdout,
            stderr=exc.stderr,
            timeout=True,
        ) from exc
    except OSError as exc:
        # z. B. Skript nicht ausführbar oder nicht gefunden
        logger.exception("Fehler beim Starten des Skripts: %s", cmd)
        raise ScriptError(
            cmd=cmd,
            returncode=None,
            stdout=None,
            stderr=str(exc),
            timeout=False,
        ) from exc

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    if proc.returncode != 0:
        logger.error(
            "Skript fehlgeschlagen: %s (returncode=%s)\nSTDOUT:\n%s\nSTDERR:\n%s",
            cmd,
            proc.returncode,
            stdout,
            stderr,
        )
        raise ScriptError(
            cmd=cmd,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            timeout=False,
        )

    if stdout:
        logger.info("Skript erfolgreich: %s\nSTDOUT:\n%s", cmd, stdout)
    else:
        logger.info("Skript erfolgreich (keine Ausgabe): %s", cmd)

    return stdout
