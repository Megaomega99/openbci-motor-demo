@echo off
chcp 65001 >nul
title Instalar entorno bci
cd /d "%~dp0.."
call "%~dp0_conda.bat" base || (pause & exit /b 1)
call conda env create -f environment.yml || call conda env update -f environment.yml --prune
echo.
echo Listo. Prueba con scripts\comprobar_senal.bat
pause
