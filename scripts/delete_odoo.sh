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

echo ">>> Lösche Odoo-Instanz"
echo "    Slug:      ${SLUG}"
echo "    Namespace: ${NS}"
echo "    Release:   ${RELEASE}"
echo

echo ">>> Helm-Release entfernen (falls vorhanden)..."
helm uninstall "${RELEASE}" --namespace "${NS}" || echo "Helm-Release nicht gefunden, fahre fort..."

echo ">>> Namespace löschen (falls vorhanden)..."
kubectl delete namespace "${NS}" --ignore-not-found

echo
echo ">>> Löschen abgeschlossen."
