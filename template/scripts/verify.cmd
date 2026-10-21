@echo off
call "%~dp0_py.cmd" "%~dp0verify.py" %*
exit /b %ERRORLEVEL%
