@echo off
rem WINDOWS ONLY. On a Mac, use start.command instead.
rem Double-click this file on Windows to start the project dashboard.
setlocal
cd /d "%~dp0"
title Project dashboard

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto nopython
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 goto nopython

if exist ".venv\Scripts\python.exe" goto packages
echo First start: setting things up. This takes a few minutes and needs the internet.
%PY% -m venv .venv
if errorlevel 1 goto failed

:packages
".venv\Scripts\python.exe" -c "import streamlit, pandas, openpyxl, yaml" >nul 2>nul
if not errorlevel 1 goto run
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 goto failed

:run
".venv\Scripts\python.exe" run.py
goto end

:nopython
echo.
echo Python 3.11 or newer is not installed.
echo Install it from https://www.python.org/downloads/
echo Answer y to the questions the installer asks.
echo If Python is already installed and you still see this, open Command Prompt,
echo type:  py install   and press Enter.
echo Then double-click start.bat again.
echo.
pause
goto end

:failed
echo.
echo Set-up failed. Check the internet connection and double-click start.bat again.
echo.
pause

:end
endlocal
