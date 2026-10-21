$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "release_pack.py") @args
exit $LASTEXITCODE
