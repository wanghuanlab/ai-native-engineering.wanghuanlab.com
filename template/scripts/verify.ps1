$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "verify.py") @args
exit $LASTEXITCODE
