@echo off
chcp 65001 >nul
set PYTHONUTF8=1

echo.
echo ======================================================================
echo               BANCO BARI  ^|  CENTRAL DE AUTOMACAO DE CREDITO
echo ======================================================================
echo.

cd /d "%~dp0"

:: ==============================================================================
:: Este .bat delega TODO o trabalho ao run_project.ps1 via PowerShell.
:: O PS1 cuida de: detectar Python, baixar versao portatil se necessario,
:: instalar dependencias e rodar a esteira. Nenhuma instalacao no sistema.
:: ==============================================================================

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_project.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] A esteira retornou com falha. Veja as mensagens acima.
    pause
    exit /b %errorlevel%
)
