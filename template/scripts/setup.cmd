@echo off
call "%~dp0_py.cmd" "%~dp0setup.py" %*
exit /b %ERRORLEVEL%
