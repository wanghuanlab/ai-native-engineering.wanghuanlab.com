$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "sync_baseline.py") @args
exit $LASTEXITCODE
