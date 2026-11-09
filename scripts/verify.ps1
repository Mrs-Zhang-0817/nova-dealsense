param([string]$Api='http://localhost:8000/api/v1',[string]$Web='http://localhost:3000')
$ErrorActionPreference='Stop'
if (-not (Invoke-RestMethod "$Api/health").success){throw 'API unavailable'}
$markets=Invoke-RestMethod "$Api/markets"
if ('CN' -notin $markets.country_code -or 'US' -notin $markets.country_code){throw 'Missing demo markets'}
$dashboard=Invoke-RestMethod "$Api/dashboard"
if ($null -eq $dashboard.demo.feasible_runs){throw 'Dashboard schema mismatch'}
if ((Invoke-WebRequest -UseBasicParsing $Web).StatusCode -ne 200){throw 'Frontend unavailable'}
Write-Output 'API, database markets, dashboard and frontend OK'
