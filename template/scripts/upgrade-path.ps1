$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "upgrade_path.py") @args
exit $LASTEXITCODE
