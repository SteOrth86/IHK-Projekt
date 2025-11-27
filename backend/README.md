# kube-app-provisioner

FastAPI-Backend zum Provisionieren von WordPress- und Odoo-Instanzen (Minikube). Code liegt jetzt im Paket `kube_app_provisioner`.

## Quickstart (lokal)
- Python 3.12, virtualenv anlegen: `python3 -m venv .venv && source .venv/bin/activate`
- Dependencies: `pip install -r requirements.txt`
- Start: `uvicorn kube_app_provisioner.main:app --host 0.0.0.0 --port 8000`
- API-Key optional per Env: `export BACKEND_API_KEY=devkey123`

## Tests
- `./.venv/bin/python -m pytest`

## Provisioning-Skripte (Minikube)
- Pfade: `scripts/provision_odoo.sh`, `scripts/provision_wp.sh`, plus delete/suspend/resume.
- Erwartet `kubectl`/`helm` und Minikube-Context.

## Docker
- Build aus `backend/`: `docker build -t kube-app-provisioner:dev .`
- Run: `docker run -p 8000:8000 kube-app-provisioner:dev`

## Struktur
- `kube_app_provisioner/`: Backend-Paket (routers, services, utils, schemas, config, storage)
- `data/`: Persistente JSON-Stores (instances/orders)
- `scripts/`: K8s/Helm Provisioning + Suspend/Resume
- `tests/`: Pytest-Suite (nutzt Paket-Imports)
