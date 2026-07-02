@echo off
title Sentinel Chain Launcher
echo.
echo ========================================
echo   Sentinel Chain Launcher
echo ========================================
echo.
cd /d "%~dp0"

if not exist "%~dp0Launch-Sentinel-Chain.ps1" (
  echo.
  echo Sentinel Chain could not find Launch-Sentinel-Chain.ps1.
  echo Please extract the full Sentinel Chain folder, or reinstall with SentinelChain-Setup.
  echo Send this screenshot to Sentinel Chain support if the problem continues.
  pause
  exit /b 2
)

set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL%" (
  where powershell.exe >nul 2>nul
  if errorlevel 1 (
    echo.
    echo PowerShell was not found. Sentinel Chain needs Windows PowerShell to start and repair missing dependencies.
    echo Please send this screenshot to Sentinel Chain support.
    pause
    exit /b 9009
  )
  set "POWERSHELL=powershell.exe"
)

"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-Sentinel-Chain.ps1" %*
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" (
  echo.
  echo Sentinel Chain Launcher exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
