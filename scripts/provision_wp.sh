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

# Verzeichnisse relativ zum Skript bestimmen
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VALUES_FILE="${PROJECT_ROOT}/k8s/minikube/wp-values.yaml"

if [ ! -f "${VALUES_FILE}" ]; then
  echo "Fehler: Values-Datei nicht gefunden: ${VALUES_FILE}" >&2
  exit 1
fi

echo ">>> Verwende Values-Datei: ${VALUES_FILE}"
echo

# Namespace explizit anlegen (falls nicht vorhanden)
kubectl get ns "${NS}" >/dev/null 2>&1 || kubectl create namespace "${NS}"

# WICHTIG: Hier NUR das VALUES_FILE verwenden, NICHT 'wp-values.yaml'
helm install "${RELEASE}" bitnami/wordpress \
  -n "${NS}" \
  --create-namespace \
  -f "${VALUES_FILE}" \
  --set ingress.hostname="${HOST}"

echo
echo ">>> Fertig. Status prüfen mit:"
echo "    kubectl get pods -n ${NS}"
echo "    kubectl get ingress -n ${NS}"
