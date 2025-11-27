# tests/test_audit.py

import logging
import pathlib
import sys

# Sicherstellen, dass der Projekt-Root (backend-Ordner) im sys.path ist
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kube_app_provisioner.common.audit import audit_event


def test_audit_event_creates_log_entry(caplog):
    logger = logging.getLogger("kube_app_provisioner.audit")

    with caplog.at_level(logging.INFO, logger=logger.name):
        audit_event(
            "test_action",
            instance_id="inst-123",
            suspended_before=False,
            suspended_after=True,
        )

    records = [r for r in caplog.records if r.name == logger.name]
    assert records

    msg = records[0].getMessage()
    assert "AUDIT" in msg
    assert "test_action" in msg
    assert "inst-123" in msg
