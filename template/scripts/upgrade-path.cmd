@echo off
call "%~dp0_py.cmd" "%~dp0upgrade_path.py" %*
exit /b %ERRORLEVEL%
