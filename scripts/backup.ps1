param([Parameter(Mandatory)][string]$Archive)
$ErrorActionPreference='Stop'
$dest=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Archive)
& "$PSScriptRoot/../.venv/Scripts/python.exe" "$PSScriptRoot/../backend/maintenance.py" backup $dest
exit $LASTEXITCODE
