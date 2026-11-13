@echo off
rem Busca conda y activa el entorno "bci". Lo usan los demas .bat.
set "CONDA_ACT="
if defined CONDA_EXE for %%I in ("%CONDA_EXE%") do if exist "%%~dpIactivate.bat" set "CONDA_ACT=%%~dpIactivate.bat"
for %%P in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3" "%LOCALAPPDATA%\miniconda3" "%LOCALAPPDATA%\anaconda3" "C:\ProgramData\miniconda3" "C:\ProgramData\anaconda3" "%USERPROFILE%\miniforge3") do (
    if not defined CONDA_ACT if exist "%%~P\Scripts\activate.bat" set "CONDA_ACT=%%~P\Scripts\activate.bat"
)
if not defined CONDA_ACT (
    echo No encuentro conda. Instala Miniconda: https://docs.conda.io/en/latest/miniconda.html
    exit /b 1
)
call "%CONDA_ACT%" %1
