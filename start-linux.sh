#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
