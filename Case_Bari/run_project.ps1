# ==============================================================================
# RUN_PROJECT.ps1 — Grupo Bari | Pipeline Orchestrator
# Usa Python PORTÁTIL (sem instalação no sistema, sem admin, sem risco).
# Baixa um zip leve do python.org, extrai na pasta .python_portable e roda tudo.
# ==============================================================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Blue
Write-Host "              BANCO BARI  |  CENTRAL DE AUTOMACAO DE CREDITO          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Blue
Write-Host ""

# ==============================================================================
# BLOCO 1: DETECTA SE JÁ EXISTE UM PYTHON REAL (não é stub da Microsoft Store)
# ==============================================================================
function Get-RealPython {
    foreach ($cmd in @("python", "py", "python3")) {
        try {
            $found = Get-Command $cmd -ErrorAction Stop
            # Stubs da Microsoft Store ficam em WindowsApps — ignorar
            if ($found.Source -like "*WindowsApps*") { continue }
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3") { return $cmd }
        } catch { }
    }
    return $null
}

$pyCmd = Get-RealPython

# ==============================================================================
# BLOCO 2: PYTHON PORTÁTIL (sem instalação, sem admin, sem risco de BSOD)
# ==============================================================================
$portableDir = Join-Path $PSScriptRoot ".python_portable"
$portablePy  = Join-Path $portableDir "python.exe"
$portablePip = Join-Path $portableDir "Scripts\pip.exe"

if (-not $pyCmd) {
    Write-Host "[AUTO-SETUP] Python nao encontrado. Configurando Python Portatil..." -ForegroundColor Yellow
    Write-Host "  -> Nenhuma instalacao no sistema. Nenhum admin necessario." -ForegroundColor DarkGray
    Write-Host ""

    if (-not (Test-Path $portablePy)) {
        # --- 2a. Baixa o zip embeddable do python.org ---
        $pyVersion = "3.12.10"
        $zipUrl    = "https://www.python.org/ftp/python/$pyVersion/python-$pyVersion-embed-amd64.zip"
        $zipPath   = Join-Path $env:TEMP "python_embed.zip"

        Write-Host "  Passo 1/3: Baixando Python $pyVersion portatil (~10 MB)..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
        } catch {
            Write-Host "[ERRO] Falha ao baixar Python: $_" -ForegroundColor Red
            Write-Host "Verifique sua conexao com a internet e tente novamente." -ForegroundColor Yellow
            Read-Host "Pressione ENTER para sair"
            exit 1
        }

        # --- 2b. Extrai o zip ---
        Write-Host "  Passo 2/3: Extraindo para .python_portable ..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $portableDir -Force | Out-Null
        Expand-Archive -Path $zipPath -DestinationPath $portableDir -Force
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

        # --- 2c. Habilita site-packages (necessário para pip funcionar) ---
        $pthFile = Get-ChildItem $portableDir -Filter "python*._pth" | Select-Object -First 1
        if ($pthFile) {
            $pthContent = Get-Content $pthFile.FullName -Raw
            $pthContent = $pthContent -replace "#import site", "import site"
            Set-Content $pthFile.FullName $pthContent -Encoding ASCII
        }

        # --- 2d. Instala pip via get-pip.py ---
        Write-Host "  Passo 3/3: Instalando pip no ambiente portatil..." -ForegroundColor Cyan
        $getPipPath = Join-Path $portableDir "get-pip.py"
        try {
            Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipPath -UseBasicParsing
            & $portablePy $getPipPath --quiet
        } catch {
            Write-Host "[ERRO] Falha ao instalar pip: $_" -ForegroundColor Red
            Read-Host "Pressione ENTER para sair"
            exit 1
        }
        Remove-Item $getPipPath -Force -ErrorAction SilentlyContinue

        Write-Host ""
        Write-Host "  Python Portatil configurado em .python_portable\" -ForegroundColor Green
    } else {
        Write-Host "  Python Portatil ja existe em .python_portable\" -ForegroundColor Green
    }

    $pyCmd = $portablePy
}

$pyVersion = & $pyCmd --version 2>&1
Write-Host "-> Usando: $pyVersion" -ForegroundColor Cyan
Write-Host ""

# ==============================================================================
# BLOCO 3: INSTALA AS DEPENDÊNCIAS (pandas, numpy, matplotlib)
# ==============================================================================
$stampFile = Join-Path $portableDir ".deps_ok"
$reqFile   = "requirements.txt"
if (-not (Test-Path $reqFile)) { $reqFile = "..\requirements.txt" }

# Instala apenas se:
#   1. O carimbo .deps_ok não existe (primeira vez), OU
#   2. O requirements.txt foi modificado depois do carimbo (dependências mudaram)
$needsInstall = $true
if ((Test-Path $stampFile) -and (Test-Path $reqFile)) {
    $stampTime = (Get-Item $stampFile).LastWriteTime
    $reqTime   = (Get-Item $reqFile).LastWriteTime
    if ($stampTime -gt $reqTime) { $needsInstall = $false }
}

if ($needsInstall -and (Test-Path $reqFile)) {
    Write-Host "[AUTO-SETUP] Instalando dependencias do requirements.txt..." -ForegroundColor Yellow
    if ($pyCmd -eq $portablePy -and (Test-Path $portablePip)) {
        & $portablePip install -r $reqFile --quiet --no-warn-script-location
    } else {
        & $pyCmd -m pip install -r $reqFile --quiet --no-warn-script-location
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Falha ao instalar dependencias." -ForegroundColor Red
        Read-Host "Pressione ENTER para sair"
        exit 1
    }
    # Grava o carimbo para não precisar reinstalar nas próximas execuções
    New-Item -ItemType File -Path $stampFile -Force | Out-Null
    Write-Host "Dependencias instaladas com sucesso!" -ForegroundColor Green
} elseif (-not (Test-Path $reqFile)) {
    Write-Host "[AVISO] requirements.txt nao encontrado." -ForegroundColor Yellow
} else {
    Write-Host "-> Dependencias ja instaladas. Pulando." -ForegroundColor DarkGray
}

Write-Host ""

# ==============================================================================
# BLOCO 4: EXECUÇÃO DA ESTEIRA (3 ETAPAS)
# ==============================================================================
Write-Host "[ ETAPA 1/3 ] Diagnostico e Analise Estatistica do Funil..." -ForegroundColor Yellow
& $pyCmd funnel_analysis.py
if ($LASTEXITCODE -ne 0) { Write-Host "[ERRO] Etapa 1 falhou." -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host ""
Write-Host "[ ETAPA 2/3 ] Esteira Automatizada RPA + Relatorio Executivo PDF..." -ForegroundColor Yellow
& $pyCmd rpa_routine.py
if ($LASTEXITCODE -ne 0) { Write-Host "[ERRO] Etapa 2 falhou." -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host ""
Write-Host "[ ETAPA 3/3 ] Extracao Inteligente de Laudos com IA (NLP)..." -ForegroundColor Yellow
& $pyCmd ai_extraction.py
if ($LASTEXITCODE -ne 0) { Write-Host "[ERRO] Etapa 3 falhou." -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  ESTEIRA EXECUTADA COM SUCESSO!" -ForegroundColor Green
Write-Host "  Entregaveis gerados:" -ForegroundColor Green
Write-Host "    Relatorio_Lideranca.pdf  (One-Pager executivo para diretoria)" -ForegroundColor Green
Write-Host "    laudos_extraidos.json    (17 laudos estruturados)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
