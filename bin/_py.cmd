@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "TARGET=%~1"
if "%TARGET%"=="" (
  echo 用法：_py.cmd ^<python 脚本^> [参数...] 1>&2
  exit /b 2
)
shift
set "USERARGS="
:collect
if "%~1"=="" goto exec
set USERARGS=!USERARGS! "%~1"
shift
goto collect
:exec
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%TARGET%" !USERARGS!
  exit /b !ERRORLEVEL!
)
where python >nul 2>&1
if not errorlevel 1 (
  python "%TARGET%" !USERARGS!
  exit /b !ERRORLEVEL!
)
where python3 >nul 2>&1
if not errorlevel 1 (
  python3 "%TARGET%" !USERARGS!
  exit /b !ERRORLEVEL!
)
echo 需要 Python 3.10 或更高版本（py -3、python 或 python3） 1>&2
exit /b 1
