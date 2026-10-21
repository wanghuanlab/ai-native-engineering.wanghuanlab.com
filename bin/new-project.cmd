@echo off
call "%~dp0_py.cmd" "%~dp0new_project.py" %*
exit /b %ERRORLEVEL%
