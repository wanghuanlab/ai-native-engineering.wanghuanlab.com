@echo off
call "%~dp0_py.cmd" "%~dp0lib\new_module.py" %*
exit /b %ERRORLEVEL%
