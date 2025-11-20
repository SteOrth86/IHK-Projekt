#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <slug>" >&2
  echo "Example: $0 kunde1" >&2
  exit 1
fi

SLUG="$1"
NS="odoo-${SLUG}"
RELEASE="odoo-${SLUG}"

echo ">>> [STUB] Odoo-Instanz löschen"
echo "    Slug:      ${SLUG}"
echo "    Namespace: ${NS}"
echo "    Release:   ${RELEASE}"
echo
echo ">>> Hinweis: Dieses Skript ist noch nicht implementiert (nur Stub)."

# später: helm uninstall + namespace delete
exit 1
