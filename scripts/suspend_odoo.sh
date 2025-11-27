#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  exit 1
fi

NAMESPACE="$1"

echo "[suspend_odoo] Suspend Odoo in namespace: ${NAMESPACE}"
# Beispiel: Deployment herunter skalieren. Passe den Namen bei Bedarf an.
kubectl -n "${NAMESPACE}" scale deployment odoo --replicas=0
