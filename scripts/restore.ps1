param([Parameter(Mandatory)][string]$Archive,[Parameter(Mandatory)][string]$Database)
$ErrorActionPreference='Stop'
& "$PSScriptRoot/../.venv/Scripts/python.exe" "$PSScriptRoot/../backend/maintenance.py" restore (Resolve-Path -LiteralPath $Archive).Path $Database
exit $LASTEXITCODE
