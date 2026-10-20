@echo off
title SUB.DOM-BBR
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py SUB.DOM-BBR.py
) else (
    python SUB.DOM-BBR.py
)
if errorlevel 1 (
    echo.
    echo Could not start. Install Python 3 from https://www.python.org/downloads/
    echo During setup, enable "Add Python to PATH".
    pause
)
