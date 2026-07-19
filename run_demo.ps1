$ErrorActionPreference = 'Stop'
Write-Host 'Starting ClassPulse at http://127.0.0.1:8000' -ForegroundColor Green
Start-Process 'http://127.0.0.1:8000'
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
