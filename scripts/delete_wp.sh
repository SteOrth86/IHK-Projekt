#!/usr/bin/env bash

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <slug>"
  echo "Example: $0 kunde3"
  exit 1
fi

SLUG="$1"
NS="wp-${SLUG}"
RELEASE="wp-${SLUG}"

echo ">>> Lösche WordPress-Instanz"
echo "    Slug:       ${SLUG}"
echo "    Namespace:  ${NS}"
echo "    Release:    ${RELEASE}"
echo

# Helm-Release entfernen (falls vorhanden)
if helm status "${RELEASE}" -n "${NS}" >/dev/null 2>&1; then
  helm uninstall "${RELEASE}" -n "${NS}"
else
  echo "Hinweis: Helm-Release ${RELEASE} in Namespace ${NS} nicht gefunden."
fi

# Namespace löschen (falls vorhanden)
if kubectl get ns "${NS}" >/dev/null 2>&1; then
  kubectl delete namespace "${NS}"
else
  echo "Hinweis: Namespace ${NS} existiert nicht."
fi

echo
echo ">>> Fertig. Prüfen mit:"
echo "    helm list -A"
echo "    kubectl get ns"
