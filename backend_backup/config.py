from pathlib import Path
import os

# Ordner, in dem sich das Backend befindet: ~/ihk-projekt/backend
BASE_DIR = Path(__file__).resolve().parent

# Projekt-Root: ~/ihk-projekt
PROJECT_ROOT = BASE_DIR.parent

# Skript-Ordner: ~/ihk-projekt/scripts
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Daten-Ordner für Persistenz: ~/ihk-projekt/backend/data
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# JSON-Datei für Instanzen
INSTANCES_FILE = DATA_DIR / "instances.json"
ORDERS_FILE = DATA_DIR / "orders.json"

# Pfade zu den Skripten im scripts-Ordner:
WP_PROVISION_SCRIPT = SCRIPTS_DIR / "provision_wp.sh"
WP_DELETE_SCRIPT = SCRIPTS_DIR / "delete_wp.sh"
WP_SUSPEND_SCRIPT = SCRIPTS_DIR / "suspend_wp.sh"
WP_RESUME_SCRIPT = SCRIPTS_DIR / "resume_wp.sh"

ODOO_PROVISION_SCRIPT = SCRIPTS_DIR / "provision_odoo.sh"
ODOO_DELETE_SCRIPT = SCRIPTS_DIR / "delete_odoo.sh"

# Optionaler API-Key
API_KEY = os.getenv("BACKEND_API_KEY")

# Stripe-Konfiguration (Testmodus)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# SMTP-/Mail-Konfiguration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
SMTP_USERNAME = os.getenv("SMTP_USERNAME") or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or None

# Absenderadresse für Systemmails
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@example.test")

# Standard-Zieladresse für Zugangsdaten (z. B. für Test / IHK-Demo)
ACCESS_DATA_EMAIL_TO = os.getenv("ACCESS_DATA_EMAIL_TO")
