#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  echo "Example: $0 odoo-kunde1" >&2
  exit 1
fi

NS="$1"
RELEASE="${NS}"

echo ">>> Lösche Odoo-Instanz"
echo "    Namespace: ${NS}"
echo "    Release:   ${RELEASE}"
echo

# Helm-Realease entfernen (falls vorhanden)

if helm status "${Release}" -n "${NS} >/dev/null 2>&1; then
  helm uninstall "${RELEASE}" -n "${NS}"
else
  echo "Hinweis: Helm-Release ${RELEASE} in Namespace ${NS} nicht gefunden."
fi

# Namespace löschen (falls vorhansden)

if kubectl get ns "${NS}" >/dev/null 2>&1; then
  kubectl delete namespace "${NS}"
else
  echo "Hinweis: Namespace ${NS} existiert nicht."
fi

echo
echo ">>> Deinstallation abgeschlossen. Prüfen mit:"
echo "    helm list -A | grep odoo-"
echo "    kubectl get ns | grep odoo-"
