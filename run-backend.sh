#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source backend/.venv/bin/activate
cd backend
exec python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
