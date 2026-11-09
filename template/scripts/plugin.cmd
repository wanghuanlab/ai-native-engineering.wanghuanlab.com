@echo off
call "%~dp0_py.cmd" "%~dp0plugin.py" %*
exit /b %ERRORLEVEL%
