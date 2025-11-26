#!/usr/bin/env bash
# Einfacher Smoke-Check für eine WordPress-Instanz über Ingress.
# Prüft die Login-Seite /wp-login.php und bewertet HTTP 200 oder 302 als "OK".

set -euo pipefail

HOST="${1:-demo1.local}"
SCHEME="${2:-http}"

URL="${SCHEME}://${HOST}/wp-login.php"

echo "Smoke-Check für WordPress-Login-Seite:"
echo "  URL:  ${URL}"
echo

# Wir fangen den curl-Exitcode ab, statt bei Fehler hart abzubrechen
set +e
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "${URL}")
CURL_EXIT=$?
set -e

if [[ "${CURL_EXIT}" -ne 0 ]]; then
  echo "❌ Smoke-Check FEHLER: curl-Fehler ${CURL_EXIT} (z. B. Host nicht erreichbar oder TLS-Problem)"
  exit 1
fi

echo "  HTTP-Status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "302" ]]; then
  echo "✅ Smoke-Check OK: WordPress-Login ist erreichbar."
  exit 0
else
  echo "❌ Smoke-Check FEHLER: Erwartet 200 oder 302, aber bekommen: ${HTTP_CODE}"
  exit 1
fi
