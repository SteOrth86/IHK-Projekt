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
HOST="${SLUG}.local"

echo ">>> Provisioniere WordPress-Instanz"
echo "    Slug:       ${SLUG}"
echo "    Namespace:  ${NS}"
echo "    Release:    ${RELEASE}"
echo "    Hostname:   ${HOST}"
echo

# Namespace wird von Helm auch erstellt, aber so ist es explizit
kubectl get ns "${NS}" >/dev/null 2>&1 || kubectl create namespace "${NS}"

helm install "${RELEASE}" bitnami/wordpress \
  -n "${NS}" \
  --create-namespace \
  -f wp-values.yaml \
  --set ingress.hostname="${HOST}"

echo
echo ">>> Fertig. Status prüfen mit:"
echo "    kubectl get pods -n ${NS}"
echo "    kubectl get ingress -n ${NS}"
