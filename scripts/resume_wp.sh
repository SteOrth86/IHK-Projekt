#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <namespace>" >&2
  exit 1
fi

NAMESPACE="$1"

echo "[resume_wp] Resume WordPress in namespace: ${NAMESPACE}"
# TODO: Hier könntest du später wieder hochskalieren:
# kubectl -n "${NAMESPACE}" scale deployment wordpress --replicas=1
