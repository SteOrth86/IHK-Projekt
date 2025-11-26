#!/usr/bin/env bash
# Einfacher Smoke-Check für eine WordPress-Instanz über Ingress.
# Prüft die Login-Seite /wp-login.php und bewertet HTTP 200 oder 302 als "OK".

set -euo pipefail

# Erster Parameter: Hostname (z. B. demo1.local)
HOST="${1:-demo1.local}"

# Zweiter Parameter: Schema (http oder https), Default: http
SCHEME="${2:-http}"

URL="${SCHEME}://${HOST}/wp-login.php"

echo "Smoke-Check für WordPress-Login-Seite:"
echo "  URL:  ${URL}"
echo

# HTTP-Statuscode abfragen (ohne Body)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}")

echo "  HTTP-Status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "302" ]]; then
  echo "✅ Smoke-Check OK: WordPress-Login ist erreichbar."
  exit 0
else
  echo "❌ Smoke-Check FEHLER: Erwartet 200 oder 302, aber bekommen: ${HTTP_CODE}"
  exit 1
fi
