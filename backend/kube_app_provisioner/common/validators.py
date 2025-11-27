from __future__ import annotations

import re

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
DOMAIN_RE = re.compile(r"^(?=.{3,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")


def validate_slug(value: str, prefix: str) -> str:
    """
    Normalisiert und validiert einen Slug fuer Instanzen.
    """
    v = value.strip().lower()
    if not SLUG_RE.match(v):
        raise ValueError("slug darf nur Kleinbuchstaben, Ziffern und '-' enthalten")
    if v.startswith(("wp-", "odoo-")):
        raise ValueError("slug darf nicht mit 'wp-' oder 'odoo-' beginnen")
    if len(f"{prefix}{v}") > 63:
        raise ValueError("slug ist zu lang fuer den Kubernetes-Namespace (max. 63 Zeichen)")
    return v


def validate_domain(value: str) -> str:
    v = value.strip().lower()
    if not DOMAIN_RE.match(v):
        raise ValueError("domain ist ungueltig (z. B. 'kunde1.example.test')")
    return v
