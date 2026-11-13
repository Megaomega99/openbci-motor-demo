@echo off
chcp 65001 >nul
title Comprobar senal OpenBCI
cd /d "%~dp0.."
call "%~dp0_conda.bat" bci || (pause & exit /b 1)
python -u -m bci_motor.check --board cyton --active --bias %*
echo.
pause
