@echo off
chcp 65001 >nul
set PYTHONUTF8=1

echo.
echo ======================================================================
echo               BANCO BARI  ^|  CENTRAL DE AUTOMACAO DE CREDITO
echo ======================================================================
echo.
echo [AVISO DE AMBIENTE WINDOWS]
echo Este script verifica os pre-requisitos de execucao do projeto.
echo Caso nao estejam presentes, o script baixara e instalara
echo automaticamente as bibliotecas necessarias (pandas, numpy, matplotlib)
echo e o Python portatil de forma isolada, sem alterar o sistema operacional.
echo.

cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_project.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] A esteira retornou com falha. Veja as mensagens acima.
    pause
    exit /b %errorlevel%
)
