# services/email.py
from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Optional

import config
from audit import audit_event
from storage import Instance


def _build_wordpress_access_email(
    instance: Instance,
    to_address: str,
) -> EmailMessage:
    """
    Baut eine einfache Text-E-Mail mit den Zugangsdaten
    für eine WordPress-Instanz.
    """
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_address
    msg["Subject"] = f"Zugangsdaten für WordPress-Instanz {instance.domain}"

    url = f"https://{instance.domain}/wp-admin"

    body = (
        "Hallo,\n\n"
        "deine WordPress-Instanz wurde erfolgreich eingerichtet.\n\n"
        f"URL: {url}\n"
        "Benutzername: admin\n"
        "Passwort: wurde bei der Provisionierung gesetzt und "
        "wird separat übermittelt bzw. im Passwortmanager hinterlegt.\n\n"
        "Viele Grüße\n"
        "TrendTec Plattform\n"
    )

    msg.set_content(body)
    return msg


def _send_email(msg: EmailMessage) -> None:
    """
    Versendet die übergebene E-Mail über SMTP.
    """
    if config.SMTP_USE_TLS:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            if config.SMTP_USERNAME and config.SMTP_PASSWORD:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            if config.SMTP_USERNAME and config.SMTP_PASSWORD:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)


def send_wordpress_access_email(
    instance: Instance,
    to_address: Optional[str] = None,
) -> None:
    """
    Versendet eine E-Mail mit Zugangsdaten zur WordPress-Instanz.

    to_address:
        Zieladresse. Wenn None, wird config.ACCESS_DATA_EMAIL_TO verwendet.
        Ist keine Zieladresse konfiguriert, passiert nichts.
    """
    recipient = to_address or config.ACCESS_DATA_EMAIL_TO
    if not recipient:
        # Kein Empfänger konfiguriert → E-Mail-Feature derzeit „aus“
        return

    msg = _build_wordpress_access_email(instance, recipient)
    _send_email(msg)

    audit_event(
        "wordpress_access_email_sent",
        instance_id=instance.id,
        domain=instance.domain,
        to=recipient,
    )
