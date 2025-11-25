#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${BACKEND_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  echo "Fehler: BACKEND_API_KEY ist nicht gesetzt." >&2
  echo "Bitte export BACKEND_API_KEY=... vor dem Aufruf." >&2
  exit 1
fi

echo ">>> Hole aktuelle Instanzen von ${BASE_URL}/instances ..."
RESP="$(curl -s "${BASE_URL}/instances")"

# Falls der Backend-Endpoint keine Liste zurückgibt (z. B. Fehlerseite)
if ! echo "$RESP" | jq -e . >/dev/null 2>&1; then
  echo "Fehler: Antwort von /instances ist kein gültiges JSON." >&2
  echo "$RESP"
  exit 1
fi

COUNT="$(echo "$RESP" | jq 'length')"

if [[ "$COUNT" -eq 0 ]]; then
  echo "Keine Instanzen vorhanden. Nichts zu löschen."
  exit 0
fi

echo "Gefundene Instanzen: $COUNT"
echo

# Format: "<type> <id>" pro Zeile
echo "$RESP" | jq -r '.[] | "\(.type) \(.id)"' | while read -r TYPE ID; do
  case "$TYPE" in
    wordpress)
      PREFIX="wp"
      ;;
    odoo)
      PREFIX="odoo"
      ;;
    *)
      echo "Überspringe unbekannten Typ '$TYPE' für ID '$ID'."
      continue
      ;;
  esac

  URL="${BASE_URL}/instances/${PREFIX}/${ID}"
  echo ">>> Lösche ${TYPE}-Instanz '${ID}' via ${URL}"

  HTTP_CODE="$(
    curl -s -o /dev/null -w "%{http_code}" \
      -X DELETE "$URL" \
      -H "X-API-Key: ${API_KEY}"
  )"

  echo "    HTTP-Status: ${HTTP_CODE}"
  echo
done

echo ">>> Aufräumen abgeschlossen."
exit 0
