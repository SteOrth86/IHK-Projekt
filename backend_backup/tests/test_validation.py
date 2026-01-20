# backend/tests/test_validation.py

import sys
from pathlib import Path

# Projekt-Root (backend-Ordner) auf sys.path legen,
# damit "from routers.wordpress ..." funktioniert.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from pydantic import ValidationError

from routers.wordpress import WordPressCreateRequest
from routers.odoo import OdooCreateRequest


# -------------------------
# WordPress Validation
# -------------------------

def test_wp_slug_is_normalized_to_lowercase():
    req = WordPressCreateRequest(
        slug="KundeApp-01",
        domain="kunde-valid.example.test",
    )
    assert req.slug == "kundeapp-01"


def test_wp_slug_rejects_invalid_characters():
    with pytest.raises(ValidationError):
        WordPressCreateRequest(
            slug="kunde!!!",
            domain="kunde-valid.example.test",
        )


def test_wp_slug_rejects_reserved_prefixes():
    # darf nicht mit "wp-" beginnen
    with pytest.raises(ValidationError):
        WordPressCreateRequest(
            slug="wp-testslug",
            domain="kunde-valid.example.test",
        )
    # darf auch nicht mit "odoo-" beginnen
    with pytest.raises(ValidationError):
        WordPressCreateRequest(
            slug="odoo-testslug",
            domain="kunde-valid.example.test",
        )


def test_wp_domain_must_be_valid_hostname():
    # ungültige Domain -> ValidationError
    with pytest.raises(ValidationError):
        WordPressCreateRequest(
            slug="kunde-valid",
            domain="nur-kunde",  # keine TLD, kein Punkt
        )


# -------------------------
# Odoo Validation
# -------------------------

def test_odoo_slug_is_normalized_to_lowercase():
    req = OdooCreateRequest(
        slug="OdooApp-01",
        domain="odoo-valid.example.test",
    )
    # nur lowercase, kein verbotener Präfix wie "odoo-" oder "wp-"
    assert req.slug == "odooapp-01"


def test_odoo_slug_rejects_invalid_characters():
    with pytest.raises(ValidationError):
        OdooCreateRequest(
            slug="odoo slug mit space",
            domain="odoo-valid.example.test",
        )


def test_odoo_slug_rejects_reserved_prefixes():
    with pytest.raises(ValidationError):
        OdooCreateRequest(
            slug="wp-irgendwas",
            domain="odoo-valid.example.test",
        )
    with pytest.raises(ValidationError):
        OdooCreateRequest(
            slug="odoo-irgendwas",
            domain="odoo-valid.example.test",
        )


def test_odoo_domain_must_be_valid_hostname():
    with pytest.raises(ValidationError):
        OdooCreateRequest(
            slug="odoo-valid",
            domain="odoo@test",  # ungültig wegen @
        )
