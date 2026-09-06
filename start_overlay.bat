@echo off
setlocal
cd /d "%~dp0"
title Dawnwalker Death Overlay

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 server.py
    goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
    python server.py
    goto :end
)

echo.
echo [BLAD] Nie znaleziono Python 3.
echo Zainstaluj Python 3 i zaznacz opcje "Add Python to PATH".
echo.
pause

:end
endlocal
