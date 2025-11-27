#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  exit 1
fi

NAMESPACE="$1"

echo "[suspend_wp] Suspend WordPress in namespace: ${NAMESPACE}"
# TODO: Hier könntest du später z. B. ein Deployment skalieren:
# kubectl -n "${NAMESPACE}" scale deployment wordpress --replicas=0
