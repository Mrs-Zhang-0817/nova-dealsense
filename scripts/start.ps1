param([Parameter(Mandatory)][ValidateSet('api','web')][string]$Service)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
if ($Service -eq 'api') {
    Set-Location "$root/backend"
    & "$root/.venv/Scripts/python.exe" -m alembic upgrade head
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & "$root/.venv/Scripts/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
} else {
    Set-Location "$root/frontend"
    npm.cmd run start -- --hostname 127.0.0.1 --port 3000
}
exit $LASTEXITCODE
