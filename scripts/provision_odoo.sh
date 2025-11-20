#!/usr/bin/env bash
set -euo pipefail

# Erwartet: <slug> [domain]
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <slug> [domain]" >&2
  echo "Example: $0 kunde1 kunde1.odoo.local" >&2
  exit 1
fi

SLUG="$1"
if [ "$#" -eq 2 ]; then
  DOMAIN="$2"
else
  DOMAIN="${SLUG}.odoo.local"
fi

NS="odoo-${SLUG}"
RELEASE="odoo-${SLUG}"

echo ">>> [STUB] Odoo-Instanz vorbereiten"
echo "    Slug:      ${SLUG}"
echo "    Namespace: ${NS}"
echo "    Release:   ${RELEASE}"
echo "    Domain:    ${DOMAIN}"
echo
echo ">>> Hinweis: Dieses Skript ist noch nicht implementiert (nur Stub)."

# später kommt hier echte Helm-/Kubernetes-Logik hin
exit 1
