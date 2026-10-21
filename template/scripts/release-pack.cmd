@echo off
call "%~dp0_py.cmd" "%~dp0release_pack.py" %*
exit /b %ERRORLEVEL%
