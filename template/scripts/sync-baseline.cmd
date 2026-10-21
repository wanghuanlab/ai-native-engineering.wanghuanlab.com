@echo off
call "%~dp0_py.cmd" "%~dp0sync_baseline.py" %*
exit /b %ERRORLEVEL%
