$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
& (Join-Path $here "_py.ps1") (Join-Path $here "lib\new_module.py") @args
exit $LASTEXITCODE
