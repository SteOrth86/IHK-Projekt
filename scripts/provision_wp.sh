#!/usr/bin/env bash

set -euo pipefail

# Erwartet: <slug> [domain]
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <slug> [domain]" >&2
  echo "Example: $0 kunde3 kunde3.local" >&2
  exit 1
fi

SLUG="$1"

# Domain: entweder 2. Parameter oder Default "<slug>.local"
if [ "$#" -eq 2 ]; then
  DOMAIN="$2"
else
  DOMAIN="${SLUG}.local"
fi

NS="wp-${SLUG}"
RELEASE="wp-${SLUG}"
HOST="${DOMAIN}"

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

echo ">>> Deploye WordPress via Helm..."
helm upgrade --install "${RELEASE}" bitnami/wordpress \
  --namespace "${NS}" \
  --create-namespace \
  -f "${VALUES_FILE}" \
  --set ingress.enabled=true \
  --set ingress.hostname="${HOST}" \
  --set wordpressBlogName="WP ${SLUG}"

TEMPLATE="${PROJECT_ROOT}/k8s/minikube/wp-backup-template.yaml"

if [ -f "${TEMPLATE}" ]; then
  echo
  echo ">>> Lege Backup-PVC + CronJob für ${SLUG} an..."
  sed "s/__SLUG__/${SLUG}/g" "${TEMPLATE}" | kubectl apply -f -
else
  echo
  echo ">>> Hinweis: Backup-Template nicht gefunden (${TEMPLATE}), üb>
fi

echo
echo ">>> Fertig!"
echo "    Namespace: ${NS}"
echo "    Release:   ${RELEASE}"
echo "    Hostname:  ${HOST}"
echo "    Hinweis:   Bitte /etc/hosts oder DNS so konfigurieren, dass ${HOST} auf die Minikube-IP zeigt."

