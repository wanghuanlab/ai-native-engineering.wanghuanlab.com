@echo off
call "%~dp0_py.cmd" "%~dp0lib\new_change.py" %*
exit /b %ERRORLEVEL%
