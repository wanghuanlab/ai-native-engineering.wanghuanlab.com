@echo off
call "%~dp0_py.cmd" "%~dp0dev.py" %*
exit /b %ERRORLEVEL%
