#!/usr/bin/env bash

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <namespace>"
  echo "Example: $0 kunde1"
  exit 1
fi

NS="$1"
RELEASE="${NS}"

echo ">>> Lösche WordPress-Instanz"
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
