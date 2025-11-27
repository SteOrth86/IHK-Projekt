# kube-app-provisioner

Provisioniert WordPress- und Odoo-Instanzen (Minikube) über FastAPI.

## Backend starten
- Voraussetzungen: Python 3.12, Minikube/Kubectl/Helm für echte Provisionierung.
- Setup:
  ```bash
  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  export BACKEND_API_KEY=devkey123   # optional
  uvicorn kube_app_provisioner.main:app --host 0.0.0.0 --port 8000
  ```
- API-Doku: http://localhost:8000/docs (API-Key per Authorize, falls gesetzt).

## Stripe/Webhook (Test)
- Env setzen: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (z. B. aus `stripe listen`).
- Stripe CLI: `stripe listen --forward-to localhost:8000/webhooks/stripe`.
- Checkout-Test: `stripe trigger checkout.session.completed --add-body=checkout_session.client_reference_id=<ORDER_ID>`.
- Orders/API: `POST /orders` anlegen; Webhook provisioniert WP/Odoo (Status `provisioned`, `instance_id` gesetzt).

## Provisioning-Skripte
- Liegen in `scripts/`: provision/delete/suspend/resume für WP/Odoo, nutzen kubectl/helm.
- Pfade in `backend/kube_app_provisioner/core/config.py`.

## Docker
- Build aus `backend/`: `docker build -t kube-app-provisioner:dev .`
- Run: `docker run -p 8000:8000 kube-app-provisioner:dev`

## Struktur
- `backend/kube_app_provisioner/`:
  - `common/` (Audit, Errors, RequestID, Validators)
  - `core/` (Config, Models, Storage, Status, k8s_status)
  - `services/core/` (Lifecycle-Helpers)
  - `services/apps/` (wordpress, odoo, orders, health, status, email)
  - `routers/` (FastAPI-Router)
  - `utils/` (run_script)
  - `main.py` (FastAPI-App)
- `backend/data/` Persistenz (JSON)
- `backend/tests/` Pytest
- `scripts/` K8s/Helm Skripte
