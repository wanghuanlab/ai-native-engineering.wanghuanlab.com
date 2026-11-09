$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "dev.py") @args
exit $LASTEXITCODE
