@echo off
title Auto-Crypto Launcher
echo.
echo ========================================
echo   Auto-Crypto Launcher
echo ========================================
echo.
cd /d "%~dp0"

if not exist "%~dp0Launch-Auto-Crypto.ps1" (
  echo.
  echo Auto-Crypto could not find Launch-Auto-Crypto.ps1.
  echo Please extract the full Auto-Crypto folder, or reinstall with AutoCrypto-Setup.
  echo Send this screenshot to Auto-Crypto support if the problem continues.
  pause
  exit /b 2
)

set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL%" (
  where powershell.exe >nul 2>nul
  if errorlevel 1 (
    echo.
    echo PowerShell was not found. Auto-Crypto needs Windows PowerShell to start and repair missing dependencies.
    echo Please send this screenshot to Auto-Crypto support.
    pause
    exit /b 9009
  )
  set "POWERSHELL=powershell.exe"
)

"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-Auto-Crypto.ps1" %*
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" (
  echo.
  echo Auto-Crypto launcher exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
