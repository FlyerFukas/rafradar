@echo off
cd /d "%~dp0"
title RafRadar - Kontrol Paneli
py src\panel.py
if errorlevel 1 (
  echo.
  echo Panel baslatilamadi. Python kurulu mu? "py --version" ile kontrol edin.
  pause
)
