$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectPath

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de Python.' }

if (-not (Test-Path 'node_modules\.bin\tailwindcss.cmd')) {
    npm install
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de Tailwind CSS.' }
}

npm run build:css
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el CSS de Tailwind.' }

Start-Process 'http://127.0.0.1:8002' -WindowStyle Hidden
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
