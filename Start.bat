@echo off
setlocal
title eBay Auction Tool
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 server.py
  goto :end
)
where python >nul 2>&1
if not errorlevel 1 (
  python server.py
  goto :end
)
echo Python 3 wurde nicht gefunden.
echo Bitte Python 3 von https://www.python.org/downloads/windows/ installieren.
echo Bei der Installation "Add Python to PATH" aktivieren.
pause
:end
endlocal
