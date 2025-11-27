#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  exit 1
fi

NAMESPACE="$1"

echo "[resume_odoo] Resume Odoo in namespace: ${NAMESPACE}"
# Beispiel: Deployment wieder hoch skalieren. Passe den Namen bei Bedarf an.
kubectl -n "${NAMESPACE}" scale deployment odoo --replicas=1
