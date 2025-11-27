# Stripe Webhook Quickstart (Testmodus)

## Voraussetzungen
- Stripe CLI installiert und eingeloggt (`stripe login`).
- Backend läuft: `uvicorn kube_app_provisioner.main:app --host 0.0.0.0 --port 8000`
- Env: `STRIPE_SECRET_KEY` (Test-Key), `STRIPE_WEBHOOK_SECRET` (s. Stripe CLI)

## Einrichten
```bash
cd ~/ihk-projekt/backend
export STRIPE_SECRET_KEY=sk_test_...
stripe listen --forward-to localhost:8000/webhooks/stripe
# Ausgabe enthält: Webhook signing secret -> STRIPE_WEBHOOK_SECRET setzen
export STRIPE_WEBHOOK_SECRET=whsec_...
```

## Order anlegen und testen
1) Order erstellen (Beispiel WordPress):
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_type":"wordpress","instance_slug":"stripe-demo","domain":"stripe-demo.example.test"}'
```
Order-ID aus Antwort merken (`id`).

2) Checkout-Event triggern:
```bash
stripe trigger checkout.session.completed \
  --add-body=checkout_session.client_reference_id=<ORDER_ID>
```

3) Ergebnis prüfen:
```bash
curl http://localhost:8000/orders/<ORDER_ID>        # status should be provisioned, instance_id set
curl http://localhost:8000/instances/<instance_id>  # Instanzdaten
```

## Hinweise
- `product_type: "wordpress"` oder `"odoo"` werden provisioniert; unbekannte Typen ignoriert.
- Bei Provisionierungsfehlern (z. B. Skript) wird Order-Status auf `error` gesetzt.
- Für Tests ohne Signaturprüfung `STRIPE_WEBHOOK_SECRET` leer lassen (nur lokal empfohlen).
