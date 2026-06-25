# install.ps1 — One-liner installer for CLI CivilEng (Windows PowerShell)
# Usage: irm https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.ps1 | iex
#
# Para revisar antes de executar:
#   irm https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.ps1 -OutFile install.ps1
#   notepad install.ps1
#   .\install.ps1

$ErrorActionPreference = "Stop"

$RepoUrl     = "https://github.com/lhenriquesouza/cli-civileng.git"
$InstallDir  = if ($env:CLI_CIVILENG_HOME) { $env:CLI_CIVILENG_HOME } else { "$env:USERPROFILE\.cli-civileng" }
$BinDir      = if ($env:CLI_CIVILENG_BIN) { $env:CLI_CIVILENG_BIN } else { "$env:USERPROFILE\.local\bin" }

Write-Host ""
Write-Host "🏗️  CLI CivilEng — Instalador (Windows)" -ForegroundColor Cyan
Write-Host "=================================="
Write-Host ""

# ── Prerequisites ───────────────────────────────────────
Write-Host "→ Verificando pré-requisitos..." -ForegroundColor Green

$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $v = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($v) {
            $pythonCmd = $cmd
            $pyVersion = $v
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "✗  Python não encontrado." -ForegroundColor Red
    Write-Host "   Instale Python 3.11+ de: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "   ⚠ Marque 'Add Python to PATH' durante a instalação." -ForegroundColor Yellow
    exit 1
}

$major, $minor = $pyVersion.Split(".")
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 11)) {
    Write-Host "✗  Python 3.11+ requerido. Versão encontrada: $pyVersion" -ForegroundColor Red
    exit 1
}
Write-Host "Python $pyVersion ✓"

$gitOk = $null
try { $gitOk = git --version 2>$null } catch {}
if (-not $gitOk) {
    Write-Host "⚠  git não encontrado." -ForegroundColor Yellow
    Write-Host "   Instale de: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "git ✓"

# ── Clone / update repo ─────────────────────────────────
if (Test-Path $InstallDir) {
    Write-Host "→ Repositório já existe em $InstallDir — atualizando..." -ForegroundColor Green
    Push-Location $InstallDir
    try {
        git pull origin main --ff-only 2>$null
    } catch {
        Write-Host "⚠  git pull falhou, usando versão local" -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "→ Clonando repositório..." -ForegroundColor Green
    git clone --depth 1 $RepoUrl $InstallDir
    if (-not $?) {
        Write-Host "✗  Falha ao clonar repositório" -ForegroundColor Red
        exit 1
    }
}

Push-Location $InstallDir

# ── Virtual environment ─────────────────────────────────
if (-not (Test-Path "venv")) {
    Write-Host "→ Criando ambiente virtual..." -ForegroundColor Green
    & $pythonCmd -m venv venv
}

Write-Host "→ Instalando dependências..." -ForegroundColor Green
$activateScript = "$InstallDir\venv\Scripts\Activate.ps1"
. $activateScript
pip install --upgrade pip -q
pip install -e . -q

# ── CLI wrapper script ──────────────────────────────────
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

$wrapperPath = "$BinDir\cli-civileng.ps1"
@"
# Wrapper: ativa o venv e executa a CLI
`$InstallDir = if (`$env:CLI_CIVILENG_HOME) { `$env:CLI_CIVILENG_HOME } else { "`$env:USERPROFILE\.cli-civileng" }
`$activateScript = "`$InstallDir\venv\Scripts\Activate.ps1"
if (-not (Test-Path `$activateScript)) {
    Write-Host "❌ CLI CivilEng não instalada. Rode o install.ps1 primeiro." -ForegroundColor Red
    exit 1
}
. `$activateScript
python -m cli_civileng.main @args
"@ | Set-Content -Path $wrapperPath -Encoding UTF8

# ── PATH check ──────────────────────────────────────────
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User") -split ";"
if ($BinDir -notin $currentPath) {
    [Environment]::SetEnvironmentVariable(
        "PATH",
        "$BinDir;" + [Environment]::GetEnvironmentVariable("PATH", "User"),
        "User"
    )
    $env:PATH = "$BinDir;$env:PATH"
    Write-Host "→ $BinDir adicionado ao PATH do usuário" -ForegroundColor Green
}

# ── Config ──────────────────────────────────────────────
if (-not (Test-Path "$InstallDir\config.yaml")) {
    Copy-Item "$InstallDir\config.yaml.example" "$InstallDir\config.yaml"
    Write-Host "⚠  Arquivo config.yaml criado em $InstallDir\config.yaml" -ForegroundColor Yellow
    Write-Host "   Edite-o com sua API key do OpenRouter:" -ForegroundColor Yellow
    Write-Host "   notepad $InstallDir\config.yaml" -ForegroundColor Yellow
    Write-Host ""
}

Pop-Location

# ── Done ────────────────────────────────────────────────
Write-Host ""
Write-Host "✅ CLI CivilEng instalada com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "   Comandos disponíveis:"
Write-Host "     cli-civileng --help"
Write-Host "     cli-civileng extract-rules"
Write-Host "     cli-civileng validate"
Write-Host ""
Write-Host "   ⚠  Antes de usar, configure sua API key:"
Write-Host "     notepad $InstallDir\config.yaml"
Write-Host ""
Write-Host "   Feche e reabra o terminal, ou execute:"
Write-Host "     refreshenv"
Write-Host ""
