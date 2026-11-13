@echo off
chcp 65001 >nul
title Demo BCI - Mueve el motor con el cerebro
cd /d "%~dp0.."
call "%~dp0_conda.bat" bci || (pause & exit /b 1)
rem Ajusta las opciones a tu montaje (ver README):
python -u -m bci_motor --board cyton --active --bias --motor motorinador --rpm 30 %*
echo.
pause
