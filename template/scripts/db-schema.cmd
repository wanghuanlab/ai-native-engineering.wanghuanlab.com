@echo off
call "%~dp0_py.cmd" "%~dp0db_schema.py" %*
exit /b %ERRORLEVEL%
