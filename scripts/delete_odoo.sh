#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  echo "Example: $0 odoo-kunde1" >&2
  exit 1
fi

NS="$1"
RELEASE="$NS"

echo ">>> Loesche Odoo-Instanz"
echo "    Namespace: $NS"
echo "    Release:   $RELEASE"
echo

# Helm-Release entfernen (falls vorhanden)
if helm status "$RELEASE" -n "$NS" >/dev/null 2>&1; then
  echo "Helm-Release '$RELEASE' im Namespace '$NS' gefunden. Deinstalliere..."
  helm uninstall "$RELEASE" -n "$NS"
else
  echo "Hinweis: Helm-Release '$RELEASE' in Namespace '$NS' nicht gefunden. Ueberspringe Helm-Uninstall."
fi

# Namespace loeschen (falls vorhanden)
if kubectl get ns "$NS" >/dev/null 2>&1; then
  echo "Loesche Namespace '$NS'..."
  if ! kubectl delete namespace "$NS" --wait=false; then
    echo "Warnung: Namespace '$NS' konnte nicht geloescht werden (evtl. bereits terminating oder geloescht)."
  fi
else
  echo "Hinweis: Namespace '$NS' existiert nicht. Nichts zu loeschen."
fi

echo
echo ">>> Odoo-Deinstallation abgeschlossen. Pruefen mit:"
echo "    helm list -A | grep odoo-"
echo "    kubectl get ns | grep odoo-"

exit 0
