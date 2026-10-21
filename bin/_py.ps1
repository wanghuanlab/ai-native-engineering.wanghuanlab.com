$ErrorActionPreference = "Stop"
if ($args.Count -lt 1) {
    Write-Error "用法：_py.ps1 <python 脚本> [参数...]"
    exit 2
}
$Script = $args[0]
$rest = @()
if ($args.Count -gt 1) { $rest = $args[1..($args.Count - 1)] }
function Invoke-Py([string]$Exe, [string[]]$Prefix) {
    & $Exe @Prefix $Script @rest
    exit $LASTEXITCODE
}
if (Get-Command py -ErrorAction SilentlyContinue) { Invoke-Py "py" @("-3") }
if (Get-Command python -ErrorAction SilentlyContinue) { Invoke-Py "python" @() }
if (Get-Command python3 -ErrorAction SilentlyContinue) { Invoke-Py "python3" @() }
Write-Error "需要 Python 3.10 或更高版本（py -3、python 或 python3）"
exit 1
