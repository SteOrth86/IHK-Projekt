# backend/tests/test_run_script.py

import sys
from pathlib import Path

# Projekt-Root (backend-Ordner) auf sys.path legen
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import pytest

from utils.commands import run_script, ScriptError


def _make_script(tmp_path: Path, content: str, name: str = "script.sh") -> Path:
    """
    Hilfsfunktion: legt ein kleines Shell-Skript im tmp_path an
    und macht es ausführbar.
    """
    script_path = tmp_path / name
    script_path.write_text(content, encoding="utf-8")
    os.chmod(script_path, 0o755)
    return script_path


def test_run_script_success_returns_stdout(tmp_path):
    """
    Ein einfaches Skript, das etwas auf stdout schreibt und mit Exit-Code 0 endet,
    soll von run_script erfolgreich ausgeführt werden.
    """
    script = _make_script(
        tmp_path,
        "#!/usr/bin/env bash\n"
        "echo 'hello-from-script'\n",
        name="ok.sh",
    )

    out = run_script(script)

    # Newline am Ende ist ok – wir checken nur, dass der Text drin ist.
    assert "hello-from-script" in out


def test_run_script_nonzero_exit_raises_scripterror(tmp_path):
    """
    Ein Skript mit Exit-Code != 0 soll ScriptError werfen.
    stdout und stderr werden mitgegeben.
    """
    script = _make_script(
        tmp_path,
        "#!/usr/bin/env bash\n"
        "echo 'info-line'\n"
        "echo 'error-line' >&2\n"
        "exit 42\n",
        name="fail.sh",
    )

    with pytest.raises(ScriptError) as excinfo:
        run_script(script)

    err = excinfo.value
    assert err.returncode == 42
    assert err.timeout is False
    assert "info-line" in (err.stdout or "")
    assert "error-line" in (err.stderr or "")


def test_run_script_timeout_raises_scripterror_with_timeout_flag(tmp_path):
    """
    Wenn das Skript länger läuft als der gesetzte Timeout, soll ScriptError
    mit timeout=True und returncode=None geworfen werden.
    """
    script = _make_script(
        tmp_path,
        "#!/usr/bin/env bash\n"
        "sleep 2\n"
        "echo 'this-should-not-complete'\n",
        name="timeout.sh",
    )

    with pytest.raises(ScriptError) as excinfo:
        run_script(script, timeout=1)

    err = excinfo.value
    assert err.timeout is True
    # Beim Timeout haben wir keinen echten Exit-Code
    assert err.returncode is None
