#!/usr/bin/env sh
set -eu
echo "Starting AhaLoop at http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
